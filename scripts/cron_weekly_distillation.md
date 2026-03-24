# Weekly Memory Distill — Cron Prompt

Run every Sunday at 21:00 Bangkok time.

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

7) **Cross-reference drift check** (auto-clean):
   - Scan ACTIVE_WORK.md for items marked "✅ Done" or "Completed" still in Current Workstreams → remove them.
   - Scan `memory/follow-ups.md` Active items → if the referenced project is parked/dormant/completed in ACTIVE_WORK → archive the follow-up.
   - Scan `memory/commitments.md` Active entries → if marked "Fulfilled" but still in Active section → move to Fulfilled section.
   - Scan MEMORY.md "Key workstreams" → if a workstream is completed/removed in ACTIVE_WORK → remove from MEMORY.md.
   - Report all changes made in the weekly brief under "🔄 Cross-ref cleanup".

8) **Dormant project review**:
   - Scan ACTIVE_WORK.md "Dormant / On-hold" section.
   - For each dormant project, check if any mention appears in this week's daily notes.
   - If a dormant project has had zero mentions for 30+ days → explicitly ask the user: "archive หรือยังต้องเก็บไว้?"
   - List dormant projects with last-mention date in the weekly brief.

9) **CTO Weekly Brief** for {{USER_NAME}}:
   - Total active workstreams + status (progressing / stale / blocked).
   - Top 3 wins this week.
   - What is blocked and for how long.
   - What is stale (no activity 7+ days) — should it be paused/dropped?
   - Dormant projects nudge (from step 8).
   - Cross-ref cleanup summary (from step 7).
   - Recommended top 3 priorities for next week.
   - Risks or decisions needed.
   - Overdue commitments (if any).

10) **Save Weekly Note**:
   - Compute ISO week: `date +%G-W%V` (e.g. `2026-W11`)
   - Write the full CTO Weekly Brief + all changes/reviews to `memory/weekly/YYYY-Www.md`
   - Format: frontmatter with `week`, `date_range`, `generated` fields, then sections matching the brief
   - Push to Obsidian: `bash scripts/obsidian_push_weekly.sh YYYY-Www`

11) **Re-index Memory DB**:
   - Run: `GOOGLE_API_KEY=$(cat ~/.openclaw/workspace/secrets/gemini_api_key.txt | tr -d '\n') GHOST_EMBEDDING_PROVIDER=gemini python3 ~/.openclaw/workspace/scripts/ghost_memory_db.py pipeline`
   - This re-indexes all memory files, rebuilds knowledge graph links, and deduplicates.
   - If it fails, log the error but continue to step 12.

12) **Announce** to {{USER_NAME}}:
   - CTO Weekly Brief (concise version — full version saved to weekly note)
   - Key changes to MEMORY.md and ACTIVE_WORK.md
   - Learnings promoted or archived
   - Ideas/follow-ups promoted or archived
   - Mention: "Full weekly note saved → Obsidian 15_Weekly/"
