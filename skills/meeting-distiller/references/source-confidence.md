# Source Confidence

Use this reference when meeting inputs come from mixed-quality sources.

## Trust order

Default ranking:
1. Raw transcript text
2. Screenshot that clearly shows transcript or native note content
3. Human notes taken during/after meeting
4. AI-generated meeting summary

## Rules

- If transcript and AI summary conflict, prefer transcript.
- If screenshot confirms a UI tab or visible content, trust the screenshot for that visible portion only.
- If the transcript is partial, avoid treating silence as disproof.
- If an AI summary adds sections like Decisions, Action Items, or Open Questions, verify whether those were explicitly said or inferred.

## Confidence categories

### Confirmed
Use when directly visible in transcript or source text.

Examples:
- “Need the email to create user”
- “Flow is open link → edit → save → refresh”

### Inferred
Use when strongly implied but not said as a formal decision.

Examples:
- “They likely plan a short follow-up after access is granted”
- “This session appears to be a quick walkthrough, not full training”

### Unclear
Use when the source is incomplete or contradictory.

Examples:
- exact owner unknown
- deadline guessed by AI summary only
- speaker identity not mapped

## Good phrasing

- “Confirmed from transcript:”
- “Likely, but not explicitly stated:”
- “AI summary suggests this, but transcript support is weak:”
- “Unclear from current source:”

## Bad behavior to avoid

- Converting weak AI guesses into firm decisions
- Assigning owners without evidence
- Turning approximate timing into exact deadlines without noting inference
- Mapping anonymous speakers to real people without explicit source support
