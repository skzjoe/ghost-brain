# HEARTBEAT.md

Goal: catch urgent signals between cron runs. Bash-first, 0 tokens when nothing needs attention.

## How it works
1. Run `scripts/heartbeat_pulse.sh` — pure bash/python, no LLM needed.
2. If output = `HEARTBEAT_OK` → reply HEARTBEAT_OK (silent, 0 tokens).
3. If output contains alerts → forward to user.

## Token cost
- Nothing urgent: **0 tokens** (bash exits with HEARTBEAT_OK)
- Alert without meeting: **~500 tokens** (forward alert text)
- Meeting prep: **~2,000 tokens** (invoke LLM for talking points)

## Rules
- Never spam with routine OK messages.
- Dedup follow-up nudges via `memory/heartbeat-state.json` (3-day cooldown).
- If heartbeat_pulse.sh is missing or errors → reply HEARTBEAT_OK (fail silent).
