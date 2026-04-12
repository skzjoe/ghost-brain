---
name: health
description: "Ghost product health — consolidated view of memory, learning loop, execution state, proactive systems, and capture pipeline. Ghost-layer only; delegates platform checks to OpenClaw."
user-invocable: true
---

# /health

Ghost product health check. Reports on Ghost-layer concerns only — memory, learning, execution state, proactive systems, and capture pipeline. Does NOT check gateway, channels, config, models, or security (those are OpenClaw's job via `openclaw status` / `openclaw doctor` / `openclaw security audit`).

## Instructions

Run all checks below, then compose the output.

---

### Section 1 — 🧠 Memory

1. **MEMORY.md size + last updated**
   - `wc -c MEMORY.md` → report size in KB
   - Parse `_Last updated:` line or use file modification date
   - Flag ⚠️ if >15KB or >14d stale

2. **Daily notes count (last 30d)**
   - Count `memory/2026-*.md` files with dates within last 30 days
   - Report count (healthy: 20+, warning: <15)

3. **Last capture timestamp**
   - Check modification dates of: `memory/decisions.md`, `memory/people.md`, `memory/ideas.md`, `memory/commitments.md`, `memory/follow-ups.md`
   - Report the most recent modification as "X ago"

4. **Memory DB stats**
   - Run: `bash scripts/run_memory_pipeline.sh check 2>/dev/null`
   - Extract item count + link count if available
   - If script missing or fails, report "not configured"

---

### Section 2 — 🔄 Learning Loop

1. **Total learnings**
   - Count entries in `.learnings/LEARNINGS.md` (lines starting with `- ` or `## ` that represent rules/learnings)
   - Count entries in `.learnings/domains/*.md` and `.learnings/projects/*.md`
   - Report combined total

2. **Overdue for review**
   - Run: `python3 scripts/learning_review.py due 2>/dev/null`
   - Count lines in output (each = one overdue item)
   - If script missing or fails, check `.learnings/learning-review-state.json` for `nextReviewDate` fields in the past

3. **Pending promotion**
   - Search `.learnings/` files for lines containing `status: pending` or `[pending]`
   - Report count

4. **Last reflection**
   - Check modification dates of files in `.learnings/` directory
   - Report the most recent modification as "today", "yesterday", or "Xd ago"

---

### Section 3 — 📌 Execution State

1. **Active workstreams count**
   - Parse `ACTIVE_WORK.md` for workstream entries (lines starting with `##` or similar headers that denote distinct workstreams)
   - Report count

2. **Commitments due ≤7d**
   - Parse `memory/commitments.md` for entries with deadlines
   - Count entries where deadline is within 7 days from today
   - List them briefly (name + deadline)

3. **Stale follow-ups**
   - Parse `memory/follow-ups.md` for active entries
   - Count items where the "since" or "added" date is >7 days ago
   - Flag count

4. **Focus layer age**
   - Check `memory/now.md` modification date
   - Report as "generated Xh ago" or "generated Xd ago"
   - Flag ⚠️ if >24h old

---

### Section 4 — 💓 Proactive Systems

1. **Heartbeat**
   - Read `memory/heartbeat-state.json` → extract `lastRunAt` field
   - Report how long ago it ran
   - ✅ if <2h, ⚠️ if 2-6h, ❌ if >6h or missing

2. **Morning briefing**
   - Run `openclaw cron list` and find the morning briefing cron
   - Report status (ok/idle/error) and last run time
   - ✅ if ran today on a workday, ⚠️ if missed

3. **EOD log**
   - From same `openclaw cron list` output, find EOD session log cron
   - Report status and last run time

4. **Weekly distill**
   - From same `openclaw cron list` output, find weekly memory distill cron
   - Report status and last run time
   - ✅ if ran within 7d

---

### Section 5 — 📊 Capture Pipeline (last 7d)

1. **Decisions captured** — count entries in `memory/decisions.md` with dates in last 7 days
2. **People updated** — count entries in `memory/people.md` with "Last mentioned" or dates in last 7 days
3. **Ideas captured** — count entries in `memory/ideas.md` with dates in last 7 days
4. **Commitments active** — count non-fulfilled entries in `memory/commitments.md`

---

### Section 6 — Overall Verdict

Determine overall status based on findings:

- **🟢 Healthy** — no ❌ findings, at most 1-2 minor ⚠️
- **🟡 Attention needed** — multiple ⚠️ or 1 ❌ that isn't critical
- **🔴 Issues** — multiple ❌ or critical systems down

Add a one-line summary highlighting the most important finding (e.g., "20 learning reviews overdue — run /learnings").

---

## Output Format

```
👻 Ghost Health — {date time}
══════════════════════════════

🧠 Memory
  MEMORY.md            : {size} ({ok/⚠️ bloat})
  Daily notes (30d)    : {count} files
  Last capture         : {time ago}
  Memory DB            : {items} items, {links} links

🔄 Learning Loop
  Total learnings      : {count}
  Overdue for review   : {count}
  Pending promotion    : {count}
  Last reflection      : {when}

📌 Execution State
  Active workstreams   : {count}
  Commitments due ≤7d  : {count} {details if any}
  Stale follow-ups     : {count}
  Focus layer          : generated {age}

💓 Proactive Systems
  Heartbeat            : {✅/⚠️/❌} last run {time ago}
  Morning briefing     : {✅/⚠️/❌} last run {time}
  EOD log              : {✅/⚠️/❌} last run {time}
  Weekly distill       : {✅/⚠️/❌} last run {time}

📊 Capture Pipeline (7d)
  Decisions captured   : {count}
  People updated       : {count}
  Ideas captured       : {count}
  Commitments active   : {count}

Overall: {🟢/🟡/🔴} {verdict} ({one-line summary})
```

Keep output plain text with emoji — optimized for Telegram (no wide tables, no markdown formatting).

---

## What /health does NOT check

These are OpenClaw's responsibility — use the listed commands instead:

| Concern | Command |
|---|---|
| Gateway health | `openclaw status`, `openclaw health` |
| Channel connectivity | `openclaw channels`, `openclaw doctor` |
| Model availability | `openclaw status` |
| Config validity | `openclaw doctor` |
| Security posture | `openclaw security audit` |
