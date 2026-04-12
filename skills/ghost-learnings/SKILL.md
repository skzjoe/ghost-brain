---
name: learnings
description: "Show Ghost's learning-loop status, due learnings, and promotion state."
user-invocable: true
---

# /learnings

Show learning-loop status and what needs attention.

## Usage
```
/learnings
```

## Instructions

1. Run:
   ```bash
   python3 scripts/ghost_learning_loop.py status
   ```
2. Summarize:
   - total learnings
   - by state (observed, validated, promoted, archived)
   - due for review
   - last captured
   - pending skill candidates / skill improvements
3. If due_for_review > 0, explicitly call that out.
4. If skill candidates or improvements are pending, surface them as the main action.
5. Keep it short and operator-friendly.
