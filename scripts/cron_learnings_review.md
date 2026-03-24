# Morning Learning Review — Cron Prompt

Daily learning review: surface due items, auto-reinforce, and scan for promotions.

## Steps

1. **Surface due learnings**: Run `python3 scripts/learning_review.py due 3` to get up to 3 due items.
   - If output is `LR_OK` → skip to step 3.
   - Otherwise, present the due items to the user as a quick reminder.

2. **Auto-reinforce**: Run `python3 scripts/learning_review.py reinforce-due 3` to advance presented items in the spaced repetition ladder.
   - This is critical — without reinforcement, items stay at L0 forever.

3. **Scan for new learnings**: Run `python3 scripts/learning_review.py scan` to pick up any newly captured items in `.learnings/`.

4. **Promotion check** (weekly, on Mondays only):
   - Read `.learnings/LEARNINGS.md`, `domains/*.md`, `projects/*.md`
   - Find patterns that appear 3+ times across files → recommend promoting to `LEARNINGS.md`
   - Flag entries older than 90 days with no recurrence → recommend archiving
   - Update `.learnings/REVIEW.md` with today's date and findings

## Output
- If items were surfaced: present them as concise reminders, then confirm reinforcement.
- If promotion candidates found: list them but do NOT auto-apply — present for user approval.
- If nothing actionable: reply HEARTBEAT_OK
