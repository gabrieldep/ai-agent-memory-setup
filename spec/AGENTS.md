# AGENTS.md — Universal Instructions for AI Coding Assistants

> Tool-agnostic source of truth. This file is read by Cursor (`AGENTS.md` at workspace root), GitHub Copilot (via symlink to `.github/copilot-instructions.md`), Claude Code (via symlink to `CLAUDE.md`), and any other agent following the AGENTS.md convention.

## What this vault is

This directory is the **persistent memory** for every AI coding assistant you use. It survives across sessions, across tools, and across projects. Everything decided, learned, or discovered ends up here as structured notes.

Two complementary systems live side by side:

- **Declarative memory** (this vault): what was decided, why, and what's left to do
- **Structural memory** (Graphify, per-project): how the code is shaped, queryable as a graph

The agent's job is to **read the right layer first** instead of re-reading raw source files.

## Project stacks

<!-- Edit this section for your projects -->
- Project X: React + Supabase
- Project Y: Python + FastAPI

## Zettelkasten conventions

### Note creation
- Use wikilinks: `[[note-name]]` — never markdown links for internal navigation
- Every note has YAML frontmatter (see template below)
- Filenames in kebab-case: `auth-flow.md`, never `Auth Flow.md`
- One concept per permanent note (atomicity)
- Minimum 2 wikilinks per permanent note (dense linking)

### Standard frontmatter

```yaml
---
title: Note Name
tags: [project, topic]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
type: permanent
---
```

### Never do
- Don't delete notes without asking
- Don't use markdown links for internal navigation (use wikilinks)
- Don't create notes without frontmatter
- Don't change folder structure without documenting it in `logs/`

## Continuity commands

These two commands are the heart of the memory system. Both are invocable as native slash/prompt commands in each agent **and** as plain shell scripts at `~/.copilot-memory/bin/`.

### `/memory-load` (alias: `/resume`)

When invoked:

1. Read the 3 most recent session logs in `logs/`
2. Read `<current-project>/architecture/decisions.md` if it exists
3. If the current project has a `graphify-out/graph.json`, summarize it (god nodes, recent connections)
4. Summarize current state, open questions, and what's left to do — in ≤ 200 words
5. Stop and wait for the user's first real instruction

### `/memory-save` (alias: `/save`)

When invoked:

1. Summarize the session: what was done, decisions made, open questions, files modified
2. Write `logs/YYYY-MM-DD-HHMM-<slug>.md` with:
   - `## What was done` — bullet list with wikilinks to created/modified notes
   - `## Decisions` — each decision in a single sentence
   - `## Open questions` — anything that didn't get answered
   - `## Next session` — what to pick up first
3. Add wikilinks to every note and project mentioned
4. Shell out to `memory-save --check` to verify the log was written and well-formed
5. If the current working directory is a git repo, stage all changes and commit with message `session: <slug>`

## Context Navigation (3-layer query rule)

Inside any project that has a `graphify-out/` directory, **always query in this order**:

1. **First:** `graphify-out/graph.json` (or `graphify-out/wiki/index.md` if present) — code structure and connections
2. **Second:** this vault — for decisions, progress, and project context
3. **Third:** only read raw source files when editing, or when the first two layers don't have the answer

### When to rebuild the graph
- After structural changes (new modules, major refactors)
- Run `graphify update .` (only processes modified files)
- The graph is persistent — do **not** rebuild every session

### Do NOT
- Don't manually modify files inside `graphify-out/`
- Don't re-read the entire codebase if the graph already has the information

## Chat ingestion

Conversations from every supported tool land in `chats/<source>/`:

- `chats/claude-code/` — Claude Code transcripts
- `chats/claude-web/` — Claude.ai browser exports
- `chats/cursor/` — Cursor agent transcripts
- `chats/copilot/` — GitHub Copilot chat exports

All chats get:
- `type: chat` and `chat-import` tag in frontmatter
- A `source:` field identifying the origin tool
- Auto-extracted topic tags
- Wikilinks to vault notes that already exist

### Filter in Obsidian graph view
- `tag:chat-import` — only imported chats
- `path:chats/cursor` — only Cursor chats
- `-path:chats` — hide all chats (clean view of curated knowledge)

## Folder roles

| Folder | Role |
|---|---|
| `permanent/` | Consolidated atomic notes (the real knowledge base) |
| `inbox/` | Raw capture — ideas, drafts, things to triage |
| `fleeting/` | Quick temporary notes that may or may not survive |
| `templates/` | Note templates |
| `logs/` | Global session logs from `/memory-save` |
| `references/` | External reference material |
| `<project-name>/` | Per-project MOCs, architecture, decisions, features |
| `chats/<source>/` | Imported conversations (read-only — do not edit) |
| `graphify/<project>/` | Codebase knowledge graphs (read-only — auto-generated) |

## Project-level AGENTS.md

When a project repo has its own `AGENTS.md`, it should be slim and point back here:

```markdown
# AGENTS.md

Persistent memory: $VAULT (see $VAULT/AGENTS.md for vault conventions).

## This project
<!-- project-specific instructions -->
```

The vault rules in this file are the source of truth — project files extend, never override, them.
