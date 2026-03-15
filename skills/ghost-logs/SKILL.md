---
name: logs
description: "Summarize current session's work and capture it to daily note + second brain files. Must be done before /new."
user-invocable: true
---

# /logs

Summarize the current session and capture everything to the second brain.

## Instructions

### 1. Summarize session → daily note
Create or append to `memory/YYYY-MM-DD.md` (today's date). Use this structure:

```markdown
### Session N (HH:MM–HH:MM, model)
**Theme: {1-line summary}**

- {key activities, in order}
```

Under the session log, update these sections (create if missing):

```markdown
## ✅ Done
- [x] {completed items from this session}

## 🧾 Decisions
- {decisions made, with reasoning}

## 📌 Next Actions
- {what's next}

## 📎 Artifacts
- {files created/modified with paths}
```

If sections already exist from earlier sessions today, **append** — don't overwrite.

### 2. Capture to second brain files
Scan the session for each of these and append if found:

| Signal | Target file | What to capture |
|---|---|---|
| Significant decision made | `memory/decisions.md` | `[YYYY-MM-DD] Decision — Reasoning (source)` |
| Person mentioned in work context | `memory/people.md` | Name, role, org, context, last mentioned date |
| Future idea ("someday", "might want to", "น่าจะ", "ลองดู") | `memory/ideas.md` | Idea + context |
| Promise to client/stakeholder | `memory/commitments.md` | Date, to whom, what was promised, context |
| Correction/error/user feedback | `.learnings/ERRORS.md` or appropriate domain/project file | Error entry with fix + prevention |

Before appending decisions, quick-scan existing entries for contradictions — if found, flag it.

### 3. Push to Obsidian
Run: `bash scripts/obsidian_push_daily.sh YYYY-MM-DD`

If the script doesn't exist, note it but don't fail — the daily note is still saved locally.

### 4. Confirm
Reply with a brief summary of what was logged:
- 📝 Daily note status
- 🧾 Decisions captured (count)
- 👥 People updated (count)
- 💡 Ideas captured (count)
- 🤝 Commitments captured (count)
- ❌ Errors/learnings logged (count)
- 📓 Obsidian push status

## Rules
- Must be done before `/new` — remind user if they try `/new` without `/logs`
- Don't duplicate entries already in today's note from earlier sessions
- Keep session summaries concise — activities, not conversation replay
- If nothing was captured for a category, skip it in the confirmation (don't list "0")
