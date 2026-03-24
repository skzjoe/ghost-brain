# EOD Session Log — Cron Prompt

Run at 23:00 Bangkok time. Consolidate today's daily note, capture second-brain items, and check drift.

**Do NOT push to Obsidian** — the separate Obsidian Push cron (23:05) handles that after this job finishes.

## Steps

1) **Determine TODAY** in Asia/Bangkok (YYYY-MM-DD).

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

8) **Commitment ↔ ACTIVE_WORK cross-check**:
   - Scan ACTIVE_WORK.md for any workstream with a deliverable date or deadline.
   - Check if a matching entry exists in `memory/commitments.md`.
   - If missing → auto-append a commitment entry with the deadline.
   - Also check: any commitment in commitments.md whose project is not in ACTIVE_WORK → flag as possibly stale.

9) **Re-index Memory DB**:
   - Run: `GOOGLE_API_KEY=$(cat ~/.openclaw/workspace/secrets/gemini_api_key.txt | tr -d '\n') GHOST_EMBEDDING_PROVIDER=gemini python3 ~/.openclaw/workspace/scripts/ghost_memory_db.py pipeline`
   - This re-indexes all memory files (Gemini 256d embeddings), rebuilds knowledge graph links, and deduplicates.
   - Takes ~5s, 0 LLM tokens. If it fails, log the error but continue to step 10.

10) **Detect active fast lanes**:
   - Run: `python3 scripts/detect_active_lanes.py`
   - Generates `.local/active_lanes.txt` — top 5 fast lanes based on this week's work patterns.
   - Pure keyword matching, 0 tokens, <1s. If it fails, skip.

11) **Generate context bridge**:
   - Run: `bash scripts/generate_context_bridge.sh`
   - This creates `.local/session_context.md` — a compact context summary (~500 tokens) for the next session.
   - If it fails, skip (non-critical).

12) **Announce** concise confirmation to {{USER_NAME}}:
   - Summary of what was logged
   - Decisions/people/ideas/commitments captured
   - Learnings captured or promoted
   - Top Next Actions for tomorrow
