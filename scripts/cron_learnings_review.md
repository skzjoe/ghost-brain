# Monthly Learnings Review — Cron Prompt

Scan `.learnings/` for promotion candidates and stale entries.

## Steps
1. Read `.learnings/LEARNINGS.md` (global)
2. Read all files in `.learnings/domains/` and `.learnings/projects/`
3. Read `.learnings/ERRORS.md` and `.learnings/FEATURE_REQUESTS.md`

## Analysis
- **Promotion candidates**: Find patterns that appear 3+ times across domain/project files → recommend promoting to `LEARNINGS.md` (global)
- **Stale entries**: Flag learnings older than 90 days with no recent recurrence → recommend archiving to `.learnings/archive/`
- **Cross-pollination**: If a project-scoped learning applies broadly → recommend copying to the relevant domain file

## Output
- Compose a summary:
  - Promotion candidates (what + where → where)
  - Stale entries to archive
  - Cross-pollination suggestions
- Update `.learnings/REVIEW.md` with today's date and findings
- If nothing actionable, reply HEARTBEAT_OK
- If changes are recommended, list them but do NOT auto-apply — present for {{USER_NAME}}'s approval in the next session
