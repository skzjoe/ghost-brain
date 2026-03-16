---
name: fastlanes
description: "Show and manage fast lane templates — domain-specific response structures that improve answer quality."
user-invocable: true
---

# /fastlanes

Show available fast lanes or suggest new ones based on your work patterns.

## Instructions

### /fastlanes (no args)
Show all configured fast lanes from `GHOST_PLAYBOOK.md` (look for the `## Fast Lanes` section).

Format as a compact table:
```
⚡ Active Fast Lanes

| Domain | Structure | Trigger |
|---|---|---|
| Coding | Cause → Fix → Test → Rollback | Code questions, bugs, errors |
| Docs | Draft → Gaps → Critique → Next | Writing, specs, documentation |
| ... | ... | ... |

💡 To add a custom lane, say: /fastlanes add <domain>
```

### /fastlanes add <domain>
1. Ask: "What kind of work is this for? Describe a typical request in this domain."
2. Based on the description, generate a fast lane entry:
   ```markdown
   ### {Domain}
   {Step 1} → {Step 2} → {Step 3} → {Step 4} → {Step 5}
   - {1-2 lines of behavioral guidance}
   ```
3. Append to the `## Fast Lanes` section of `GHOST_PLAYBOOK.md`
4. Confirm: "Added {domain} fast lane. I'll use this structure automatically for matching requests."

### /fastlanes remove <domain>
1. Remove the matching fast lane section from `GHOST_PLAYBOOK.md`
2. Confirm removal

## Starter Fast Lanes (for product)
These ship with Ghost Brain as defaults in `PLAYBOOK.md`:

```markdown
### Coding / Debug
Most likely cause → Fastest verification → Fix path → Risk/rollback → Next diagnostic if still failing
- Lead with highest-probability cause. Distinguish likely / possible / unlikely.

### Docs / Specs
Deliverable draft → Gaps/ambiguities → Critique from reviewer POV → Next edits/approval
- Prefer reusable artifact. Turn rough notes into structured docs.

### Ops / Infrastructure
Current state → Issue/risk → Fix → Expected result → Rollback/caveat
- Prefer automated/scripted fixes. Call out what could break.

### Decision Support
Recommendation → Why this wins → Tradeoffs/hidden costs → What to defer → Decision-triggering next step
- Don't stay neutral when one option is better.

### Planning / Strategy
Recommendation → Why now → Impact → Risks/dependencies → 30-60-90 next moves
- Optimize for leverage and sequencing. Fewer high-impact moves over long task lists.

### Communication / Email
What matters now → What can wait → Draft reply → Risks/commitments → Follow-up trigger
- Prefer draft-ready replies. Call out unclear purpose or scheduling conflicts.
```
