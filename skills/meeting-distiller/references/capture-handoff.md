# Capture Handoff

Use when a meeting result should be turned into memory artifacts.

## Capture targets

### decisions.md
Capture when the meeting contains a real decision, for example:
- chosen workflow
- approved approach
- accepted scope interpretation
- agreed operating rule

### commitments.md
Capture when someone promises:
- a deliverable
- a deadline
- a follow-up date
- access/account creation

### follow-ups.md
Capture when the result depends on someone else sending or confirming something.

### daily note
Capture a short log when the meeting matters operationally even if no major decision was made.

### people.md
Update when new contacts appear or existing contacts gain new context.

## Safety rule

Do not promote weak inferences into durable memory. Only capture what is explicit or clearly agreed.
Use repaired names/terms (from transcript repair step) in captures, not the raw ASR output.

## Chain: meeting-distiller → docs-toolkit → daily note → Obsidian

When a meeting distillation should become a durable artifact:

1. **Distill first** using meeting-distiller (this skill).
2. **Create artifact** — save the full distillation to `projects/docs-toolkit/outputs/YYYY-MM-DD_meeting_<topic>.md`.
3. **Daily note** — append a short summary block to `memory/YYYY-MM-DD.md` with:
   - meeting topic
   - decisions
   - action items
   - artifact path
4. **Memory capture** — append to `memory/decisions.md`, `memory/commitments.md`, `memory/follow-ups.md`, `memory/people.md` as appropriate.
5. **Obsidian push** — mirror the artifact to `<vault>/20_Artifacts/docs-toolkit/outputs/` and push the daily note via `scripts/obsidian_push_daily.sh`.

### When to auto-chain

- If the meeting produced decisions or commitments → always capture.
- If the user says "จดไว้" / "save" / "log" → full chain.
- If the user only asks for a quick summary → do not auto-chain unless the content is clearly important.
- When in doubt, suggest capture rather than silently doing or silently skipping.

### Short form (no artifact needed)

If the meeting is minor, skip the docs-toolkit artifact and just:
1. Append a short log to daily note.
2. Capture any commitments/follow-ups.

## Suggested daily note structure

- meeting/topic
- short outcome
- decisions
- action items
- blockers/missing inputs
- artifact link if created
