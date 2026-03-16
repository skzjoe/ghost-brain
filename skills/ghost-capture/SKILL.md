---
name: capture
description: "Quick-capture to the right second brain file — decisions, ideas, commitments, follow-ups, or people. Usage: /capture <type>: <content>"
user-invocable: true
---

# /capture

Universal quick-capture command. Routes content to the correct second brain file without relying on auto-detection triggers.

## Usage
```
/capture idea: build a CLI dashboard for metrics
/capture decision: use Prisma v6 over v7 — simpler connection handling
/capture commitment: deliver report to client by Friday
/capture followup: waiting on design team for mockups
/capture person: Sarah — PM at Acme Corp, met at kickoff meeting
```

## Instructions

1. Parse the user's message for `<type>: <content>` pattern. Supported types:
   - `idea` → `memory/ideas.md`
   - `decision` → `memory/decisions.md`
   - `commitment` → `memory/commitments.md`
   - `followup` / `follow-up` / `fu` → `memory/follow-ups.md`
   - `person` / `people` / `contact` → `memory/people.md`

2. If no type is specified or type is unrecognized, ask:
   > What kind of capture? → [Idea] [Decision] [Commitment] [Follow-up] [Person]
   (Use inline buttons)

3. Before appending, **dedup check**: scan existing entries in the target file for similar content. If a near-duplicate exists, warn and ask whether to skip or append anyway.

4. Format and append based on file type:

### Ideas → `memory/ideas.md`
Append under `## Active Ideas`:
```markdown
### {short title extracted from content}
- **Source:** {today} capture
- **Idea:** {content}
- **Status:** Parking
```

### Decisions → `memory/decisions.md`
Append as:
```markdown
[{today}] {content} (manual capture)
```

### Commitments → `memory/commitments.md`
Append row under `## Active`:
```markdown
| {today} | {to — extract if mentioned, else "TBD"} | {commitment text} | /capture |
```

### Follow-ups → `memory/follow-ups.md`
Append row under `## Active`:
```markdown
| {item text} | {owner — extract if mentioned, else "Me"} | {today} | — | Pending |
```

### People → `memory/people.md`
Append under the most appropriate section (Team/Clients/Personal), or create new entry:
```markdown
### {name}
- **Role/Context:** {extracted context}
- **Last mentioned:** {today}
```

5. Confirm what was captured and where:
   > ✅ Captured idea → `memory/ideas.md`: "{short title}"

6. If the daily note exists for today, also add a brief log entry:
   > - Captured {type}: {short summary}
