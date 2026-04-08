# Cron Patterns for OpenClaw

10 useful automation patterns. Adapt schedules/prompts to your needs.

## Daily

### 1. Morning Briefing (08:00)
Brief the user on today's priorities, calendar, unread emails, and blockers.
```
Schedule: cron 0 8 * * * @ Your/Timezone
Target: main (sends to user)
Prompt: Read yesterday's note + ACTIVE_WORK.md + calendar + email → compose morning briefing with top 3 priorities, blockers, and meeting prep.
```

### 2. EOD Session Log (23:00)
Consolidate the day's work into a structured daily note.
```
Schedule: cron 0 23 * * * @ Your/Timezone
Target: main
Prompt: Read today's daily note → fill gaps → capture decisions/people/ideas/commitments to second brain files → check ACTIVE_WORK.md for drift.
```

### 3. Obsidian Daily Sync (23:05)
Sync daily note to external note system (Obsidian, Notion, etc.)
```
Schedule: cron 5 23 * * * @ Your/Timezone
Prompt: Run push script for today's date. Silent on success.
```

### 4. Commitment Deadline Alert (08:30)
Check for commitments due today or overdue.
```
Schedule: cron 30 8 * * *
Prompt: Read commitments.md → alert if any due within 2 days or overdue. Silent if nothing due.
```

### 5. Morning Learning Review (08:15)
Surface due learnings from .learnings/ using interval-based recall.
```
Schedule: cron 15 8 * * * @ Your/Timezone
Prompt: Scan learnings → if items due, send brief review to user with key lessons and which area they apply to. Silent if nothing due.
```

## Weekly

### 6. Weekly Memory Distill (Sunday 21:00)
Compact memory, review second brain, generate weekly brief.
```
Schedule: cron 0 21 * * 0 @ Your/Timezone
Prompt: Read all daily notes this week → update MEMORY.md + ACTIVE_WORK.md → review learnings for promotion → review ideas/follow-ups/commitments → save weekly note → announce brief.
```

### 7. Weekly Backup (Sunday 20:00)
Back up critical workspace files.
```
Schedule: cron 0 20 * * 0
Prompt: Run backup script. Silent on success.
```

### 8. Weekly Report (Monday 08:30)
Generate a professional weekly summary.
```
Schedule: cron 30 8 * * 1
Prompt: Read week's daily notes + ACTIVE_WORK.md → compose report with progress, decisions, blockers, next priorities → save as file.
```

## Monthly

### 9. Monthly Note Archive (1st of month 06:00)
Archive daily notes older than 30 days.
```
Schedule: cron 0 6 1 * *
Prompt: Move daily notes older than 30 days to memory/archive/. Silent on success.
```

## Continuous

### 10. Gateway Healthcheck (every 6h)
Check gateway is alive and responsive.
```
Schedule: cron 0 */6 * * *
Prompt: Check gateway status + RPC probe. Alert only if down. Silent on success.
```

## Setup tips
- Use `openclaw cron create` to add each job
- Use `--target main` for jobs that should message the user
- Omit `--target` for silent/housekeeping jobs
- Use `--prompt-file` to load prompt from a file (easier to maintain)
- All prompts should end with "reply HEARTBEAT_OK if nothing to report" for silent jobs
- In automation, prefer fully-qualified messaging targets (`telegram:<chat_id>`, not bare ids) so announce delivery stays unambiguous across channels
- If a cron prompt runs Memory DB maintenance, prefer `bash scripts/run_memory_pipeline.sh ...` over raw `python3 scripts/ghost_memory_db.py ...`
