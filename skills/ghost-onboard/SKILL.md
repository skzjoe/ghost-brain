---
name: onboard
description: "First-run guided setup — ask a few questions, then populate MEMORY.md, ACTIVE_WORK.md, USER.md, and the first daily note."
user-invocable: true
---

# /onboard

Guided first-run setup for Ghost Brain. Makes the empty workspace usable in 2 minutes.

## Instructions

1. Check if `MEMORY.md` already has real content (not just template headers). If yes, warn: "It looks like you already have a brain set up. Running /onboard will overwrite your current files. Continue?" Wait for confirmation.

2. Ask the user these questions (use inline buttons where possible):
   - **Name**: "What should I call you?"
   - **Role**: "What's your role? (e.g., CTO, developer, freelancer, PM)"
   - **Company/org** (optional): "Company or org name?"
   - **Timezone**: "Your timezone? (e.g., Asia/Bangkok, US/Eastern, Europe/Berlin)"
   - **Work domains**: "What kind of work do you do? Pick all that apply:" → coding, docs/writing, ops/infra, project management, business/sales, design, other
   - **Active projects** (optional): "List 1-3 current projects (comma-separated, or skip)"

3. Generate and write these files:

### USER.md
```markdown
# USER.md - About You

- **Name:** {name}
- **Role:** {role} @ {company or "Independent"}
- **Timezone:** {timezone}
- **Preferences:** concise, accurate, direct
```

### MEMORY.md
```markdown
# MEMORY.md - Long-Term Context

## Operating Rules
- **Second Brain**: Ghost acts as your second brain — captures decisions, people, ideas, commitments, and follow-ups automatically.
- **Playbook**: follow `GHOST_PLAYBOOK.md` for response patterns and fast lanes.
- **Active work**: check `ACTIVE_WORK.md` before asking you to restate priorities.

## Work Context
- **Role**: {role} @ {company}
- **Domains**: {work domains}

## Second Brain files
- `memory/decisions.md` — decision journal with reasoning
- `memory/people.md` — lightweight CRM for key contacts
- `memory/ideas.md` — idea parking lot
- `memory/commitments.md` — promises/timelines to clients/stakeholders
- `memory/follow-ups.md` — items waiting on someone

_Last updated: {today}_
```

### ACTIVE_WORK.md
If projects were provided, create entries for each:
```markdown
# ACTIVE_WORK.md — Active Work Register

## Current Workstreams

### 1) {project name}
- **Status:** Active
- **Focus:** TBD
- **Next:** Define scope and first deliverable

## Dormant / On-hold Projects

## If Idle, Pull Next
- Review and flesh out active project details
- Set up cron jobs with `setup-crons.sh`
```

### First daily note: `memory/{today}.md`
```markdown
# {today}

## 🧠 Log
- Ghost Brain set up via /onboard
- Work domains: {domains}
- Active projects: {projects or "none yet"}

## ✅ Done
- [x] Initial Ghost Brain setup

## 📌 Next Actions
- Flesh out ACTIVE_WORK.md with real project details
- Run `setup-crons.sh` to enable automated routines
- Start working — Ghost will auto-capture decisions, ideas, and people as you go
```

4. After writing all files, summarize what was created and suggest next steps:
   - "Try asking me something about your work — I'll use the right fast lane automatically"
   - "Say `/capture idea: ...` to save an idea"
   - "At end of day, say `/logs` to capture your session"
