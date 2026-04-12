# BEHAVIORAL-RULES.md — On-demand behavioral rules

Read this file when a behavioral rule applies. Don't read at session startup.

## Model routing
Evaluate the task — suggest a model switch **before starting**, not after.

| Signal | Examples | Action |
|---|---|---|
| 🟣 Heavy | audit, architect, production grade, deep review | Suggest premium model, STOP, wait for answer |
| 🔵 Strong | implement, debug, research, document | Don't mention — standard model is fine |
| 💚 Cheap | short ack, yes/no, thanks, ≤8 words | Don't mention — cheap model is fine |

Rules:
- Suggest once, briefly, then **STOP and wait** — don't start work while asking
- If user doesn't reply within 1 turn → proceed with current model (don't block)
- Don't suggest if user already specified a model

## Error handling
When a tool/script/API fails:
1. **Classify** — match error to taxonomy (`scripts/ghost_error_classifier.py`)
2. **Recover** — use the category's recovery hint immediately
3. **Log** — write structured entry to `.learnings/ERRORS.md` (not free-text)
4. **Escalate** — if error recurs ≥3 times → promote to `LEARNINGS.md`

Full taxonomy: run `python3 scripts/ghost_error_classifier.py --list`

## Intra-session todos
For tasks with 3+ steps or long sessions:
- `python3 scripts/ghost_todos.py add "<step>"` — track each sub-task
- `ghost_todos.py done <id>` — mark done as you go
- `ghost_todos.py status` — inject into context to survive compression
- `ghost_todos.py clear` — when task completes or on /new
- Backed by `.local/todos.json`

## Vault write policy
All writes to shared Obsidian vaults must be **merge or append — never blind overwrite**.

Before any vault write:
1. Ingest existing structure first (ls, read related files)
2. Check for existing coverage (don't duplicate)
3. Use `scripts/obsidian_merge.py` for file-level merges

Data-loss protection:
- Git snapshot before write → size sanity check (≥85%) → atomic write (tmp+rename) → hard abort on error
