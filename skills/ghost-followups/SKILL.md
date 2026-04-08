---
name: followups
description: "Show active follow-up items from memory/follow-ups.md with staleness indicators."
user-invocable: true
---

# /followups

Show follow-ups with staleness tracking.

## Instructions

1. Read `memory/follow-ups.md`
2. Calculate days since each item's `Since` date
3. Present with staleness:
   - 🟢 Fresh (<7 days)
   - 🟡 Getting stale (7-14 days)
   - 🔴 Stale (>14 days) — suggest action
4. For stale items, suggest: nudge, escalate, archive, or re-scope
5. If an item is vague or not closure-oriented, suggest moving it out of follow-ups into a general watchlist or active work register
6. If empty, say "ไม่มี follow-up ค้างครับ"
