#!/usr/bin/env bash
# install.sh — top-level installer for copilot-memory-setup
#
# Bootstraps a vault and installs one or more agent adapters.
#
# Usage:
#   ./install.sh --vault ~/vault --agent cursor --agent copilot
#   ./install.sh --project ~/repos/myapp --agent cursor
#   ./install.sh --vault ~/vault --agent cursor --copy
#
# Flags:
#   --vault PATH      bootstrap or update a vault at PATH
#   --project PATH    install adapters in a project at PATH (uses --vault for VAULT_DIR)
#   --agent NAME      add an agent adapter (cursor, copilot). Repeatable.
#   --copy            generate copies instead of symlinks (Windows-friendly)
#   --list-agents     print supported agents and exit

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTERS_DIR="$REPO_ROOT/adapters"

VAULT=""
PROJECT=""
AGENTS=()
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --vault)   VAULT="$2"; shift 2 ;;
        --project) PROJECT="$2"; shift 2 ;;
        --agent)   AGENTS+=("$2"); shift 2 ;;
        --copy)    EXTRA_ARGS+=(--copy); shift ;;
        --list-agents)
            ls "$ADAPTERS_DIR" 2>/dev/null
            exit 0
            ;;
        -h|--help)
            sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

if [[ ${#AGENTS[@]} -eq 0 ]]; then
    echo "ERROR: at least one --agent is required" >&2
    echo "Available agents:" >&2
    ls "$ADAPTERS_DIR" >&2
    exit 2
fi

if [[ -z "$VAULT" && -z "$PROJECT" ]]; then
    echo "ERROR: provide --vault and/or --project" >&2
    exit 2
fi

for agent in "${AGENTS[@]}"; do
    installer="$ADAPTERS_DIR/$agent/install.sh"
    if [[ ! -x "$installer" ]]; then
        echo "ERROR: no installer for agent '$agent' at $installer" >&2
        exit 1
    fi

    if [[ -n "$VAULT" ]]; then
        echo ""
        echo "==========================================="
        echo "  Installing $agent at vault: $VAULT"
        echo "==========================================="
        "$installer" --target vault --path "$VAULT" "${EXTRA_ARGS[@]}"
    fi

    if [[ -n "$PROJECT" ]]; then
        echo ""
        echo "==========================================="
        echo "  Installing $agent at project: $PROJECT"
        echo "==========================================="
        vault_for_project="${VAULT:-$HOME/vault}"
        "$installer" --target project --path "$PROJECT" \
                     --vault "$vault_for_project" "${EXTRA_ARGS[@]}"
    fi
done

echo ""
echo "==========================================="
echo "  All done."
echo "==========================================="
echo ""
echo "Make sure your shell loads ~/.copilot-memory/bin:"
echo "    echo 'export PATH=\"\$HOME/.copilot-memory/bin:\$PATH\"' >> ~/.bashrc"
echo ""
if [[ -n "$VAULT" ]]; then
    echo "Vault: $VAULT"
fi
if [[ -n "$PROJECT" ]]; then
    echo "Project: $PROJECT"
fi
echo "Agents installed: ${AGENTS[*]}"
