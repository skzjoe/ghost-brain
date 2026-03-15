# Weekly Report — Cron Prompt

Generate a professional weekly summary report every Monday morning for {{USER_NAME}}.

## Steps

1) **Determine date range**: previous Mon–Sun (Asia/Bangkok)

2) **Gather data**:
   - Read all daily notes from the week: `memory/YYYY-MM-DD.md` (Mon through Sun)
   - Read `ACTIVE_WORK.md` for current workstream status
   - Read `memory/decisions.md` — filter decisions from this week
   - Read `memory/commitments.md` — any new or fulfilled commitments
   - Read `memory/follow-ups.md` — status changes this week

3) **Compose report** in Markdown with these sections:
   ```
   # Weekly Report: [date range]
   ## Executive Summary (3-5 bullet highlights)
   ## Workstream Progress
   - For each active workstream: status, what moved, blockers
   ## Key Decisions Made
   ## Commitments & Follow-ups
   - New commitments made
   - Follow-ups resolved / still pending
   ## Metrics (if available)
   - Tasks completed
   - Blockers resolved vs new
   ## Next Week Focus
   - Top 3 priorities
   - Known risks/blockers
   ```

4) **Save report**:
   - Markdown: `media/out/reports/weekly-YYYY-MM-DD.md`
   - Generate PDF: use the nano-pdf skill or pandoc if available
   - PDF: `media/out/reports/weekly-YYYY-MM-DD.pdf`

5) **Push to Obsidian**:
   - Copy markdown report to `{{OBSIDIAN_VAULT_PATH}}/15_Weekly/report-YYYY-MM-DD.md`

6) **Announce** to {{USER_NAME}} with a brief summary + file paths + "Report saved → Obsidian 15_Weekly/"

## Quality
- Professional tone, concise, scannable
- Include specific deliverables, not vague status
- Flag risks proactively
