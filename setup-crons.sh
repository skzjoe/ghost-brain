#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain — Cron Setup (Interactive)
# Creates all 10 automated routines for your Ghost Brain.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPTS="$WORKSPACE/scripts"

echo "👻 Ghost Brain — Cron Setup"
echo "   Workspace: $WORKSPACE"
echo ""

# Check workspace exists
if [[ ! -d "$WORKSPACE" ]]; then
  echo "❌ Workspace not found: $WORKSPACE"
  echo "   Set OPENCLAW_WORKSPACE or run 'openclaw setup' first."
  exit 1
fi

# Check openclaw CLI exists
if ! command -v openclaw &>/dev/null; then
  echo "❌ openclaw CLI not found. Install OpenClaw first."
  exit 1
fi

# ── Interactive setup ──

# Timezone
echo "🌍 What timezone? (IANA format, e.g. America/New_York, Europe/London, Asia/Tokyo)"
read -rp "   Timezone [UTC]: " TZ
TZ="${TZ:-UTC}"
echo ""

# Model
echo "🤖 What model for cron jobs? Examples:"
echo "   - anthropic/claude-sonnet-4-6"
echo "   - openai/gpt-4o"
echo "   - google/gemini-2.0-flash"
echo "   - (any model your provider supports)"
read -rp "   Model [anthropic/claude-sonnet-4-6]: " MODEL
MODEL="${MODEL:-anthropic/claude-sonnet-4-6}"
echo ""

# Obsidian
echo "📓 Do you use Obsidian for notes?"
read -rp "   Push daily notes to Obsidian? (y/n) [n]: " USE_OBSIDIAN
USE_OBSIDIAN="${USE_OBSIDIAN:-n}"
echo ""

# Confirm
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Timezone: $TZ"
echo "   Model:    $MODEL"
echo "   Obsidian: $USE_OBSIDIAN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -rp "Create cron jobs? (y/n) [y]: " CONFIRM
CONFIRM="${CONFIRM:-y}"
[[ "$CONFIRM" != "y" ]] && { echo "Aborted."; exit 0; }
echo ""

echo "🕐 Creating cron jobs..."
echo ""

# ── Helper ──
create_cron() {
  local name="$1" schedule="$2" prompt_arg="$3" extra="${4:-}"
  
  if openclaw cron add \
    --name "$name" \
    --cron "$schedule" \
    --tz "$TZ" \
    $prompt_arg \
    --model "$MODEL" \
    $extra 2>/dev/null; then
    echo "   ✅ $name"
  else
    echo "   ❌ $name — failed (check 'openclaw cron add --help')"
  fi
}

# ── Daily ──

# 1. Morning Briefing (08:00)
create_cron "Morning Briefing" "0 8 * * *" \
  "--message \"$(cat "$SCRIPTS/cron_morning.md" 2>/dev/null || echo 'Read ACTIVE_WORK.md + calendar + email → compose morning briefing')\"" \
  "--announce --to last"

# 2. Morning Learning Review (08:15)
create_cron "Morning Learning Review" "15 8 * * *" \
  "--message \"$(cat "$SCRIPTS/cron_learnings_review.md" 2>/dev/null || echo 'Run: python3 scripts/sr_review.py scan && python3 scripts/sr_review.py due 3. If nothing due, reply HEARTBEAT_OK.')\"" \
  "--announce --to last"

# 3. Commitment Deadline Alert (08:30)
create_cron "Commitment Deadline Alert" "30 8 * * *" \
  "--message \"$(cat "$SCRIPTS/cron_commitment_alerts.md" 2>/dev/null || echo 'Read memory/commitments.md → alert if any due within 2 days. Reply HEARTBEAT_OK if nothing due.')\"" \
  "--announce --to last"

# 4. EOD Session Log (23:00)
create_cron "EOD Session Log" "0 23 * * *" \
  "--message \"$(cat "$SCRIPTS/cron_eod.md" 2>/dev/null || echo 'Summarize today into daily note → capture decisions/people/ideas/commitments to second brain files.')\"" \
  "--announce --to last"

# 5. Obsidian Daily Sync (23:05) — optional
if [[ "$USE_OBSIDIAN" == "y" ]]; then
  create_cron "Obsidian Daily Sync" "5 23 * * *" \
    "--message \"Run: bash scripts/obsidian_push_today.sh — if successful reply HEARTBEAT_OK\""
fi

# ── Every N hours ──

# 6. Gateway Healthcheck (every 6h)
create_cron "Gateway Healthcheck" "0 */6 * * *" \
  "--message \"$(cat "$SCRIPTS/cron_gateway_health.md" 2>/dev/null || echo 'Check gateway status. Reply HEARTBEAT_OK if alive. Alert if down.')\""

# ── Weekly ──

# 7. Weekly Backup (Sunday 20:00)
create_cron "Weekly Backup" "0 20 * * 0" \
  "--message \"$(cat "$SCRIPTS/cron_backup.md" 2>/dev/null || echo 'Run: bash scripts/backup_core.sh — reply HEARTBEAT_OK if successful.')\""

# 8. Weekly Memory Distill (Sunday 21:00)
create_cron "Weekly Memory Distill" "0 21 * * 0" \
  "--message \"$(cat "$SCRIPTS/cron_weekly_distillation.md" 2>/dev/null || echo 'Read all daily notes this week → update MEMORY.md + ACTIVE_WORK.md → review learnings → announce weekly brief.')\"" \
  "--announce --to last"

# 9. Weekly Report (Monday 08:30)
create_cron "Weekly Report" "30 8 * * 1" \
  "--message \"$(cat "$SCRIPTS/cron_weekly_report.md" 2>/dev/null || echo 'Generate weekly summary report from daily notes + ACTIVE_WORK.md. Save to media/out/reports/.')\"" \
  "--announce --to last"

# ── Monthly ──

# 10. Monthly Note Archive (1st of month 06:00)
create_cron "Monthly Note Archive" "0 6 1 * *" \
  "--message \"$(cat "$SCRIPTS/cron_archive_notes.md" 2>/dev/null || echo 'Archive daily notes older than 30 days to memory/archive/. Reply HEARTBEAT_OK.')\""

# ── Summary ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CREATED=$(openclaw cron list 2>/dev/null | grep -c "ok\|idle" || echo "?")
echo "✅ Done! $CREATED cron jobs active."
echo ""
echo "Verify: openclaw cron list"
echo "Edit:   openclaw cron edit <id> --cron '0 9 * * *' --tz '$TZ'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
