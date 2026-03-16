#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain — Cron Setup
# Interactive setup for all 12 automated routines.
# Run after install.sh to activate automation.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPTS="$WORKSPACE/scripts"

echo "👻 Ghost Brain — Cron Setup"
echo ""

# ── Interactive config ──

# Timezone
read -rp "🌍 Timezone (e.g. America/New_York, Europe/London, Asia/Tokyo) [UTC]: " TZ_INPUT
TZ="${TZ_INPUT:-UTC}"
echo "   Using: $TZ"
echo ""

# Model
echo "🤖 Which model for cron jobs? (these run background tasks, cost-efficient is fine)"
echo "   Examples:"
echo "     anthropic/claude-sonnet-4-6"
echo "     openai/gpt-4.1-mini"
echo "     google/gemini-2.5-flash"
echo ""
read -rp "   Model [anthropic/claude-sonnet-4-6]: " MODEL_INPUT
MODEL="${MODEL_INPUT:-anthropic/claude-sonnet-4-6}"
echo "   Using: $MODEL"
echo ""

# Obsidian (optional)
read -rp "📓 Do you use Obsidian for daily notes? (y/N): " USE_OBSIDIAN
echo ""

# Confirm
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Timezone: $TZ"
echo "  Model:    $MODEL"
echo "  Obsidian: ${USE_OBSIDIAN:-N}"
echo "  Workspace: $WORKSPACE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -rp "Proceed? (Y/n): " CONFIRM
[[ "${CONFIRM:-Y}" =~ ^[Nn] ]] && echo "Cancelled." && exit 0

echo ""
echo "🕐 Creating cron jobs..."
echo ""

# ── 1. Daily Morning Summary (08:00) ──
openclaw cron create \
  --name "Daily Morning Summary" \
  --schedule "cron 0 8 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_morning.md" \
  --target main \
  --model "$MODEL"
echo "✅ Morning Summary (08:00)"

# ── 2. Spaced Repetition Review (08:15) ──
openclaw cron create \
  --name "Spaced Repetition Review" \
  --schedule "cron 15 8 * * *" \
  --exact \
  --prompt "Run: python3 scripts/sr_review.py scan && python3 scripts/sr_review.py due 3

If output is SR_OK → reply SR_OK (nothing due).

If learnings are due:
1. Read each learning's full entry from the source file
2. Send a brief message titled '🔄 Learning Review' with:
   - The key lesson in 1-2 sentences
   - Which area it applies to
   - List the IDs for reinforcement
3. After sending, run: python3 scripts/sr_review.py dismiss <ID> for each surfaced item" \
  --model "$MODEL"
echo "✅ Spaced Repetition (08:15)"

# ── 3. Commitment Deadline Alerts (08:30) ──
openclaw cron create \
  --name "Commitment Deadline Alerts" \
  --schedule "cron 30 8 * * *" \
  --prompt-file "$SCRIPTS/cron_commitment_alerts.md" \
  --model "$MODEL"
echo "✅ Commitment Alerts (08:30)"

# ── 3. Daily EOD Summary (23:00) ──
openclaw cron create \
  --name "Daily EOD Summary" \
  --schedule "cron 0 23 * * * @ $TZ" \
  --prompt-file "$SCRIPTS/cron_eod.md" \
  --target main \
  --model "$MODEL"
echo "✅ EOD Summary (23:00)"

# ── 4. Obsidian Push (23:05) — optional ──
if [[ "${USE_OBSIDIAN:-N}" =~ ^[Yy] ]]; then
  openclaw cron create \
    --name "Obsidian Push Daily Note" \
    --schedule "cron 5 23 * * * @ $TZ" \
    --prompt "Run: bash scripts/obsidian_push_today.sh — if successful reply HEARTBEAT_OK" \
    --model "$MODEL"
  echo "✅ Obsidian Push (23:05)"
  echo "   ⚠️  You'll need to create scripts/obsidian_push_today.sh for your vault path"
else
  echo "⏭️  Obsidian Push — skipped"
fi

# ── 5. Gateway Health Check (every 6h) ──
openclaw cron create \
  --name "Gateway Health Check" \
  --schedule "cron 0 */6 * * *" \
  --prompt-file "$SCRIPTS/cron_gateway_health.md" \
  --model "$MODEL"
echo "✅ Gateway Health (every 6h)"

# ── 6. Weekly Core Backup (Sunday 20:00) ──
openclaw cron create \
  --name "Weekly Core Backup" \
  --schedule "cron 0 20 * * 0" \
  --prompt-file "$SCRIPTS/cron_backup.md" \
  --model "$MODEL"
echo "✅ Weekly Backup (Sun 20:00)"

# ── 7. Weekly Distillation (Sunday 21:00) ──
openclaw cron create \
  --name "Weekly Distillation" \
  --schedule "cron 0 21 * * 0 @ $TZ" \
  --prompt-file "$SCRIPTS/cron_weekly_distillation.md" \
  --model "$MODEL"
echo "✅ Weekly Distillation (Sun 21:00)"

# ── 8. Weekly Report (Monday 08:30) ──
openclaw cron create \
  --name "Weekly Report" \
  --schedule "cron 30 8 * * 1" \
  --prompt-file "$SCRIPTS/cron_weekly_report.md" \
  --model "$MODEL"
echo "✅ Weekly Report (Mon 08:30)"

# ── 9. Monthly Note Archive (1st of month 06:00) ──
openclaw cron create \
  --name "Monthly Note Archive" \
  --schedule "cron 0 6 1 * *" \
  --prompt-file "$SCRIPTS/cron_archive_notes.md" \
  --model "$MODEL"
echo "✅ Monthly Archive (1st 06:00)"

# ── 11. Memory DB Incremental Index (23:02) ──
openclaw cron create \
  --name "Memory DB Index" \
  --schedule "cron 2 23 * * * @ $TZ" \
  --exact \
  --prompt "Run: python3 scripts/ghost_memory_db.py index --incremental — reply HEARTBEAT_OK when done" \
  --model "$MODEL"
echo "✅ Memory DB Index (23:02)"

# ── 12. Monthly Learnings Review (1st of month 10:00) ──
openclaw cron create \
  --name "Monthly Learnings Review" \
  --schedule "cron 0 10 1 * *" \
  --prompt-file "$SCRIPTS/cron_learnings_review.md" \
  --model "$MODEL"
echo "✅ Monthly Learnings Review (1st 10:00)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Done! All cron jobs created."
echo ""
echo "Verify: openclaw cron list"
echo "Edit:   openclaw cron update <id> --schedule '...'"
echo "Delete: openclaw cron delete <id>"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
