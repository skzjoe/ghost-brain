# Second Brain — Memory Structure

A lightweight system for persistent context across sessions.

## The problem
AI agents wake up fresh every session. Without structured memory, users repeat context constantly. MEMORY.md alone isn't enough — it becomes a dumping ground.

## Solution: 5 specialized files + daily notes

Add one more lightweight layer for execution focus:

### NOW layer (`memory/now.md`)
A compact 24–72 hour execution lens. This is not long-term memory, and it should never become another dumping ground. It exists so morning briefing, EOD, weekly distill, and heartbeat can all look at the same short list of what matters now.

Suggested sections:
```markdown
## Top 3 Priorities
## Due Soon
## Active Blockers / Risks
## Waiting on Others
## Closure Recommendations
## Watchlist / Don't Forget
```

Think of it as the bridge between your large memory system and today's actual work.

### Daily notes (`memory/YYYY-MM-DD.md`)
One per day. Sections:
```markdown
## 🧠 Log
- What happened today (auto-appended by agent)

## ✅ Done
- Completed items

## 🧾 Decisions
- Decisions made and reasoning

## 📌 Next Actions
- What's next

## 🤝 Follow-ups (optional)
- Items waiting on others

## 📎 Artifacts (optional)
- Links to files/outputs created
```

### Decision journal (`memory/decisions.md`)
Captures significant decisions with reasoning. Auto-appended by agent.
```markdown
## 2026-03-15 — Chose Prisma v6 over v7
- **Context:** Setting up Supabase connection for dashboard
- **Decision:** Use Prisma v6
- **Reasoning:** v7 has connection URL complexities on WSL
- **Alternatives:** Direct pg client, Drizzle
```

### People CRM (`memory/people.md`)
Lightweight contact context. Auto-updated when people come up in conversation.
```markdown
## Sarah Chen
- **Role:** Product Manager @ ClientCo
- **Relationship:** Client
- **Context:** Primary contact for Phase 2 rollout
- **Last interaction:** 2026-03-10 — reviewed milestone deliverables
```

### Idea parking lot (`memory/ideas.md`)
Ideas mentioned in passing. Auto-captured when user says "someday", "might want to", "would be cool".
Reviewed weekly → promote to active work or archive after 30 days.

### Commitments (`memory/commitments.md`)
Promises made to clients/stakeholders with deadlines. Auto-captured.
Agent alerts when deadlines approach.

### Follow-ups (`memory/follow-ups.md`)
Items waiting on someone else. Table format with staleness tracking.
```markdown
| Item | Waiting On | Since | Deadline | Status |
|---|---|---|---|---|
| API credentials | DevOps team | 2026-03-10 | 2026-03-17 | Active |
```

**Normalization rule:** only keep concrete, closure-oriented follow-ups here. Avoid mixing in broad watchlists, standing streams, or vague reminders. If an item does not have a clear owner, waiting state, or next closure action, it belongs in active work or a general watchlist, not in `follow-ups.md`.

## How to activate
Add to your `AGENTS.md`:
```markdown
## Second Brain
After conversations, auto-capture:
- Significant decisions → memory/decisions.md (with reasoning)
- People mentioned in work context → memory/people.md
- Future ideas ("someday", "might want to") → memory/ideas.md
- Promises to clients/stakeholders → memory/commitments.md
- Items waiting on others → memory/follow-ups.md

At end of day, consolidate into memory/YYYY-MM-DD.md daily note.
- Refresh `memory/now.md` from the daily note, commitments, follow-ups, and active work so every routine shares the same short-horizon focus.
```

## Weekly distillation
Once a week (cron or manual):
1. Read all daily notes for the week
2. Update MEMORY.md (add new, remove stale)
3. Review ideas — promote or archive
4. Review follow-ups — mark completed, escalate stale, archive vague/non-actionable entries
5. Refresh `memory/now.md` so the next week starts with a clean short-horizon lens
6. Review commitments — flag overdue
7. Save weekly summary to `memory/weekly/YYYY-Www.md`

## Tips
- Keep MEMORY.md lean — it's loaded every message
- Daily notes are cheap — append freely, archive monthly
- The 5 specialized files prevent MEMORY.md from becoming a mess
- Auto-capture is key — don't rely on the user remembering to save
