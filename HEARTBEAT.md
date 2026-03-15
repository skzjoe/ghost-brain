# HEARTBEAT.md

Goal: catch urgent signals between cron runs. Bash-first, 0 tokens when nothing needs attention.

## How it works
1. Run `scripts/heartbeat_pulse.sh` — pure bash/python, no LLM needed.
2. If output = `HEARTBEAT_OK` → reply HEARTBEAT_OK (silent, 0 tokens).
3. If output contains alerts → forward to Joe. If `NEEDS_MEETING_PREP` is in any alert, pull context from ACTIVE_WORK.md + recent daily notes and prepare 3-5 bullet talking points.

## Checks (all bash, 0 tokens unless alert)
1. **Meeting in 2h** — gog calendar → if found, signal NEEDS_MEETING_PREP
2. **Commitment due ≤2 days** — grep dates in commitments.md
3. **Stale follow-ups >7 days** — grep dates in follow-ups.md (3-day cooldown between nudges)
4. **Weather** — only 7-9am & 4-6pm, only if rain/storm
5. **Unread emails** — gog gmail search with configured query

## Token cost
- Nothing urgent: **0 tokens** (bash exits with HEARTBEAT_OK)
- Alert without meeting: **~500 tokens** (forward alert text)
- Meeting prep: **~2,000 tokens** (invoke LLM for talking points)
- Typical day: **0-2,000 tokens** vs old design ~48,000/day

## Rules
- Never spam Joe with routine OK messages.
- Dedup follow-up nudges via `memory/heartbeat-state.json` (3-day cooldown).
- If heartbeat_pulse.sh is missing or errors → reply HEARTBEAT_OK (fail silent).
