---
name: recall
description: "Search Ghost's unified memory across memory files, learnings, and indexed recall sources. Usage: /recall <query>"
user-invocable: true
---

# /recall

Search across Ghost's unified memory layer.

## Usage
```
/recall OpenClaw cron
/recall Piyapodok deadline
/recall Omix MCC naming correction
```

## Instructions

1. Parse the remainder of the message as the query.
2. If no query is provided, ask: `อยาก recall เรื่องอะไรครับ?`
3. Run:
   ```bash
   python3 scripts/ghost_unified_recall.py summary '<query>'
   ```
4. Return the summary as-is, but keep it concise if the result is long.
5. If there are no hits, say that nothing confident was found and suggest a narrower query.
6. If the query is about a person/preference/past decision and the summary seems weak, say you checked unified memory but confidence is low.
