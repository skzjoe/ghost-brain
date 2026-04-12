# Auto Skill Pipeline

Immune-system approach to skill management. Ghost creates skills from experience, validates through real usage, self-improves on failure, and retires what doesn't work — all without human review.

## How It Works

```
Task completed → detect (skill-worthy?)
  → create (draft in skills/.auto/)
    → match (similar task later → use the skill)
      → record success/failure
        → 3 successes ≥90% → auto-promote ✅
        → <50% after 3 uses → auto-retire 💀
        → failure → improve (add context, revise)
```

### Key Insight

Unlike simple auto-skill-creation (create and forget), this pipeline **validates through real usage** and **kills what doesn't work**. Bad skills die automatically. Good skills earn their way to active status.

## Commands

```bash
# Check if a completed task should become a skill
python3 scripts/ghost_auto_skill.py detect '<task_log>'

# Create a skill from a successful task
python3 scripts/ghost_auto_skill.py create '<name>' '<procedure>' [description]

# Find a matching skill before starting a task
python3 scripts/ghost_auto_skill.py match '<task_description>'

# Record outcome after using a skill
python3 scripts/ghost_auto_skill.py record <skill_id> success
python3 scripts/ghost_auto_skill.py record <skill_id> failure

# Add failure context for self-improvement
python3 scripts/ghost_auto_skill.py improve <skill_id> '<what went wrong>'

# Manual overrides
python3 scripts/ghost_auto_skill.py promote <skill_id>
python3 scripts/ghost_auto_skill.py retire <skill_id>

# Dashboard and maintenance
python3 scripts/ghost_auto_skill.py status
python3 scripts/ghost_auto_skill.py list
python3 scripts/ghost_auto_skill.py cleanup
```

## Thresholds

| Threshold | Value | Effect |
|---|---|---|
| Auto-promote | 3+ successes, ≥90% rate | draft → active |
| Auto-retire | 3+ uses, <50% rate | any → retired |
| Match similarity | ≥30% keyword overlap | suggests matching skill |

## Integration

### In your agent playbook
After completing non-trivial multi-step tasks:
1. `detect '<task_summary>'` — check if skill-worthy
2. If worthy → `create '<name>' '<procedure>'`
3. Before starting any task → `match '<task_description>'`
4. If match found → follow the skill, then `record <id> success|failure`
5. On failure → `improve <id> '<what went wrong>'`

### Storage
- State: `.local/auto_skills.json`
- Skills: `skills/.auto/<name>/SKILL.md`
- Auto-created skills stay in `.auto/` even after promotion (status changes, path doesn't)

## Design Philosophy

**Immune system, not approval queue.** Skills are created, tested in the real world, and either survive or die based on performance. The human sees a dashboard, not a review queue.
