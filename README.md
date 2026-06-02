# Copilot Memory Setup — Persistent Memory for Any AI Coding Assistant

> **One vault, many copilots.** Persistent project memory and codebase awareness for Cursor, GitHub Copilot, Claude Code, and any other AI coding assistant that reads `AGENTS.md` / `CLAUDE.md` / `.github/copilot-instructions.md`.

A configurable setup that turns whatever AI coding assistant you use into an agent with long-term memory and full codebase awareness — without wasting tokens re-reading files. Originally built for Claude Code; now generalized.

🇧🇷 [Leia em Português](./README.pt-BR.md)

---

## Table of Contents

1. [The Problem](#the-problem)
2. [The Solution (Overview)](#the-solution-overview)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Part 1 — Obsidian as Persistent Memory](#part-1--obsidian-as-persistent-memory)
6. [Part 2 — Chat Import Pipeline](#part-2--chat-import-pipeline)
7. [Part 3 — Graphify (Codebase Knowledge Graph)](#part-3--graphify-codebase-knowledge-graph)
8. [Part 4 — Per-Agent Adapters](#part-4--per-agent-adapters)
9. [Part 5 — Complete Workflow](#part-5--complete-workflow)
10. [Troubleshooting](#troubleshooting)

---

## The Problem

When working with any AI coding assistant, two problems silently eat your tokens:

**Problem 1 — Amnesia between sessions.** Every new session, you have to re-explain your project: stack, past decisions, current bugs, what's left to do. The agent remembers nothing.

**Problem 2 — Codebase re-reading.** The agent re-reads your project files every session to understand the structure. A 40-file project burns ~20,000 tokens just for orientation — before you even ask a question.

These problems are agent-agnostic. Cursor, Copilot, Claude Code — they all do this.

---

## The Solution (Overview)

Three complementary systems:

| Layer | Tool | Problem solved | Cost |
|-------|------|----------------|------|
| Persistent memory | **Obsidian vault** (Zettelkasten) | Amnesia between sessions | Free |
| Code map | **Graphify** | Codebase re-reading | Free (AST mode) |
| Chat history | **Import pipeline** | Lost chat insights | Free |
| Continuity | **`/memory-load`** + **`/memory-save`** | Picking up where you left off | Free |

Plus per-agent **adapters** that lay down the right config files in the right places (`AGENTS.md`, `.cursor/commands/`, `.github/copilot-instructions.md`, etc.) so every agent reads from the same source of truth.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  OBSIDIAN VAULT (single, shared)             │
│                                                             │
│  AGENTS.md   ← universal instructions (read by every agent) │
│  permanent/  ← consolidated knowledge (Zettelkasten)        │
│  logs/       ← session logs (/memory-save)                  │
│  chats/      ← imported conversations (per source)          │
│    claude-code/  claude-web/  cursor/  copilot/             │
│  graphify/   ← codebase knowledge graphs                    │
│  <project>/  ← MOCs, decisions, architecture                │
└─────────────────────────┬───────────────────────────────────┘
                          │
              symlinks / generated copies
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│   PROJECT REPO       │        │   ~/.copilot-memory/ │
│                      │        │                      │
│  AGENTS.md           │        │  bin/memory-load     │
│  .cursor/commands/   │        │  bin/memory-save     │
│  .github/prompts/    │        │                      │
│  graphify-out/       │        │  (deterministic      │
│                      │        │   fallback scripts)  │
└──────────────────────┘        └──────────────────────┘
```

The agent's job is to **read the right layer first** instead of re-reading raw source files.

---

## Quick Start

```bash
git clone https://github.com/<you>/copilot-memory-setup.git
cd copilot-memory-setup

# Create vault + install adapters for Cursor and Copilot
./install.sh --vault ~/vault --agent cursor --agent copilot

# Then for each project repo:
./install.sh --project ~/repos/myapp --vault ~/vault --agent cursor --agent copilot

# Add the deterministic scripts to your PATH:
echo 'export PATH="$HOME/.copilot-memory/bin:$PATH"' >> ~/.bashrc
```

Now in Cursor/Copilot:
- Type `/memory-load` at the start of a session
- Type `/memory-save` when you're wrapping up
- Run `memory-load` or `memory-save --slug <slug>` directly from any shell

---

## Part 1 — Obsidian as Persistent Memory

### Concept

A single centralized Obsidian vault acts as your AI assistant's "second brain." It stores decisions, context, progress, and knowledge for all your projects. Notes follow the Zettelkasten method: atomic (one idea per note), densely interlinked, with standardized metadata.

The agent accesses the vault through `AGENTS.md` (and, when relevant, tool-specific files like `CLAUDE.md` or `.github/copilot-instructions.md` — but those are just symlinks to the same `AGENTS.md`).

### Recommended Structure

```
~/vault/                           # single vault for all projects
├── AGENTS.md                      # symlink → spec/AGENTS.md
├── permanent/                     # consolidated atomic notes
├── inbox/                         # raw capture
├── fleeting/                      # quick temporary notes
├── templates/                     # note templates
├── logs/                          # global session logs
├── references/                    # reference material
├── <project>/                     # MOCs and notes per project
│   ├── architecture/
│   ├── pipeline/
│   ├── data/
│   ├── features/
│   └── logs/
├── chats/                         # imported conversations
│   ├── claude-code/
│   ├── claude-web/
│   ├── cursor/
│   └── copilot/
└── graphify/                      # codebase knowledge graphs
    └── <project>/
```

> **Why a single vault?** One vault per project fragments knowledge. With a single vault, a note about "Supabase Auth" links to both project A and B. The graph view reveals cross-project connections you didn't expect.

### Setup

The installer handles this end-to-end:

```bash
./install.sh --vault ~/vault --agent cursor --agent copilot
```

This creates the folder structure, symlinks `~/vault/AGENTS.md` → `spec/AGENTS.md`, and lays down the agent-specific configs (slash commands, rules, prompt files).

Full details on the vault structure: see [`spec/vault-structure.md`](./spec/vault-structure.md).

---

## Part 2 — Chat Import Pipeline

### Concept

Your AI assistant chats contain valuable decisions, insights, and context that get lost in history. This pipeline exports, processes, and imports those conversations as vault notes — with frontmatter, automatic tags, and wikilinks to existing notes.

The original `claude_to_obsidian.py` has been generalized into `chat_to_obsidian.py` with per-source extractors:

| `--source` | Where transcripts come from |
|---|---|
| `claude-code` | `claude-extract --all` from `claude-conversation-extractor` |
| `claude-web` | Browser extension → `.md` drops in `~/claude-exports/web/` |
| `cursor` | `~/.cursor/projects/*/agent-transcripts/*/*.jsonl` (parsed directly) |
| `copilot` | VS Code "Chat: Export" → `.json` drops in `~/copilot-exports/` |

### Usage

```bash
# Single source
python3 scripts/chat_to_obsidian.py --source cursor --vault-dir ~/vault

# All sources at once (uses cron-friendly defaults)
scripts/sync.sh --vault ~/vault
```

### Schedule (cron, daily 10pm)

```bash
(crontab -l 2>/dev/null; echo "0 22 * * * $HOME/repos/copilot-memory-setup/scripts/sync.sh") | crontab -
```

### CLI options

| Flag | Description |
|------|-------------|
| `--source` | One of `cursor`, `copilot`, `claude-code`, `claude-web` (required) |
| `--vault-dir` | Path to your Obsidian vault (required) |
| `--import-dir` | Override the staging directory (defaults are source-specific) |
| `--dry-run` | Preview without writing |
| `--move` | Delete originals after import (only honored by sources that own files) |
| `--no-wikilinks` | Skip wikilink insertion |

Customize tag extraction by editing `KEYWORD_TAG_MAP` at the top of `scripts/chat_to_obsidian.py`.

---

## Part 3 — Graphify (Codebase Knowledge Graph)

### Concept

[Graphify](https://github.com/safishamsi/graphify) transforms your codebase into a queryable knowledge graph. Instead of the agent re-reading every file, it queries the graph — persistent across sessions, fraction of the tokens.

- **Code:** processed 100% locally via tree-sitter AST. Nothing leaves your machine.
- **Cache:** SHA256 — re-runs only process modified files.
- **Cost:** 0 tokens in default mode (pure AST). `--deep` uses LLM for semantic edges.
- **Languages:** 20+ via tree-sitter (Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, …).

### Setup

```bash
pip install graphifyy

# Install Graphify's skill/integration for your agent:
graphify install --platform cursor    # or claude, codex, opencode, copilot, ...
```

### Extract

```bash
cd ~/repos/myapp
graphify extract . --out ./graphify-out
```

Output:

```
graphify-out/
├── graph.json          # queryable graph (always)
├── graph.html          # interactive viz
├── GRAPH_REPORT.md     # god nodes, metrics
└── cache/              # SHA256 cache
```

### Update `.gitignore`

```gitignore
graphify-out/cache/
```

Keep `graph.json` and `GRAPH_REPORT.md` versioned — they're useful for the team.

### Optional: auto-rebuild

```bash
graphify hook install        # rebuilds on every commit
graphify watch .             # rebuilds on save (separate terminal)
```

### Context Navigation rule (3-layer query)

The `AGENTS.md` written by the installer already includes this rule. The agent should query in this order:

1. **First:** `graphify-out/graph.json` — code structure
2. **Second:** the vault — for decisions, progress, context
3. **Third:** only read raw source when editing, or when 1 + 2 don't have the answer

---

## Part 4 — Per-Agent Adapters

Each agent has its own installer that lays down the files it needs. All adapters read from the same `spec/AGENTS.md` source of truth.

### Cursor

```bash
adapters/cursor/install.sh --target vault   --path ~/vault
adapters/cursor/install.sh --target project --path ~/repos/myapp
```

Files installed:

| Where | What |
|---|---|
| `<target>/AGENTS.md` | Symlink → `spec/AGENTS.md` (vault) or generated pointer (project) |
| `<target>/.cursor/rules/agents.mdc` | `alwaysApply: true` rule with Zettelkasten conventions |
| `<target>/.cursor/commands/memory-load.md` | `/memory-load` slash command |
| `<target>/.cursor/commands/memory-save.md` | `/memory-save` slash command |
| `<target>/.cursor/skills/memory-load/SKILL.md` | Auto-trigger skill (vault only) |
| `<target>/.cursor/skills/memory-save/SKILL.md` | Auto-trigger skill (vault only) |

### GitHub Copilot

```bash
adapters/copilot/install.sh --target vault   --path ~/vault
adapters/copilot/install.sh --target project --path ~/repos/myapp
```

Files installed:

| Where | What |
|---|---|
| `<target>/.github/copilot-instructions.md` | Symlink → `spec/AGENTS.md` |
| `<target>/.github/prompts/memory-load.prompt.md` | `/memory-load` prompt file (VS Code 1.95+) |
| `<target>/.github/prompts/memory-save.prompt.md` | `/memory-save` prompt file |
| `<target>/AGENTS.md` | Slim pointer (project target only) |

> **Caveat for Copilot:** GitHub Copilot is workspace-scoped only — there is no global instructions location. So you need to run the project adapter for every repo. The deterministic shell scripts at `~/.copilot-memory/bin/` are the more reliable surface for Copilot users.

### Symlinks vs copies

By default the installer uses symlinks (one source of truth). Pass `--copy` to write real files with a `<!-- GENERATED -->` header instead — useful on Windows or when symlinks aren't tracked by your VCS.

### Adding more agents

Drop a folder under `adapters/<name>/` with an `install.sh` that accepts `--target {vault|project} --path PATH [--copy]`. The top-level `install.sh --agent <name>` will pick it up automatically.

---

## Part 5 — Complete Workflow

### Typical session

```
Open agent (Cursor / Copilot / etc.)
    │
    ├── /memory-load                  ← loads vault context
    │                                   (recent logs, decisions, graph report)
    │
    ├── Agent queries graph.json      ← understands code structure
    │                                   without re-reading every file
    │
    ├── Work on code                  ← features, bugs, refactors
    │
    ├── /memory-save                  ← writes session log + git commit
    │
    └── (graph rebuilds via hook)     ← if `graphify hook install` was run
```

### Savings per layer

| Layer | Without | With |
|-------|---------|------|
| `/memory-load` | Re-explain project every session | Agent already has the context |
| Graphify | Re-read ~40 files (~20k tokens) | Query 1 graph (~280 tokens) |
| Chat pipeline | Insights lost in history | Everything indexed and searchable |
| `/memory-save` | Forget what was done | Complete history with wikilinks |

### Graph view filters (Obsidian)

| Filter | Shows |
|---|---|
| `path:permanent` | Only permanent notes |
| `path:graphify` | Only codebase nodes |
| `tag:chat-import` | Only imported chats |
| `path:chats/cursor` | Cursor chats only |
| `-path:graphify -path:chats` | Pure curated knowledge |

---

## Troubleshooting

**Graph view empty with filter applied:**
Disable "Orphans" and "Existing files only" in the graph filters. Cmd+Q and reopen Obsidian to force reindexing.

**Symlinks not following on Windows:**
Re-run the installer with `--copy`. Files are generated as real files with a `<!-- GENERATED -->` header. You'll need to re-run `--copy` after spec changes.

**`memory-save --check` fails:**
The log is missing one of the required sections (`## What was done`, `## Decisions`, `## Open questions`, `## Next session`) or its frontmatter. Open the file under `$VAULT/logs/` and add the missing pieces.

**Cursor commands don't appear:**
Make sure the workspace root is the vault or project where you ran the installer. Cursor reads `.cursor/commands/` relative to the open workspace. Restart Cursor after install.

**Copilot doesn't pick up `.github/copilot-instructions.md`:**
The file is workspace-scoped only. Confirm you're working in a folder that has the file at its root (or one level down). Toggle the Copilot Chat "Use Instructions Files" setting and reload the window.

**Cursor extractor finds nothing:**
Cursor transcripts live at `~/.cursor/projects/*/agent-transcripts/*/*.jsonl`. If the path is different on your install, pass `--import-dir <root>` to override.

**Copilot extractor finds nothing:**
You need to manually export chats first: VS Code Command Palette → "Chat: Export" → save the `.json` to `~/copilot-exports/`. Then run `chat_to_obsidian.py --source copilot`.

**Cron doesn't run on macOS:**
Grant Full Disk Access to your terminal (or `cron`) in System Preferences → Privacy & Security.

**Graphify wiki not generated:**
`wiki/` is only produced by the skill form with `--wiki`. The headless `graphify extract` doesn't expose it. Use `graphify query "question"` against `graph.json` instead, or run the skill form.

**Files with parentheses in name:**
Graphify generates notes like `myFunction().md`. Obsidian struggles with `()`. Batch rename:
```bash
cd ~/vault/graphify/<project>
for f in *"("*; do mv "$f" "$(echo "$f" | sed 's/[()]//g')"; done
```

---

## Repo layout

```
copilot-memory-setup/
├── spec/                          # tool-agnostic source of truth
│   ├── AGENTS.md
│   ├── vault-structure.md
│   └── commands/{memory-load,memory-save}.md
├── adapters/                      # per-tool installers
│   ├── cursor/
│   └── copilot/
├── scripts/
│   ├── chat_to_obsidian.py        # generalized chat importer
│   ├── extractors/                # per-source extractors
│   ├── sync.sh                    # cron-friendly wrapper
│   ├── bin/{memory-load,memory-save}  # deterministic scripts
│   ├── claude_to_obsidian.py      # kept for backward compat
│   └── sync_claude_obsidian.sh    # kept for backward compat
├── install.sh                     # top-level dispatcher
└── README.md
```

---

## Credits & Links

- [Graphify](https://github.com/safishamsi/graphify) — codebase knowledge graphs (MIT)
- [Obsidian](https://obsidian.md) — PKM and second brain (free)
- [Cursor](https://cursor.sh), [GitHub Copilot](https://github.com/features/copilot), [Claude Code](https://docs.anthropic.com) — the agents this targets
- Inspired by Andrej Karpathy's system and the r/ClaudeAI community

---

**If this helped you, star the repo and share it with other devs using AI coding assistants.**
