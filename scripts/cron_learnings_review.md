# Morning Learning Review — Cron Prompt

Run after the morning briefing. Surface a few due learnings from `.learnings/` using interval-based recall.

## Steps
1. Run:
   - `python3 scripts/learning_review.py scan`
   - `python3 scripts/learning_review.py due 3`
2. If output is `LR_OK` → reply `LR_OK` and stay silent.
3. If items are due:
   - Read each surfaced learning's full entry from the source file.
   - Compose a brief message titled `🔄 Learning Review` with, for each item:
     - the key lesson in 1-2 sentences
     - which area it applies to
     - the learning ID
4. Do **not** call `message.send` directly from the prompt. Return the text normally so cron delivery/announce can send it.
5. Do **not** auto-reinforce. Wait for the user's later response before reinforcing anything.
6. After surfacing items, run `python3 scripts/learning_review.py dismiss <ID>` for each surfaced item so it does not repeat tomorrow unchanged.

## Output rules
- No items due → `LR_OK`
- Items due → concise review message only
