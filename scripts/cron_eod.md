# EOD Session Log — Cron Prompt

Run at 23:00 local time. Consolidate today's daily note, capture second-brain items, and check drift.

**Do NOT push to Obsidian** — the separate Obsidian Push cron (23:05) handles that after this job finishes.

## Steps

1) **Determine TODAY** in your configured timezone (YYYY-MM-DD).

2) **Open daily note**: `~/.openclaw/workspace/memory/TODAY.md`
   - If missing: create from template at `memory/TEMPLATE.md`.

3) **Consolidate** (/summary behavior):
   - Merge into one clean block (no duplicate sections).
   - Preserve critical IDs/URLs/commands.
   - Sections: 🧠 Log / ✅ Done / 🧾 Decisions / 📌 Next Actions / 🤝 Follow-ups / 📎 Artifacts

4) **Write back** to the same file.

5) **Second Brain capture** — scan today note. **Dedup**: read each target file first; skip entries that already exist.
   a) Significant decisions → append to `memory/decisions.md` (date, decision, reasoning)
   b) People in work context → update `memory/people.md` (role, status, last interaction)
   c) Parked ideas ("น่าจะ...", "สักวัน...", "ลองดู...") → append to `memory/ideas.md`
   d) Commitments made → append to `memory/commitments.md` (date, to whom, what was promised)
   e) Follow-up items → update `memory/follow-ups.md` (add new, update existing status)

6) **Learnings scan**:
   - Scan for corrections, errors, or feedback patterns.
   - Log to appropriate `.learnings/` file.
   - Check if pending learnings qualify for promotion (recurrence >= 3).

7) **ACTIVE_WORK.md drift check**:
   - Compare today note against ACTIVE_WORK.md.
   - Update changed statuses/blockers/paths.
   - Add new workstreams that appeared today.

8) **Re-index Memory DB**:
   - Run: `python3 ~/.openclaw/workspace/scripts/ghost_memory_db.py index`
   - This is incremental (~1s, 0 tokens) — only indexes changed/new files.

9) **Announce** concise confirmation to {{USER_NAME}}:
   - Summary of what was logged
   - Decisions/people/ideas/commitments captured
   - Learnings captured or promoted
   - Top Next Actions for tomorrow
