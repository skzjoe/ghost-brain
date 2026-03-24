# PLAUD Patterns

Use when the source comes from PLAUD notes, transcripts, screenshots, or emailed links.

## Common pattern

PLAUD often provides:
- a generated Summary view
- a Transcript view
- screenshots or copied snippets from either view

## Recommended handling

1. Check whether the source is Summary or Transcript.
2. If Transcript exists, treat it as the stronger source.
3. Use Summary only as a helper for structure, not as final truth.

## Frequent PLAUD failure modes

- Adds polished headings not explicitly discussed
- Assigns action items that are only implied
- Invents formal “decisions” from casual conversation
- Turns approximate timing into exact deadlines
- Preserves speaker anonymity as Speaker 1/2/3/4

## Safe operating pattern

- Start with transcript-backed facts
- Then compare with PLAUD summary
- Keep useful structure
- Remove unsupported certainty

## Example wording

- “PLAUD summary is mostly aligned, but the transcript supports a lighter claim.”
- “This looks like a walkthrough/demo rather than a firm decision meeting.”
- “The summary adds deadlines that are not clearly spoken in the transcript.”

## Special case: screenshots

If the user sends a screenshot of PLAUD UI:
- identify whether the screenshot shows Transcript or Summary tab
- do not claim content beyond what is visible
- use the screenshot to guide next navigation or extraction

## PLAUD + Thai ASR compound errors

PLAUD uses its own ASR pipeline which has specific Thai weaknesses:
- Speaker names in Thai are almost always garbled — always cross-check with context
- PLAUD Summary may "fix" a garbled name into a different wrong name — do not trust corrections in the Summary unless confirmed by transcript context
- Thai filler words (ครับ, ค่ะ, อ่ะ) are sometimes merged into the next word by PLAUD's ASR
- When PLAUD splits a single speaker turn across two Speaker labels, the content is usually still one person — note the likely merge
