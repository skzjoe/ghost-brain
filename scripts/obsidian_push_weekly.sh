#!/usr/bin/env bash
set -euo pipefail

# Push a weekly note to your Obsidian vault.
# Usage: bash obsidian_push_weekly.sh YYYY-Www (e.g. 2026-W11)
#
# Configure OBSIDIAN_WEEKLY_DIR below.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

# ━━━ CONFIGURE THIS ━━━
OBSIDIAN_WEEKLY_DIR=""  # e.g. ~/obsidian-vault/15_Weekly
# ━━━━━━━━━━━━━━━━━━━━━━

if [[ -z "$OBSIDIAN_WEEKLY_DIR" ]]; then
  echo "❌ OBSIDIAN_WEEKLY_DIR not configured. Edit this script first."
  echo "   Path: $0"
  exit 1
fi

WEEK="${1:?Usage: obsidian_push_weekly.sh YYYY-Www}"
SRC="$WORKSPACE/memory/weekly/$WEEK.md"
DST="$OBSIDIAN_WEEKLY_DIR/$WEEK.md"

if [[ ! -f "$SRC" ]]; then
  echo "⏭️  No weekly note for $WEEK"
  exit 0
fi

mkdir -p "$OBSIDIAN_WEEKLY_DIR"
cp "$SRC" "$DST"
echo "✅ Pushed $WEEK → $DST"
