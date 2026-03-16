---
name: project
description: "Initialize or load project memory. Usage: /project init <name> or /project <name>"
user-invocable: true
---

# /project

Manage project-specific memory files.

## Usage
```
/project init myapp        — scaffold a new project memory file
/project myapp             — load and show project context
/project list              — list all project memory files
```

## Instructions

### /project init <name>
1. Check if `memory/projects/<name>.md` already exists. If yes, show it instead of overwriting.
2. Create `memory/projects/<name>.md`:

```markdown
# {Name} — Project Memory

## Overview
- **Started:** {today}
- **Status:** Active
- **Stack/tools:** TBD
- **Repo:** TBD

## Key Decisions
<!-- Major technical and business decisions for this project -->

## People
<!-- Key contacts, stakeholders, team members -->

## Lessons Learned
<!-- What worked, what didn't, patterns to remember -->

## Links & References
<!-- Important URLs, docs, resources -->

## Notes
<!-- Running notes, context that doesn't fit elsewhere -->
```

3. Also create `.learnings/projects/<name>.md` if it doesn't exist:
```markdown
# {Name} — Project Learnings

<!-- Execution-quality lessons specific to this project.
     Move reusable patterns to domain or global learnings. -->
```

4. Check if the project is in `ACTIVE_WORK.md`. If not, ask:
   > This project isn't in ACTIVE_WORK.md yet. Add it? [Yes] [No]

5. Confirm: "Project memory initialized for {name}. I'll auto-load this context whenever you mention {name}."

### /project <name> (no init)
1. Read and display `memory/projects/<name>.md`
2. Also load `.learnings/projects/<name>.md` silently for context
3. Show a brief summary of the project state

### /project list
1. List all files in `memory/projects/` with their first-line title and last-modified date
2. Cross-reference with `ACTIVE_WORK.md` to show which are active vs untracked
