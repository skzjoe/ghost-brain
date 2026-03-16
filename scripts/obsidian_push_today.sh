#!/usr/bin/env bash
# Push today's daily note to Obsidian.
# Called by the Obsidian Push cron (23:05).
DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$DIR/obsidian_push_daily.sh" "$(date +%Y-%m-%d)"
