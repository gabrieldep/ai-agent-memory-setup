#!/usr/bin/env bash
# scripts/sync.sh — generalized chat sync (replaces sync_claude_obsidian.sh)
#
# Imports chats from one or more AI assistants into the Obsidian vault.
# Designed to be run by cron, or manually whenever.
#
# Usage:
#   sync.sh                              # uses defaults: all sources, $HOME/vault
#   sync.sh --vault ~/vault              # explicit vault
#   sync.sh --source cursor --source claude-code
#   sync.sh --move                       # delete originals (where applicable)
#
# Add to cron (every night at 10pm):
#   (crontab -l 2>/dev/null; echo "0 22 * * * $HOME/scripts/sync.sh") | crontab -

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${VAULT_DIR:-$HOME/vault}"
LOG="${SYNC_LOG:-$SCRIPT_DIR/sync.log}"
MOVE=0
SOURCES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --vault)  VAULT="$2"; shift 2 ;;
        --source) SOURCES+=("$2"); shift 2 ;;
        --move)   MOVE=1; shift ;;
        --log)    LOG="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

if [[ ${#SOURCES[@]} -eq 0 ]]; then
    SOURCES=(claude-code claude-web cursor copilot)
fi

if [[ ! -d "$VAULT" ]]; then
    echo "ERROR: vault not found at $VAULT" >&2
    exit 1
fi

mkdir -p "$(dirname "$LOG")"

{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync started"
    echo "  vault:   $VAULT"
    echo "  sources: ${SOURCES[*]}"
    echo "  move:    $MOVE"
} >> "$LOG"

extra=()
[[ $MOVE -eq 1 ]] && extra+=(--move)

failed=()
for source in "${SOURCES[@]}"; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] → $source" >> "$LOG"
    if ! python3 "$SCRIPT_DIR/chat_to_obsidian.py" \
            --source "$source" --vault-dir "$VAULT" "${extra[@]}" \
            >> "$LOG" 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAIL: $source" >> "$LOG"
        failed+=("$source")
    fi
done

if [[ ${#failed[@]} -gt 0 ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync finished with failures: ${failed[*]}" >> "$LOG"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync finished cleanly" >> "$LOG"
echo "" >> "$LOG"
