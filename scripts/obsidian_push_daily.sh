#!/usr/bin/env bash
set -euo pipefail

# Push a daily note to your Obsidian vault.
# Usage: bash obsidian_push_daily.sh YYYY-MM-DD
#
# Configure OBSIDIAN_DAILY_DIR below to match your vault path.
# Examples:
#   macOS:  ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyVault/10_Daily
#   Linux:  ~/obsidian-vault/10_Daily
#   WSL:    /mnt/c/Users/YOU/iCloudDrive/iCloud~md~obsidian/MyVault/10_Daily

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

# ━━━ CONFIGURE THIS ━━━
OBSIDIAN_DAILY_DIR=""  # Set your Obsidian daily notes path here
# ━━━━━━━━━━━━━━━━━━━━━━

if [[ -z "$OBSIDIAN_DAILY_DIR" ]]; then
  echo "❌ OBSIDIAN_DAILY_DIR not configured. Edit this script first."
  echo "   Path: $0"
  exit 1
fi

DATE="${1:-$(date +%Y-%m-%d)}"
SRC="$WORKSPACE/memory/$DATE.md"
DST="$OBSIDIAN_DAILY_DIR/$DATE.md"

if [[ ! -f "$SRC" ]]; then
  echo "⏭️  No daily note for $DATE"
  exit 0
fi

mkdir -p "$OBSIDIAN_DAILY_DIR"
cp "$SRC" "$DST"
echo "✅ Pushed $DATE → $DST"
