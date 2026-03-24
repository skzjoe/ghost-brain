---
name: self-improvement
description: "Captures learnings, errors, and corrections to enable continuous improvement. Use when: (1) A command or operation fails unexpectedly, (2) User corrects Claude ('No, that's wrong...', 'Actually...'), (3) User requests a capability that doesn't exist, (4) An external API or tool fails, (5) Claude realizes its knowledge is outdated or incorrect, (6) A better approach is discovered for a recurring task. Also review learnings before major tasks."
metadata:
---

# Self-Improvement Skill

Log learnings and errors for continuous improvement. Promote recurring patterns into durable workspace guidance.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` (category: `correction`) |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` (category: `knowledge_gap`) |
| Found better approach | Log to `.learnings/LEARNINGS.md` (category: `best_practice`) |
| Broadly applicable | Promote to `AGENTS.md`, `TOOLS.md`, or `SOUL.md` |

## Workspace Structure

```
.learnings/
├── LEARNINGS.md          # Corrections, knowledge gaps, best practices
├── ERRORS.md             # Command failures, exceptions
├── FEATURE_REQUESTS.md   # User-requested capabilities
├── REVIEW.md             # Promotion/archive review state
├── domains/*.md          # Lessons scoped to work type
├── projects/*.md         # Lessons scoped to one project
└── archive/*.md          # Inactive/superseded learnings
```

## Logging Format

### Learning Entry → `.learnings/LEARNINGS.md`

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601  **Priority**: low|medium|high|critical  **Status**: pending
**Area**: frontend|backend|infra|tests|docs|config

### Summary
One-line description

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-XXXXXXXX-XXX
- Pattern-Key: (optional, for recurring-pattern tracking)
---
```

### Error Entry → `.learnings/ERRORS.md`

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601  **Priority**: high  **Status**: pending

### Summary
Brief description of what failed

### Error
Actual error message

### Context
Command attempted, parameters, environment

### Suggested Fix
What might resolve this

### Metadata
- Reproducible: yes|no|unknown
- Related Files: path/to/file.ext
---
```

### Feature Request → `.learnings/FEATURE_REQUESTS.md`

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601  **Priority**: medium  **Status**: pending

### Requested Capability
What the user wanted

### Complexity Estimate
simple|medium|complex

### Suggested Implementation
How this could be built
---
```

## ID Format
`TYPE-YYYYMMDD-XXX` (e.g., `LRN-20250115-001`, `ERR-20250115-A3F`)

## Resolving & Promoting

Update status: `pending` → `resolved` | `promoted` | `wont_fix`

### Promotion Rule
Promote to workspace files when:
- Recurrence ≥ 3 across ≥ 2 distinct tasks within 30 days

| Learning Type | Promote To |
|---|---|
| Behavioral patterns | `SOUL.md` |
| Workflow improvements | `AGENTS.md` |
| Tool gotchas | `TOOLS.md` |

Write promoted rules as short prevention rules, not incident write-ups.

## Scoping Rules
- Facts, decisions, session continuity → `MEMORY.md` / `memory/YYYY-MM-DD.md`
- Performance lessons, corrections, workflow improvements → `.learnings/`
- Default to smallest scope: project → domain → global
- Archive stale lessons instead of deleting

## Detection Triggers

**Corrections**: "No, that's not right...", "Actually...", "You're wrong...", "That's outdated..."
**Feature Requests**: "Can you also...", "I wish you could...", "Is there a way to..."
**Errors**: Non-zero exit code, exception, unexpected output, timeout

## Periodic Review

Review at natural breakpoints (before major tasks, after features, weekly).
```bash
grep -h "Status\*\*: pending" .learnings/*.md | wc -l
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["
```

For detailed setup (hooks, multi-agent, skill extraction): see `references/`.

## Post-Capture: Sync with Learning Review

After writing any new entry to `.learnings/`, run:
```bash
python3 scripts/learning_review.py scan
```
This registers the new item in the spaced repetition tracker so it will be surfaced in Morning Learning Review cron. Without this, new learnings won't appear in the SR system until the next daily scan.
