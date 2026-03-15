# Token Efficiency Rules

Practical patterns to reduce cost without losing quality.

## Context window management
- **Track context size.** OpenClaw shows it in `/status`. Under 50k = fine. Over 200k = consider `/summary` then `/new`.
- **Cache hit rate matters more than total tokens.** Stable workspace files (SOUL.md, AGENTS.md, etc.) get cached at ~1/10 cost after first message. Keep them stable — don't edit every session.
- **Workspace files are loaded every message.** Keep them lean. Move rarely-used reference to `memory/reference/` (read on demand, not auto-injected).

## Output discipline
- **Never dump raw logs.** Use `--limit`, `head -n`, `grep`, `tail` before showing output.
- **Prefer bullets over prose** for status/summaries. Prose only when analysis depth is needed.
- **Don't restate what the user already knows.** Lead with the answer, not the recap.
- **One-liner tasks = one-liner answers.** Don't pad with unnecessary context.

## Tool call efficiency
- **Batch independent calls.** If 3 commands have no dependencies, run all 3 in one block — don't serialize.
- **Don't narrate obvious tool calls.** Just call the tool. Narrate only for multi-step or risky operations.
- **Use grep/find before reading whole files.** Cheaper to search then read the relevant section.
- **Spawn sub-agents for parallel work.** Reading 5 files serially = 5 round trips. Sub-agent reads them all at once.

## Conversation patterns
- **Recommend `/summary` before `/new`** when context passes ~200k. Captures state, resets cheap.
- **Long conversations compound cost.** Each message re-sends entire history. More messages = exponentially more tokens.
- **Don't open-loop.** If the user says "ทำทั้งหมดเลย", batch the work — don't ask for confirmation between each step.
- **Store data as files, not chat.** Large tables, JSON, CSV → write to file and reference. Don't paste 500 lines into chat.

## Workspace file strategy
- **Auto-injected files** (SOUL.md, AGENTS.md, USER.md, etc.): keep total under 5-8KB combined. These are read every single message.
- **On-demand files** (memory/reference/, .learnings/): read only when relevant. No cost when not accessed.
- **Daily notes**: one per day, append-only during the day. Archive monthly.
- **MEMORY.md**: compact regularly. It's in every message — every extra line costs tokens forever.

## Rate limiting & API discipline
- **5s minimum between API calls** — prevents 429s and provider throttling
- **10s minimum between search calls** — search APIs (web, ClawHub, etc.) are stricter
- **Max 5 calls per batch, then 2min cooldown** — don't fire 20 API calls in a loop
- **Respect 429/Retry-After headers** — if rate-limited, wait the specified time, don't retry immediately
- **Serialize bursts** — if you need to do 10 writes, space them out instead of parallel-blasting
- **Prefer fewer, larger writes** — one API call with 10 items beats 10 calls with 1 item each
- **Log rate limit errors** — capture in `.learnings/ERRORS.md` so the agent remembers which APIs are sensitive

Why this matters for tokens: rate limit errors trigger retries → retries burn extra tokens on error messages + re-processing → a 429 loop can easily 3-5x the token cost of the original task.

## Anti-patterns (avoid these)
- ❌ Putting full API docs in workspace files (use memory/reference/ instead)
- ❌ Huge MEMORY.md with historical details (keep lean, archive old)
- ❌ Asking "are you sure?" after every step (burns a round trip)
- ❌ Dumping `cat` of entire files when you need 3 lines
- ❌ Multiple small messages when one message would do
- ❌ Recreating context that's already in workspace files
- ❌ Firing API calls in a tight loop without delays
- ❌ Retrying 429 errors immediately without backoff
- ❌ Making 10 small API writes when 1 bulk write works
