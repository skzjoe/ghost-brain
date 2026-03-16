# Spaced Repetition — Resurface Learnings Automatically

A lightweight spaced repetition system that ensures learnings from `.learnings/` actually get used, not just stored.

## Why

Without resurfacing, your learnings file becomes a graveyard — you log mistakes and corrections but never revisit them. Spaced repetition ensures:
- **Critical rules** surface frequently until they're second nature
- **Domain lessons** come back at increasing intervals as you prove recall
- **Graduated items** stop surfacing — no noise from mastered knowledge

## How it works

1. **Scan** — Parses all `[LRN-*]` and `[ERR-*]` blocks from `.learnings/`
2. **Schedule** — Each item gets an interval level (1 → 3 → 7 → 14 → 30 → 60 → 120 days)
3. **Surface** — Cron shows due items each morning
4. **Reinforce** — When you apply a learning, it advances to the next interval
5. **Graduate** — After passing all levels, the item stops surfacing

Priority weights adjust frequency:
- `critical` → intervals × 0.5 (surfaces twice as often)
- `high` → intervals × 0.75
- `medium` → intervals × 1.0
- `low` → intervals × 1.5

## Setup

No dependencies. Pure Python + JSON state file.

```bash
# Initialize — scan learnings and create state
python3 scripts/sr_review.py init

# See what's due today
python3 scripts/sr_review.py due

# Mark a learning as applied
python3 scripts/sr_review.py reinforce LRN-20260315-002

# Skip this cycle (same level, push next review date)
python3 scripts/sr_review.py dismiss ERR-20260315-001

# View stats
python3 scripts/sr_review.py stats

# Re-scan (picks up new learnings, removes deleted ones)
python3 scripts/sr_review.py scan
```

## Cron integration

Add a cron job that runs after your morning summary:

```
Schedule: 15 minutes after morning summary
Message:
  Run: python3 scripts/sr_review.py scan && python3 scripts/sr_review.py due 3
  If output is SR_OK → nothing due, stay silent.
  If learnings are due → send a brief review message to the user.
```

## State file

Stored at `.learnings/sr-state.json`:
```json
{
  "items": {
    "LRN-20260315-002": {
      "level": 2,
      "next_review": "2026-03-23",
      "last_reviewed": "2026-03-16",
      "times_surfaced": 3,
      "times_reinforced": 2,
      "graduated": false
    }
  }
}
```

## Tips

- **Stagger initial items** — if you have many learnings, spread `next_review` dates across a week so you don't get overwhelmed on day 1
- **3 per day** is a good default — enough to be useful, not enough to be annoying
- **Reinforce > Dismiss** — reinforcing advances the interval; dismissing keeps you at the same level
- **Graduated items are done** — once an item passes all 7 levels, it's considered mastered
