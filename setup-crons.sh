#!/usr/bin/env bash
set -euo pipefail

# Ghost Bootstrap — Cron Setup
# Run this after copying workspace files to set up all automation.
# Adjust schedules/timezones as needed.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPTS="$WORKSPACE/scripts"
TZ="Asia/Bangkok"  # Change to your timezone

echo "🕐 Setting up Ghost cron jobs..."
echo "   Workspace: $WORKSPACE"
echo "   Timezone: $TZ"
echo ""

# 1. Morning Briefing (08:00)
openclaw cron create \
  --name "Morning Briefing" \
  --schedule "cron 0 8 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_morning.md" \
  --target main \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Morning Briefing"

# 2. Commitment Deadline Alert (08:30)
openclaw cron create \
  --name "Commitment Deadline Alert" \
  --schedule "cron 30 8 * * *" \
  --prompt-file "$SCRIPTS/cron_commitment_alerts.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Commitment Deadline Alert"

# 3. Weekly Backup (Sunday 20:00)
openclaw cron create \
  --name "Weekly Backup" \
  --schedule "cron 0 20 * * 0" \
  --prompt-file "$SCRIPTS/cron_backup.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Weekly Backup"

# 4. Weekly Memory Distill (Sunday 21:00)
openclaw cron create \
  --name "Weekly Memory Distill" \
  --schedule "cron 0 21 * * 0 @ $TZ" \
  --prompt-file "$SCRIPTS/cron_weekly_distillation.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Weekly Memory Distill"

# 5. EOD Session Log (23:00)
openclaw cron create \
  --name "EOD Session Log" \
  --schedule "cron 0 23 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_eod.md" \
  --target main \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ EOD Session Log"

# 6. Obsidian Daily Sync (23:05)
openclaw cron create \
  --name "Obsidian Daily Sync" \
  --schedule "cron 5 23 * * * @ $TZ" \
  --prompt "Run: bash scripts/obsidian_push_today.sh — if successful reply HEARTBEAT_OK" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Obsidian Daily Sync"

# 7. Gateway Healthcheck (every 6h)
openclaw cron create \
  --name "Gateway Healthcheck" \
  --schedule "cron 0 */6 * * *" \
  --prompt-file "$SCRIPTS/cron_gateway_health.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Gateway Healthcheck"

# 8. Weekly Report (Monday 08:30)
openclaw cron create \
  --name "Weekly Report" \
  --schedule "cron 30 8 * * 1" \
  --prompt-file "$SCRIPTS/cron_weekly_report.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Weekly Report"

# 9. Monthly Note Archive (1st of month 06:00)
openclaw cron create \
  --name "Monthly Note Archive" \
  --schedule "cron 0 6 1 * *" \
  --prompt-file "$SCRIPTS/cron_archive_notes.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Monthly Note Archive"

# 10. Morning Learning Review (08:15 daily)
openclaw cron create \
  --name "Morning Learning Review" \
  --schedule "cron 15 8 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_learnings_review.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Morning Learning Review"

echo ""
echo "🎉 All 10 cron jobs created. Verify: openclaw cron list"
