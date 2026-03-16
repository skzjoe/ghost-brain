#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain — Cron Setup (Interactive)
# Creates all 10 automated routines for your Ghost Brain.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPTS="$WORKSPACE/scripts"

echo "👻 Ghost Brain — Cron Setup"
echo "   Workspace: $WORKSPACE"
echo ""

# ── Preflight checks ──

if [[ ! -d "$WORKSPACE" ]]; then
  echo "❌ Workspace not found: $WORKSPACE"
  echo "   Set OPENCLAW_WORKSPACE or run 'openclaw setup' first."
  exit 1
fi

if ! command -v openclaw &>/dev/null; then
  echo "❌ openclaw CLI not found. Install OpenClaw first."
  exit 1
fi

# ── Interactive setup ──

echo "🌍 What timezone? (IANA format, e.g. America/New_York, Europe/London, Asia/Tokyo)"
read -rp "   Timezone [UTC]: " TZ
TZ="${TZ:-UTC}"
echo ""

echo "🤖 What model for cron jobs? Examples:"
echo "   - anthropic/claude-sonnet-4-6"
echo "   - openai/gpt-4o"
echo "   - google/gemini-2.0-flash"
read -rp "   Model [anthropic/claude-sonnet-4-6]: " MODEL
MODEL="${MODEL:-anthropic/claude-sonnet-4-6}"
echo ""

echo "📓 Push daily notes to Obsidian?"
read -rp "   (y/n) [n]: " USE_OBSIDIAN
USE_OBSIDIAN="${USE_OBSIDIAN:-n}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Timezone: $TZ"
echo "   Model:    $MODEL"
echo "   Obsidian: $USE_OBSIDIAN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -rp "Create cron jobs? (y/n) [y]: " CONFIRM
CONFIRM="${CONFIRM:-y}"
[[ "$CONFIRM" != "y" ]] && { echo "Aborted."; exit 0; }
echo ""

# ── Helper: load prompt from file or use fallback ──

load_prompt() {
  local file="$1" fallback="$2"
  if [[ -f "$file" ]]; then
    cat "$file"
  else
    echo "$fallback"
  fi
}

PASS=0
FAIL=0

create_cron() {
  local name="$1" cron_expr="$2" prompt="$3"
  shift 3
  local extra=("$@")

  if openclaw cron add \
    --name "$name" \
    --cron "$cron_expr" \
    --tz "$TZ" \
    --model "$MODEL" \
    --message "$prompt" \
    "${extra[@]}" 2>/dev/null; then
    echo "   ✅ $name"
    ((PASS++))
  else
    echo "   ❌ $name — failed"
    ((FAIL++))
  fi
}

echo "🕐 Creating cron jobs..."
echo ""

# ── Daily ──

# 1. Morning Briefing (08:00)
create_cron "Morning Briefing" "0 8 * * *" \
  "$(load_prompt "$SCRIPTS/cron_morning.md" \
  "Read ACTIVE_WORK.md + check calendar + unread emails. Compose a morning briefing with top 3 priorities, blockers, and meeting prep. Keep it concise.")" \
  --announce

# 2. Morning Learning Review (08:15)
create_cron "Morning Learning Review" "15 8 * * *" \
  "$(load_prompt "$SCRIPTS/cron_learnings_review.md" \
  "Run: python3 scripts/sr_review.py scan && python3 scripts/sr_review.py due 3. If nothing due, reply HEARTBEAT_OK. If items due, send a brief review with the key lesson and which area it applies to.")" \
  --announce

# 3. Commitment Deadline Alert (08:30)
create_cron "Commitment Deadline Alert" "30 8 * * *" \
  "$(load_prompt "$SCRIPTS/cron_commitment_alerts.md" \
  "Read memory/commitments.md. Alert if any commitments are due within 2 days or overdue. Reply HEARTBEAT_OK if nothing due.")" \
  --announce

# 4. EOD Session Log (23:00)
create_cron "EOD Session Log" "0 23 * * *" \
  "$(load_prompt "$SCRIPTS/cron_eod.md" \
  "Summarize today's work into the daily note. Capture decisions, people, ideas, commitments to second brain files. Check ACTIVE_WORK.md for drift.")" \
  --announce

# 5. Obsidian Daily Sync (23:05) — optional
if [[ "$USE_OBSIDIAN" == "y" ]]; then
  create_cron "Obsidian Daily Sync" "5 23 * * *" \
    "Run: bash scripts/obsidian_push_today.sh — if successful reply HEARTBEAT_OK."
fi

# ── Every N hours ──

# 6. Gateway Healthcheck (every 6h)
create_cron "Gateway Healthcheck" "0 */6 * * *" \
  "$(load_prompt "$SCRIPTS/cron_gateway_health.md" \
  "Check if the OpenClaw gateway is responsive. Reply HEARTBEAT_OK if alive. Alert if down.")"

# ── Weekly ──

# 7. Weekly Backup (Sunday 20:00)
create_cron "Weekly Backup" "0 20 * * 0" \
  "$(load_prompt "$SCRIPTS/cron_backup.md" \
  "Run: bash scripts/backup_core.sh — reply HEARTBEAT_OK if successful.")"

# 8. Weekly Memory Distill (Sunday 21:00)
create_cron "Weekly Memory Distill" "0 21 * * 0" \
  "$(load_prompt "$SCRIPTS/cron_weekly_distillation.md" \
  "Read all daily notes this week. Update MEMORY.md + ACTIVE_WORK.md. Review learnings for promotion. Review ideas/follow-ups/commitments. Save weekly summary and announce brief.")" \
  --announce

# 9. Weekly Report (Monday 08:30)
create_cron "Weekly Report" "30 8 * * 1" \
  "$(load_prompt "$SCRIPTS/cron_weekly_report.md" \
  "Generate weekly summary from daily notes + ACTIVE_WORK.md. Include progress, decisions, blockers, next priorities. Save to media/out/reports/.")" \
  --announce

# ── Monthly ──

# 10. Monthly Note Archive (1st of month 06:00)
create_cron "Monthly Note Archive" "0 6 1 * *" \
  "$(load_prompt "$SCRIPTS/cron_archive_notes.md" \
  "Archive daily notes older than 30 days to memory/archive/. Reply HEARTBEAT_OK.")"

# ── Summary ──
TOTAL=$((PASS + FAIL))
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ✅ Created: $PASS / $TOTAL"
[[ $FAIL -gt 0 ]] && echo "   ❌ Failed: $FAIL"
echo ""
echo "   Verify:  openclaw cron list"
echo "   Edit:    openclaw cron edit <id> --cron '0 9 * * *'"
echo "   Remove:  openclaw cron rm <id>"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[[ $FAIL -gt 0 ]] && exit 1
exit 0
