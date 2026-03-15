# Self-Learning System

How to make your agent learn from mistakes and get better over time.

## Concept
Two separate memory systems:
1. **Factual memory** (`MEMORY.md`, `memory/*.md`) — what happened, decisions, context
2. **Execution memory** (`.learnings/`) — how to do things better

Most agents only have #1. Adding #2 means the agent stops repeating the same mistakes.

## Structure
```
.learnings/
├── LEARNINGS.md          # Global rules (promoted after 3+ occurrences)
├── ERRORS.md             # Tool/command failures with fixes
├── FEATURE_REQUESTS.md   # Capabilities the user asked for that don't exist
├── domains/              # Lessons by work type
│   ├── coding.md
│   ├── ops.md
│   └── docs.md
├── projects/             # Lessons by specific project
│   └── my-project.md
└── archive/              # Retired/superseded learnings
```

## When to log

| Trigger | Where | Example |
|---|---|---|
| Command/tool fails | `ERRORS.md` | "ERPNext rejects duplicate rows in Stock Reconciliation" |
| User corrects agent | Domain or project file | "Actually, use `included_in_print_rate=1` for tax-inclusive" |
| Better approach found | Domain file | "Batch independent API calls instead of serializing" |
| User asks for missing capability | `FEATURE_REQUESTS.md` | "Wants auto-generated PDF reports" |
| Pattern repeats 3+ times | Promote to `LEARNINGS.md` | "Always check cron list, not just crontab" |
| Lesson inactive 60+ days | Move to `archive/` | Old workaround no longer relevant |

## Entry format
```markdown
## [LRN-YYYYMMDD-NNN] short_label

**Status**: active | pending | archived
**Area**: what domain/feature

### Summary
One-line rule.

### Details
Context and reasoning (2-5 lines).

### Suggested Action
What to do differently next time.
```

## Lifecycle
1. **Log** — agent captures learning at the smallest valid scope (project → domain → global)
2. **Review** — monthly scan for promotion candidates (3+ repetitions → promote to global)
3. **Archive** — 60+ day inactive learnings move to `archive/`
4. **Pre-check** — before major tasks, agent reads relevant `.learnings/` files

## How to activate
Add to your `AGENTS.md` or system prompt:
```
After non-trivial work, do a brief self-reflection:
- Did anything fail unexpectedly? → log to .learnings/ERRORS.md
- Did the user correct me? → log to appropriate .learnings/ file
- Did I discover a better approach? → log to .learnings/domains/
- Is there a reusable lesson? → log at smallest valid scope
```

## Drop-in skill
Copy `skills/self-improving-agent/` to your workspace skills folder.
It auto-triggers on errors, corrections, and discoveries.

## Tips
- Keep entries short and actionable — rules, not essays
- Default to smallest scope: project → domain → global
- Promote only after real repetition, not speculation
- Archive is better than delete — you might need it later
- Review monthly, not daily — let patterns emerge naturally
