---
name: conflicts
description: "Scan decisions, commitments, and follow-ups for contradictions, overlaps, and inconsistencies."
user-invocable: true
---

# /conflicts

Detect contradictions and inconsistencies across second brain files.

## Instructions

1. **Read** all second brain files:
   - `memory/decisions.md`
   - `memory/commitments.md`
   - `memory/follow-ups.md`
   - `ACTIVE_WORK.md`
   - `MEMORY.md`

2. **Check for these conflict types:**

### Decision Contradictions
- Scan decisions for pairs where a later decision reverses or contradicts an earlier one
- Example: "[Mar 1] Use framework X" vs "[Mar 10] Avoid framework X"
- Flag with both dates and the contradiction

### Commitment Conflicts
- Overlapping deadlines (multiple commitments due same day)
- Commitments to projects marked dormant/completed in ACTIVE_WORK.md
- Commitments with no matching active workstream

### Follow-up Staleness
- Active follow-ups referencing completed/dormant projects
- Follow-ups with same owner and overlapping scope (duplicates)
- Follow-ups older than 30 days with no deadline (might be abandoned)

### Memory ↔ Active Work Drift
- Projects mentioned in MEMORY.md but not in ACTIVE_WORK.md (or vice versa)
- Status mismatches (MEMORY says "completed" but ACTIVE_WORK says "active")

### Orphaned Items
- People in people.md linked to projects that no longer exist
- Ideas referencing deprecated tools or completed work

3. **Output format:**

```
🔍 Conflict Scan — {date}

{if conflicts found:}
⚠️ Found {N} issue(s):

1. 🔴 CONTRADICTION: {description}
   - {date1}: {decision1}
   - {date2}: {decision2}
   → Suggestion: {which to keep/update}

2. 🟡 DRIFT: {description}
   → Suggestion: {fix}

3. 🟡 STALE: {description}
   → Suggestion: {archive or update}

{if no conflicts:}
✅ No conflicts detected. Brain is consistent.

━━━ Summary ━━━
- Decisions scanned: {count}
- Commitments checked: {count}
- Follow-ups checked: {count}
- Cross-references verified: {count}
```

4. For each conflict, suggest a specific fix (not just "review this").
