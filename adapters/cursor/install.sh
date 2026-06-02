#!/usr/bin/env bash
# adapters/cursor/install.sh
#
# Install the copilot-memory-setup adapter for Cursor.
#
# Lays down the following files (symlinks by default, --copy for real files):
#
#   At the VAULT (only with --target vault):
#     $VAULT/AGENTS.md                              → spec/AGENTS.md
#     $VAULT/.cursor/rules/agents.mdc               → adapters/cursor/templates/rules/agents.mdc
#     $VAULT/.cursor/commands/memory-load.md        → adapters/cursor/templates/commands/memory-load.md
#     $VAULT/.cursor/commands/memory-save.md        → adapters/cursor/templates/commands/memory-save.md
#     $VAULT/.cursor/skills/memory-load/SKILL.md    → adapters/cursor/templates/skills/memory-load/SKILL.md
#     $VAULT/.cursor/skills/memory-save/SKILL.md    → adapters/cursor/templates/skills/memory-save/SKILL.md
#
#   At a PROJECT (only with --target project):
#     <project>/AGENTS.md                           → slim pointer file (generated)
#     <project>/.cursor/rules/agents.mdc            → same rule file (symlink/copy)
#     <project>/.cursor/commands/{memory-load,memory-save}.md → command files
#
# Also installs the deterministic scripts into ~/.copilot-memory/bin/:
#   ~/.copilot-memory/bin/memory-load
#   ~/.copilot-memory/bin/memory-save
#
# Usage:
#   adapters/cursor/install.sh --target vault   --path ~/vault
#   adapters/cursor/install.sh --target project --path ~/repos/myapp
#   adapters/cursor/install.sh --target vault   --path ~/vault --copy

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SPEC_DIR="$REPO_ROOT/spec"
TEMPLATES="$REPO_ROOT/adapters/cursor/templates"
BIN_SRC="$REPO_ROOT/scripts/bin"
BIN_DEST="$HOME/.copilot-memory/bin"

TARGET=""
TARGET_PATH=""
USE_COPY=0
VAULT_DIR="${VAULT_DIR:-$HOME/vault}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) TARGET="$2"; shift 2 ;;
        --path)   TARGET_PATH="$2"; shift 2 ;;
        --vault)  VAULT_DIR="$2"; shift 2 ;;
        --copy)   USE_COPY=1; shift ;;
        -h|--help)
            sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$TARGET" || -z "$TARGET_PATH" ]]; then
    echo "ERROR: --target {vault|project} and --path PATH are required" >&2
    echo "Run with --help for details." >&2
    exit 2
fi

if [[ "$TARGET" != "vault" && "$TARGET" != "project" ]]; then
    echo "ERROR: --target must be 'vault' or 'project'" >&2
    exit 2
fi

mkdir -p "$TARGET_PATH"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

link_or_copy() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    if [[ -e "$dest" || -L "$dest" ]]; then
        if [[ -L "$dest" ]]; then
            rm "$dest"
        else
            local backup="${dest}.bak.$(date +%s)"
            mv "$dest" "$backup"
            echo "  backed up existing: $backup"
        fi
    fi
    if [[ "$USE_COPY" -eq 1 ]]; then
        {
            echo "<!-- GENERATED from $(realpath --relative-to="$REPO_ROOT" "$src" 2>/dev/null || echo "$src") — do not edit -->"
            cat "$src"
        } > "$dest"
        echo "  copy:    $dest"
    else
        ln -s "$src" "$dest"
        echo "  symlink: $dest -> $src"
    fi
}

install_bin() {
    if ! mkdir -p "$BIN_DEST" 2>/dev/null; then
        echo "  WARN: could not create $BIN_DEST (skipping bin install)" >&2
        return 0
    fi
    for script in memory-load memory-save; do
        local src="$BIN_SRC/$script"
        local dest="$BIN_DEST/$script"
        if [[ -e "$dest" || -L "$dest" ]]; then
            if [[ -L "$dest" ]]; then
                rm "$dest"
            else
                mv "$dest" "${dest}.bak.$(date +%s)"
            fi
        fi
        if [[ "$USE_COPY" -eq 1 ]]; then
            cp "$src" "$dest"
            chmod +x "$dest"
        else
            ln -s "$src" "$dest"
        fi
        echo "  bin:     $dest"
    done
}

# ---------------------------------------------------------------------------
# Vault install
# ---------------------------------------------------------------------------

install_vault() {
    local vault="$1"
    echo "==> Installing Cursor adapter at vault: $vault"

    # Ensure vault structure exists
    mkdir -p "$vault"/{permanent,inbox,fleeting,templates,logs,references}
    mkdir -p "$vault"/chats/{claude-code,claude-web,cursor,copilot}
    mkdir -p "$vault"/graphify

    link_or_copy "$SPEC_DIR/AGENTS.md" "$vault/AGENTS.md"

    link_or_copy "$TEMPLATES/rules/agents.mdc" \
                 "$vault/.cursor/rules/agents.mdc"

    link_or_copy "$TEMPLATES/commands/memory-load.md" \
                 "$vault/.cursor/commands/memory-load.md"
    link_or_copy "$TEMPLATES/commands/memory-save.md" \
                 "$vault/.cursor/commands/memory-save.md"

    link_or_copy "$TEMPLATES/skills/memory-load/SKILL.md" \
                 "$vault/.cursor/skills/memory-load/SKILL.md"
    link_or_copy "$TEMPLATES/skills/memory-save/SKILL.md" \
                 "$vault/.cursor/skills/memory-save/SKILL.md"

    echo "Vault adapter installed."
}

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------

install_project() {
    local proj="$1"
    local proj_slug
    proj_slug=$(basename "$proj")
    echo "==> Installing Cursor adapter at project: $proj"
    echo "    (vault assumed at: $VAULT_DIR)"

    # Project-level AGENTS.md is a slim pointer — always generated, never symlinked
    cat > "$proj/AGENTS.md" <<EOF
# AGENTS.md — $proj_slug

Persistent memory lives at **\`$VAULT_DIR\`**.
Read **\`$VAULT_DIR/AGENTS.md\`** for vault conventions (Zettelkasten rules, /memory-load and /memory-save behavior, 3-layer query rule).

## This project

<!-- Project-specific instructions go here. Examples:
     - Stack: ...
     - Conventions: ...
     - Open issues to be aware of: ...
-->

## Context Navigation (Graphify 3-layer rule)

1. Query \`graphify-out/graph.json\` (or \`graphify-out/wiki/index.md\`) for code structure
2. Query \`$VAULT_DIR\` for decisions / progress
3. Only read raw source files when editing
EOF
    echo "  wrote:   $proj/AGENTS.md"

    link_or_copy "$TEMPLATES/rules/agents.mdc" \
                 "$proj/.cursor/rules/agents.mdc"
    link_or_copy "$TEMPLATES/commands/memory-load.md" \
                 "$proj/.cursor/commands/memory-load.md"
    link_or_copy "$TEMPLATES/commands/memory-save.md" \
                 "$proj/.cursor/commands/memory-save.md"

    echo "Project adapter installed."
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

case "$TARGET" in
    vault)   install_vault   "$TARGET_PATH" ;;
    project) install_project "$TARGET_PATH" ;;
esac

echo ""
echo "==> Installing deterministic scripts to $BIN_DEST"
install_bin

echo ""
echo "Done. Add $BIN_DEST to your PATH if it isn't already:"
echo "    export PATH=\"\$HOME/.copilot-memory/bin:\$PATH\""
