#!/usr/bin/env bash
set -euo pipefail

# Push daily note(s) to an Obsidian vault.
# Policy: MERGE, never overwrite. Uses shared obsidian_merge.py.
#
# Configure with env vars or by editing defaults below.
# Examples:
#   macOS:  ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/MyVault/10_Daily
#   Linux:  /mnt/c/Users/YOU/iCloudDrive/iCloud~md~obsidian/MyVault/10_Daily
#   Direct: ~/ObsidianVault/10_Daily
#
# Usage:
#   bash scripts/obsidian_push_daily.sh YYYY-MM-DD [YYYY-MM-DD ...]

# --- Config (edit these or set env vars) ---
GHOST_WORKSPACE="${GHOST_WORKSPACE:-$(cd "$(dirname "$0")/.." && pwd)}"
SRC_DIR="${GHOST_SRC_DAILY:-$GHOST_WORKSPACE/memory}"
DEST_DIR="${GHOST_DEST_DAILY:-}"     # Must be set! e.g. ~/ObsidianVault/10_Daily
VAULT_DIR="${GHOST_VAULT:-}"          # Vault root for git ops (optional)
MERGE_SCRIPT="$GHOST_WORKSPACE/scripts/obsidian_merge.py"
# ---

if [[ -z "$DEST_DIR" ]]; then
  echo "⚠️ Set GHOST_DEST_DAILY to your Obsidian daily notes folder." >&2
  echo "   Example: export GHOST_DEST_DAILY=~/ObsidianVault/10_Daily" >&2
  exit 1
fi

[[ ! -d "$DEST_DIR" ]] && echo "⚠️ Dest not found: $DEST_DIR" >&2 && exit 1
[[ $# -lt 1 ]] && echo "Usage: $0 YYYY-MM-DD [YYYY-MM-DD ...]" >&2 && exit 2

mkdir -p "$DEST_DIR"

declare -a pushed_dates=()
declare -a pushed_rels=()

for d in "$@"; do
  src="$SRC_DIR/$d.md"
  dest="$DEST_DIR/$d.md"

  [[ ! -f "$src" ]] && echo "Missing source: $src" >&2 && exit 3

  # Git safety snapshot
  if [[ -n "${VAULT_DIR:-}" ]] && [[ -f "$dest" ]] && git -C "$VAULT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    rel="${DEST_DIR#$VAULT_DIR/}/$d.md"
    git -C "$VAULT_DIR" add -- "$rel" 2>/dev/null || true
    pushed_rels+=("$rel")
  fi

  python3 "$MERGE_SCRIPT" "$src" "$dest" || {
    echo "❌ Merge failed for $d — original preserved." >&2
    rm -f "$dest.tmp"; exit $?
  }

  pushed_dates+=("$d")
done

# Git commit if vault is a repo
if [[ -n "${VAULT_DIR:-}" ]] && [[ ${#pushed_rels[@]} -gt 0 ]] && git -C "$VAULT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  rm -f "$VAULT_DIR/.git/index.lock"
  git -C "$VAULT_DIR" add -- "${pushed_rels[@]}"
  if ! git -C "$VAULT_DIR" diff --cached --quiet -- "${pushed_rels[@]}"; then
    git -C "$VAULT_DIR" commit -m "docs(daily): sync ${pushed_dates[*]} from Ghost"
    echo "Committed: ${pushed_dates[*]}"
  else
    echo "No changes to commit."
  fi
fi
