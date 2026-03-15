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

# 1. Daily Morning Summary (08:00)
openclaw cron create \
  --name "Daily Morning Summary" \
  --schedule "cron 0 8 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_morning.md" \
  --target main \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Morning Summary"

# 2. Commitment Deadline Alerts (08:30)
openclaw cron create \
  --name "Commitment Deadline Alerts" \
  --schedule "cron 30 8 * * *" \
  --prompt-file "$SCRIPTS/cron_commitment_alerts.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Commitment Alerts"

# 3. Weekly Core Backup (Sunday 20:00)
openclaw cron create \
  --name "Weekly Core Backup" \
  --schedule "cron 0 20 * * 0" \
  --prompt-file "$SCRIPTS/cron_backup.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Weekly Backup"

# 4. Weekly Distillation (Sunday 21:00)
openclaw cron create \
  --name "Weekly Distillation" \
  --schedule "cron 0 21 * * 0 @ $TZ" \
  --prompt-file "$SCRIPTS/cron_weekly_distillation.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Weekly Distillation"

# 5. Daily EOD Summary (23:00)
openclaw cron create \
  --name "Daily EOD Summary" \
  --schedule "cron 0 23 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_eod.md" \
  --target main \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ EOD Summary"

# 6. Obsidian Push Daily Note (23:05)
openclaw cron create \
  --name "Obsidian Push Daily Note" \
  --schedule "cron 5 23 * * * @ $TZ" \
  --prompt "Run: bash scripts/obsidian_push_today.sh — if successful reply HEARTBEAT_OK" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Obsidian Push"

# 7. Gateway Health Check (every 6h)
openclaw cron create \
  --name "Gateway Health Check" \
  --schedule "cron 0 */6 * * *" \
  --prompt-file "$SCRIPTS/cron_gateway_health.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Gateway Health"

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
echo "✅ Monthly Archive"

# 10. Monthly Learnings Review (1st of month 10:00)
openclaw cron create \
  --name "Monthly Learnings Review" \
  --schedule "cron 0 10 1 * *" \
  --prompt-file "$SCRIPTS/cron_learnings_review.md" \
  --model "anthropic/claude-sonnet-4-6"
echo "✅ Monthly Learnings Review"

echo ""
echo "🎉 All 10 cron jobs created. Verify: openclaw cron list"
