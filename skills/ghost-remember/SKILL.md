---
name: remember
description: "Capture a note into the right Ghost memory layer automatically. Usage: /remember <content>"
user-invocable: true
---

# /remember

Capture content into the right Ghost memory file automatically.

## Usage
```
/remember We decided to pause Project Beacon until after Project Atlas ships
/remember Follow up with Jane on hosting migration by Friday
/remember Learned: do not treat OpenClaw cron as system crontab
```

## Instructions

1. Parse the remainder of the message as the capture content.
2. If empty, ask: `อยากให้จำเรื่องอะไรครับ?`
3. Run:
   ```bash
   python3 scripts/ghost_unified_recall.py capture '<content>'
   ```
4. Read the output and confirm:
   - detected type
   - destination file
   - short captured summary
5. If the script warns about a duplicate, do not write again blindly. Tell the user it looks similar to an existing item and ask whether to keep or skip.
6. For learning-like content, mention that it was routed into the learning system.
