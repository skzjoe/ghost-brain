# Commitment Deadline Alert — Cron Prompt

Check for commitments due within 2 days or overdue.

## Steps
1. Read `memory/commitments.md`
2. Determine today's date (Asia/Bangkok)
3. For each Active commitment with a deadline:
   - If deadline is today or overdue → 🚨 URGENT alert
   - If deadline is within 2 days → ⚠️ WARNING alert
4. If no alerts needed, reply HEARTBEAT_OK
5. If alerts exist, compose a concise message to {{USER_NAME}} listing each commitment, who it's to, what was promised, and the deadline
