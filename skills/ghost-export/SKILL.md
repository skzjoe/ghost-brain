---
name: export
description: "Export your brain state as a portable markdown bundle (zip) for backup, sharing, or migration."
user-invocable: true
---

# /export

Bundle the current brain state into a portable format.

## Usage
```
/export              — full brain export (zip)
/export weekly       — just this week's notes + decisions
/export project X    — just project X's memory + learnings
```

## Instructions

### Full Export
1. Collect these files into a flat structure:
   - `MEMORY.md`
   - `ACTIVE_WORK.md`
   - `USER.md`
   - `GHOST_PLAYBOOK.md` (or `PLAYBOOK.md`)
   - `memory/decisions.md`
   - `memory/people.md`
   - `memory/ideas.md`
   - `memory/commitments.md`
   - `memory/follow-ups.md`
   - `memory/projects/*.md`
   - Last 7 daily notes (`memory/YYYY-MM-DD.md`)
   - `.learnings/LEARNINGS.md`
   - `.learnings/ERRORS.md`
   - `.learnings/domains/*.md`
   - `.learnings/projects/*.md`

2. Create a `MANIFEST.md` at the root of the export:
```markdown
# Ghost Brain Export
- **Exported:** {timestamp}
- **User:** {from USER.md name}
- **Files:** {count}
- **Daily notes:** {date range}
- **Decisions:** {count}
- **Active follow-ups:** {count}
- **Active commitments:** {count}
- **Active ideas:** {count}
```

3. Bundle into `media/out/ghost-brain-export-{YYYY-MM-DD}.zip`

4. Report file size and location.

### Weekly Export
- Only include: last 7 daily notes + decisions from this week + active follow-ups/commitments
- Bundle into `media/out/ghost-brain-weekly-{YYYY-MM-DD}.zip`

### Project Export
- Include: `memory/projects/{name}.md` + `.learnings/projects/{name}.md` + any daily notes mentioning the project name
- Bundle into `media/out/ghost-brain-project-{name}-{YYYY-MM-DD}.zip`

## Privacy
- **Never include** `secrets/` directory content
- **Never include** `~/.openclaw/openclaw.json` (contains tokens)
- Warn if any file contains email addresses or API keys before zipping
- Strip any lines matching `ghp_`, `sk-`, `Bearer `, or common token patterns
