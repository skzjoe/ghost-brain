---
name: meeting-distiller
description: "Distill meeting transcripts, PLAUD notes, screenshots, or AI summaries into trusted summaries with decisions, action items, and open questions. Repairs Thai ASR errors (garbled names, terms, fillers) before summarizing. Separates confirmed facts from AI inferences. Use when the user shares any meeting material and wants a practical recap, action extraction, team update, or client-safe summary."
---

# Meeting Distiller

Turn noisy meeting material into operational summaries the user can trust and reuse.

## Core operating rules

- Optimize for **decision utility**, not pretty prose.
- Prefer **transcript truth** over AI-generated summaries.
- **Repair before distill**: normalize Thai ASR errors before summarizing.
- Separate **Confirmed**, **Inferred**, and **Unclear** whenever source quality matters.
- Do not pretend speaker labels (`Speaker 1/2/3`) map to real people unless the source explicitly says so.
- Treat AI meeting summaries as **helpful but non-authoritative** unless corroborated by transcript.
- Pull out what matters operationally: decisions, action items, blockers, follow-ups, deadlines.
- When the user wants a practical answer, do not over-focus on formatting theory.
- If the source is thin or noisy, still produce the best useful output, but mark confidence clearly.

## Main workflow

### 0. Transcript noise repair (always run first)

Before any analysis, scan the transcript for ASR errors. Read `references/thai-transcript-repair.md` for rules.

Quick summary of repair behavior:
- Fix obvious Thai ASR name errors when context is clear (e.g. a misheard Thai name → the confirmed spelling)
- Fix common Thai filler/garbled phrases (e.g. "พาเข้าใจ" → "พอเข้าใจ")
- Preserve English technical terms that are likely correct (e.g. "open link", "quiz", "analytics")
- When uncertain, keep the original and mark `[unclear]`
- Collect all corrections into a **Normalization Notes** section in the output
- Never silently change a name, system name, or number without noting it

### 1. Identify the source mix

Choose the dominant input type:

1. **Raw transcript**
2. **AI meeting summary** (e.g. PLAUD Summary)
3. **Screenshot of meeting notes/transcript UI**
4. **Mixed sources** (transcript + summary + screenshot + chat notes)
5. **Rough human notes only**

Default trust order:
- raw transcript (after noise repair)
- direct screenshots of transcript/notes UI
- human notes
- AI summary

If multiple sources disagree, prefer the highest-trust source and call out the mismatch.

### 2. Choose the output mode

Pick the smallest mode that satisfies the user's ask:

- **Quick summary** — short recap with next steps
- **Action extraction** — owners, due dates, follow-ups
- **Decision log** — what was agreed and what remains open
- **Team update** — clean message ready to send internally
- **Client-safe recap** — cleaner, external-facing summary
- **Full distillation** — summary + facts + decisions + actions + open questions + risks
- **Cleaned transcript** — noise-repaired readable version of raw transcript

If the user says only "สรุปให้หน่อย" or "help summarize", default to **Full distillation** when the meeting appears important, otherwise **Quick summary**.

### 3. Read only the needed reference

Load the matching reference file:

- `references/thai-transcript-repair.md` — always for Thai transcripts (loaded in step 0)
- `references/known-names.md` — always check for pre-confirmed name/term corrections (loaded in step 0)
- `references/source-confidence.md` when sources conflict or AI summary quality is questionable
- `references/output-modes.md` for output structure and mode selection
- `references/plaud-patterns.md` for PLAUD-specific behavior and cautions
- `references/action-extraction.md` when the user mainly wants tasks, owners, or deadlines
- `references/speaker-mapping.md` when the user provides a speaker map or context clues are strong enough to infer one
- `references/team-client-recap.md` when the user wants a message to forward or send
- `references/capture-handoff.md` when the result should be captured into memory, daily note, docs-toolkit artifact, or Obsidian

Read only what is needed beyond thai-transcript-repair and known-names.

### 4. Extract the operational core

Unless the user explicitly wants a verbatim transcript, identify:

- purpose of the meeting
- what was actually demonstrated/discussed
- confirmed decisions
- action items
- owners
- deadlines or time references
- blockers / missing inputs
- unresolved questions
- practical next step for the user

### 5. Normalize dates and certainty

When a deadline is vague:
- preserve the original wording if needed
- convert to a concrete date only when the context makes it reliable
- label it as inferred when necessary

Examples:
- "พรุ่งนี้" → use a concrete date only if the meeting date is known
- "ประมาณ 9 โมง" → mark as approximate
- "เดี๋ยวส่งในกลุ่ม" → action exists, deadline unclear

### 6. Flag AI overreach

If an AI summary appears to add structure or claims not clearly present in the transcript, say so briefly.

Good pattern:
- "PLAUD summary is directionally useful, but this point is only weakly supported by transcript."
- "This action item appears inferred from the summary, not explicitly said in the transcript."

### 7. Produce a practical output

Default order:
1. short summary
2. normalization notes (if any repairs were made)
3. confirmed facts
4. decisions
5. action items
6. open questions / risks
7. recommended next move

Keep it concise unless the user asks for a fuller artifact.

## Output rules

### Confidence labels

Use these when helpful:
- **Confirmed** — directly supported by transcript or explicit source
- **Inferred** — strong interpretation from context, but not directly stated
- **Unclear** — conflicting, incomplete, or weakly supported

### Normalization notes

Include when transcript repairs were made. Format:

```
## Normalization Notes
- a misheard Thai name → likely the confirmed name spelling (when consistent across transcript)
- "ดึงคำอากาศ" → unclear, possibly "ดึงคำถาม" from context
- "analytic" → "analytics" (English term correction)
```

### Action item format

Prefer:
- task
- owner
- due date
- confidence

If owner or due date is missing, say **Unassigned** or **No clear deadline** instead of guessing.

### Speaker handling

If the source only says Speaker 1/2/3/4:
- keep those labels as-is
- do not rename them to real people without evidence
- if the user provides a speaker map, read `references/speaker-mapping.md` and apply it
- if context clues are very strong, suggest a mapping but do not apply silently
- check `references/known-names.md` for prior speaker maps from the same project/client

## Practical quality bar

A good meeting distillation should help the user answer:
- What actually happened?
- What was decided?
- What do we need to do next?
- What is still missing or ambiguous?
- Is this from transcript truth or AI interpretation?
- Were any names/terms likely wrong in the original?

## Optional follow-through

When the user asks for it, convert the distilled result into one of these:
- internal team message
- client recap
- checklist
- daily note entry
- decisions / commitments / follow-ups capture

If a result clearly creates a commitment or follow-up, suggest capture rather than silently assuming it.

## Learning from corrections

After the user confirms name/term corrections in a session:
- Offer to save confirmed corrections to `references/known-names.md`.
- Next time the same name appears in a transcript, apply the fix automatically.
- Never add guesses to known-names — only user-confirmed corrections.
