#!/usr/bin/env bash
set -euo pipefail

# Push one or more daily notes to an Obsidian vault.
# Usage:
#   bash scripts/obsidian_push_daily.sh YYYY-MM-DD [YYYY-MM-DD ...]
#
# Configure with env vars or by editing defaults below.
# Examples:
#   macOS:  ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/MyVault/10_Daily
#   Linux:  ~/obsidian-vault/10_Daily
#   WSL:    /mnt/c/Users/YOU/iCloudDrive/iCloud~md~obsidian/MyVault/10_Daily

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SRC_DIR="${OPENCLAW_MEMORY_DIR:-$WORKSPACE/memory}"
OBSIDIAN_DAILY_DIR="${OBSIDIAN_DAILY_DIR:-}"
OBSIDIAN_VAULT_DIR="${OBSIDIAN_VAULT_DIR:-}"
OBSIDIAN_AUTO_COMMIT="${OBSIDIAN_AUTO_COMMIT:-0}"

if [[ -z "$OBSIDIAN_DAILY_DIR" ]]; then
  echo "❌ OBSIDIAN_DAILY_DIR not configured."
  echo "   Export OBSIDIAN_DAILY_DIR or edit: $0"
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 YYYY-MM-DD [YYYY-MM-DD ...]" >&2
  exit 2
fi

mkdir -p "$OBSIDIAN_DAILY_DIR"

declare -a pushed_dates=()
declare -a pushed_rel_paths=()

for d in "$@"; do
  src="$SRC_DIR/$d.md"
  dst="$OBSIDIAN_DAILY_DIR/$d.md"

  if [[ ! -f "$src" ]]; then
    echo "Missing source: $src" >&2
    exit 3
  fi

  cp -f "$src" "$dst"
  pushed_dates+=("$d")
  echo "✅ Pushed $d → $dst"

  if [[ -n "$OBSIDIAN_VAULT_DIR" && "$dst" == "$OBSIDIAN_VAULT_DIR"/* ]]; then
    pushed_rel_paths+=("${dst#"$OBSIDIAN_VAULT_DIR"/}")
  fi
done

if [[ "$OBSIDIAN_AUTO_COMMIT" == "1" && -n "$OBSIDIAN_VAULT_DIR" ]] \
  && git -C "$OBSIDIAN_VAULT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  && [[ ${#pushed_rel_paths[@]} -gt 0 ]]; then
  git -C "$OBSIDIAN_VAULT_DIR" add -- "${pushed_rel_paths[@]}"

  if ! git -C "$OBSIDIAN_VAULT_DIR" diff --cached --quiet -- "${pushed_rel_paths[@]}"; then
    commit_message="docs(daily): sync ${pushed_dates[*]} from ghost-brain"
    git -C "$OBSIDIAN_VAULT_DIR" commit -m "$commit_message"
    echo "Committed to Obsidian git: $commit_message"
  else
    echo "No git changes to commit for pushed daily note(s)."
  fi
fi
