---
name: weekly
description: "Weekly review — summarize the week from daily notes, surface patterns, suggest what to archive/promote/drop."
user-invocable: true
---

# /weekly

Weekly review that synthesizes daily notes into actionable insights.

## Instructions

1. **Gather data**: Read daily notes from the last 7 days (`memory/YYYY-MM-DD.md`). Also read:
   - `memory/decisions.md` — decisions from this week
   - `memory/follow-ups.md` — active follow-ups
   - `memory/commitments.md` — active commitments
   - `memory/ideas.md` — active ideas
   - `ACTIVE_WORK.md` — current workstreams

2. **Synthesize** into this format:

```
📅 Weekly Review — {date range}

━━━ 🏆 Wins ━━━
- {things completed or shipped this week}

━━━ 🔄 Patterns ━━━
- {recurring themes, repeated work types, common blockers}

━━━ ⚠️ Attention Needed ━━━
- {stale follow-ups approaching 14d}
- {commitments due soon}
- {workstreams with no activity this week}
- {ideas parked >30 days}

━━━ 📊 Activity ━━━
- Daily notes: {X}/7 written
- Decisions logged: {count}
- Follow-ups: {active count} active, {completed count} completed this week
- Ideas captured: {count new this week}

━━━ 🧹 Housekeeping Suggestions ━━━
- Archive: {completed projects, fulfilled commitments, resolved follow-ups to move}
- Promote: {ideas with repeated mentions → ACTIVE_WORK.md?}
- Drop: {stale items with no activity >30d}
- Update: {ACTIVE_WORK.md drift from reality?}

━━━ 📌 Next Week Focus ━━━
- {top 3 priorities based on patterns, commitments, and open items}
```

3. **Write** the weekly review to `memory/weekly/{YYYY}-W{WW}.md` (create dir if needed).

4. **Auto-actions** (suggest, don't auto-apply):
   - If completed follow-ups exist → suggest moving to Completed section
   - If ACTIVE_WORK.md has projects with no activity → suggest marking dormant
   - If ideas have been mentioned 3+ times → suggest promoting to ACTIVE_WORK.md
   - If decisions contradict each other → flag

5. **Push to Obsidian** if the push script exists:
   - Copy to Obsidian `15_Weekly/` directory
