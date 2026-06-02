# Vault Structure

The recommended Obsidian vault layout. This is the structure the installers create when bootstrapping a new vault and the structure `AGENTS.md` references.

## Layout

```
~/vault/                           # single vault for every project
├── AGENTS.md                      # universal instructions (symlinked from spec/AGENTS.md)
├── CLAUDE.md                      # symlink → AGENTS.md (only if Claude Code adapter is installed)
├── permanent/                     # consolidated atomic notes
├── inbox/                         # raw capture (ideas, drafts)
├── fleeting/                      # quick temporary notes
├── templates/                     # note templates
│   └── default-note.md
├── logs/                          # global session logs from /memory-save
├── references/                    # external reference material
├── <project-name>/                # MOCs and notes for each project
│   ├── architecture/              #   architecture, decisions, conventions
│   ├── pipeline/                  #   data flows, APIs
│   ├── data/                      #   schema, data model
│   ├── features/                  #   planned/implemented features
│   └── logs/                      #   project-scoped session logs
├── chats/                         # imported conversations from every tool
│   ├── claude-code/
│   ├── claude-web/
│   ├── cursor/
│   └── copilot/
└── graphify/                      # codebase knowledge graphs
    └── <project-name>/            #   one folder per project
```

## Why a single vault

One vault per project fragments knowledge. With a single vault:

- A note about "Supabase Auth" links to both Project A and Project B
- The graph view reveals cross-project connections you didn't expect
- The agent has one place to look — `$VAULT`

## Bootstrap commands

The top-level `install.sh` will create the structure automatically:

```bash
./install.sh --vault ~/vault --agent cursor --agent copilot
```

Or manually:

```bash
VAULT=~/vault
mkdir -p "$VAULT"/{permanent,inbox,fleeting,templates,logs,references}
mkdir -p "$VAULT"/chats/{claude-code,claude-web,cursor,copilot}
mkdir -p "$VAULT"/graphify
```

## Note template

`templates/default-note.md`:

```markdown
---
title: {{title}}
tags: []
created: {{date}}
updated: {{date}}
status: draft
type: permanent
---

# {{title}}

## Context

## Details

## Related links
```

## Recommended Obsidian plugins

| Plugin | Purpose | Install method |
|---|---|---|
| BRAT | Install beta plugins | Community Plugins → Browse |
| 3D Graph | 3D vault visualization | Via BRAT (v2.4.1) |
| Folders to Graph | Folders as graph nodes | Community Plugins → Browse |
| Calendar | Daily note navigation | Community Plugins → Browse |
