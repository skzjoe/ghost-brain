---
name: audit
description: "Run a full chain audit of the Ghost/OpenClaw system: gateway status, cron jobs, memory, skills, workspace hygiene, security, second brain health, and self-learning effectiveness."
user-invocable: true
---

# /audit

Run a full chain audit of the Ghost/OpenClaw system.

## Instructions

### Core checks
1. `openclaw gateway status` → Runtime, PID, RPC, version
2. `openclaw cron list` → count + check for any `status=error` or `status=failed`
3. Heartbeat config from `openclaw.json`
4. Count: memory files, daily notes, weekly notes, project memories, learnings, skills, projects
5. Backup freshness: `ls -lt backups/ | head -5`
6. `openclaw security audit`

### Silent-fail detection
7. **Cron failures**: scan cron list for any job with status other than `ok` or `idle`. Flag as 🔴.
8. **Daily note today**: check if `memory/YYYY-MM-DD.md` exists for today. Missing after 12:00 = ⚠️.
9. **MEMORY.md freshness**: check `_Last updated:` line. If >14 days ago → ⚠️ context drift risk.
10. **Overdue commitments**: quick scan `memory/commitments.md` for any with deadline < today and status != fulfilled. Count only.
11. **Stale follow-ups**: scan `memory/follow-ups.md` for Active items with `Since` date >14 days ago. Count only.
12. **Git backup status**: run `git -C $WORKSPACE log --oneline -1 2>/dev/null`. If no commits or last commit >7 days → ⚠️. If no git repo → note "not configured".
13. **Obsidian push**: check if today's or yesterday's daily note exists in Obsidian vault path. If unreachable, note it.

### Second Brain health
14. **Capture activity** (is the brain actually capturing?):
    - `memory/decisions.md`: count entries from the last 7 days. 0 = ⚠️ capture may be inactive.
    - `memory/people.md`: check last entry date. >30 days = ⚠️ stale.
    - `memory/ideas.md`: count Active ideas. Count any parked >30 days without review = ⚠️.
    - `memory/commitments.md`: count items missing deadlines. Any = ⚠️ incomplete capture.
    - `memory/follow-ups.md`: count Active items. 0 when work is active = ⚠️ not tracking.
15. **Note coverage**:
    - Count daily notes for last 7 days. <5 on workdays = ⚠️ EOD may not be running.
    - Count weekly notes for last 4 weeks. <3 = ⚠️ distillation not running.
16. **Second Brain score**:
    - 10/10: all 5 files have recent activity + daily/weekly note coverage good
    - 8/10: 1-2 files stale or missing recent entries
    - 6/10: 3+ files stale or no entries this week
    - 4/10: most files empty or untouched

### Self-Learning health
17. **Learning capture** (is the agent learning?):
    - `.learnings/ERRORS.md`: count total entries + date of most recent. >30 days since last = ⚠️.
    - `.learnings/LEARNINGS.md`: count active global rules. 0 = nothing promoted yet.
    - `.learnings/FEATURE_REQUESTS.md`: count open (not done) items.
    - `.learnings/domains/`: list domain files + check if any are empty (size <100 bytes = empty).
    - `.learnings/projects/`: list project files + check if any are empty.
18. **Learning lifecycle**:
    - Any entries with `status: pending` older than 30 days? = ⚠️ review cycle stuck.
    - Has anything been promoted to LEARNINGS.md ever? (count entries)
    - Has anything been archived? (check `.learnings/archive/` has content)
19. **Self-Learning score**:
    - 10/10: recent captures in ERRORS.md, active domain/project files, promotions done, archive used
    - 8/10: captures happening but promotion/archive cycle not active
    - 6/10: only ERRORS.md has entries, domains/projects mostly empty
    - 4/10: .learnings/ exists but barely used
    - 2/10: .learnings/ empty or missing

### Scoring table
Present a scored summary (1-10):

| Area | What to check |
|---|---|
| Runtime | Gateway status, PID, RPC, version |
| Automation | Cron count, last-run, failures, heartbeat config |
| Memory | File counts, daily note today, MEMORY.md freshness |
| Second Brain | Capture activity across all 5 files + note coverage |
| Self-Learning | Capture, promotion, archive lifecycle |
| Learnings | Structure coverage (global/domain/project) |
| Skills | Count, no obvious gaps |
| Workspace | Root hygiene, no loose temp files |
| Resilience | Backup freshness, git status, Obsidian push |
| Security | Audit findings (critical/warn/info) |
| Commitments | Overdue count (0=10, 1-2=8, 3+=6) |

### Output format
1. **Summary table** with all scores
2. **🧠 Second Brain pulse** — one-line health summary (e.g. "4/5 files active, 6/7 daily notes, 1 idea stale >30d")
3. **📝 Self-Learning pulse** — one-line summary (e.g. "12 errors logged, 8 global rules, last capture 3 days ago")
4. **🔴 Alerts** for any failures/overdue (brief)
5. **Recommendations** for any area <9
