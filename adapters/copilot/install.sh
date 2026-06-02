#!/usr/bin/env bash
# adapters/copilot/install.sh
#
# Install the copilot-memory-setup adapter for GitHub Copilot.
#
# GitHub Copilot is workspace-scoped only — there's no global instructions
# location. So this adapter has two flavors:
#
#   --target vault   → installs in the vault, so when the user opens the vault
#                      in VS Code, Copilot loads vault conventions
#   --target project → installs in a project repo so Copilot uses the memory
#                      conventions there
#
# Files laid down:
#
#   <target>/.github/copilot-instructions.md         → spec/AGENTS.md (symlink/copy)
#   <target>/.github/prompts/memory-load.prompt.md   → adapter template
#   <target>/.github/prompts/memory-save.prompt.md   → adapter template
#
# For 'project' target, AGENTS.md (slim pointer) is also written.
#
# Also installs deterministic scripts at ~/.copilot-memory/bin/.
#
# Usage:
#   adapters/copilot/install.sh --target vault   --path ~/vault
#   adapters/copilot/install.sh --target project --path ~/repos/myapp
#   adapters/copilot/install.sh --target project --path ~/repos/myapp --copy

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SPEC_DIR="$REPO_ROOT/spec"
TEMPLATES="$REPO_ROOT/adapters/copilot/templates"
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
            sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$TARGET" || -z "$TARGET_PATH" ]]; then
    echo "ERROR: --target {vault|project} and --path PATH are required" >&2
    exit 2
fi

if [[ "$TARGET" != "vault" && "$TARGET" != "project" ]]; then
    echo "ERROR: --target must be 'vault' or 'project'" >&2
    exit 2
fi

mkdir -p "$TARGET_PATH"

link_or_copy() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    if [[ -e "$dest" || -L "$dest" ]]; then
        if [[ -L "$dest" ]]; then
            rm "$dest"
        else
            mv "$dest" "${dest}.bak.$(date +%s)"
            echo "  backed up existing: ${dest}.bak"
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

install_common() {
    local dest="$1"
    link_or_copy "$SPEC_DIR/AGENTS.md" "$dest/.github/copilot-instructions.md"
    link_or_copy "$TEMPLATES/prompts/memory-load.prompt.md" \
                 "$dest/.github/prompts/memory-load.prompt.md"
    link_or_copy "$TEMPLATES/prompts/memory-save.prompt.md" \
                 "$dest/.github/prompts/memory-save.prompt.md"
}

case "$TARGET" in
    vault)
        echo "==> Installing Copilot adapter at vault: $TARGET_PATH"
        mkdir -p "$TARGET_PATH"/{permanent,inbox,fleeting,templates,logs,references}
        mkdir -p "$TARGET_PATH"/chats/{claude-code,claude-web,cursor,copilot}
        mkdir -p "$TARGET_PATH"/graphify
        install_common "$TARGET_PATH"
        ;;
    project)
        proj_slug=$(basename "$TARGET_PATH")
        echo "==> Installing Copilot adapter at project: $TARGET_PATH"
        echo "    (vault assumed at: $VAULT_DIR)"
        install_common "$TARGET_PATH"

        # Slim AGENTS.md pointer (Copilot doesn't read AGENTS.md, but other
        # tools sharing the same project will)
        cat > "$TARGET_PATH/AGENTS.md" <<EOF
# AGENTS.md — $proj_slug

Persistent memory lives at **\`$VAULT_DIR\`**.
Read **\`$VAULT_DIR/AGENTS.md\`** for vault conventions.

For GitHub Copilot specifically, the same instructions are loaded from
\`.github/copilot-instructions.md\` in this repo.

## This project

<!-- Project-specific instructions go here. -->

## Context Navigation (Graphify 3-layer rule)

1. Query \`graphify-out/graph.json\` for code structure
2. Query \`$VAULT_DIR\` for decisions / progress
3. Only read raw source files when editing
EOF
        echo "  wrote:   $TARGET_PATH/AGENTS.md"
        ;;
esac

echo ""
echo "==> Installing deterministic scripts to $BIN_DEST"
install_bin

echo ""
echo "Done. Add $BIN_DEST to your PATH:"
echo "    export PATH=\"\$HOME/.copilot-memory/bin:\$PATH\""
echo ""
echo "Note: GitHub Copilot reads .github/copilot-instructions.md automatically"
echo "when this workspace is opened in VS Code with Copilot Chat enabled."
echo "Prompt files (.prompt.md) require VS Code 1.95+ and the 'Use Instructions"
echo "Files' setting enabled."
