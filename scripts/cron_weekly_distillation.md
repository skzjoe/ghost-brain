# Weekly Distillation — Cron Prompt

Run every Sunday at 21:00 local time.

## Steps

1) **Read all daily notes** for the current week: `~/.openclaw/workspace/memory/YYYY-MM-DD.md` (Mon–Sun).

2) **Read** current `MEMORY.md` and `ACTIVE_WORK.md`.

3) **Update MEMORY.md**:
   - Add new workstreams, decisions, or context from this week.
   - Remove/archive items no longer relevant.
   - Keep lean: facts and durable context only.

4) **Update ACTIVE_WORK.md**:
   - Sync workstream statuses with this week's reality.
   - Update or remove resolved blockers.
   - Add new workstreams, remove completed/abandoned work.

5) **Learnings review**:
   - Scan `.learnings/` for recurrence >= 3 or patterns seen in 2+ tasks within 30 days.
   - Promote qualifying entries to AGENTS.md, GHOST_PLAYBOOK.md, MEMORY.md, or SOUL.md.
   - Archive stale entries (60+ days no reuse).

6) **Second Brain review**:
   a) `memory/decisions.md` — remove decisions >90 days old that aren't landmark.
   b) `memory/people.md` — update statuses, archive contacts not mentioned 60+ days.
   c) `memory/ideas.md` — promote actionable ideas to ACTIVE_WORK.md, archive ideas parked 30+ days with no interest.
   d) `memory/follow-ups.md` — mark completed items, escalate items stale 14+ days.
   e) `memory/commitments.md` — check for overdue commitments, flag any not fulfilled.

7) **Weekly Brief** for {{USER_NAME}}:
   - Total active workstreams + status (progressing / stale / blocked).
   - Top 3 wins this week.
   - What is blocked and for how long.
   - What is stale (no activity 7+ days) — should it be paused/dropped?
   - Recommended top 3 priorities for next week.
   - Risks or decisions needed.
   - Overdue commitments (if any).

8) **Save Weekly Note**:
   - Compute ISO week: `date +%G-W%V` (e.g. `2026-W11`)
   - Write the full Weekly Brief + all changes/reviews to `memory/weekly/YYYY-Www.md`
   - Format: frontmatter with `week`, `date_range`, `generated` fields, then sections matching the brief
   - Push to Obsidian: `bash scripts/obsidian_push_weekly.sh YYYY-Www`

9) **Announce** to {{USER_NAME}}:
   - Weekly Brief (concise version — full version saved to weekly note)
   - Key changes to MEMORY.md and ACTIVE_WORK.md
   - Learnings promoted or archived
   - Ideas/follow-ups promoted or archived
   - Mention: "Full weekly note saved → Obsidian 15_Weekly/"
