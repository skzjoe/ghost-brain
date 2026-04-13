# Speaker Mapping

Handle the transition from anonymous Speaker labels to real people.

## Default behavior

Keep Speaker 1/2/3/4 as-is until there is evidence.

## When the user provides a map

If the user says something like "Speaker 2 คือ <person-b>" or provides a full map:

1. Apply the mapping to the entire output.
2. Note the mapping at the top of the output:
   ```
   ## Speaker Map (provided by the user)
   - Speaker 1 → <person-a>
   - Speaker 2 → <person-b>
   - Speaker 3 → <person-c>
   - Speaker 4 → <person-d>
   ```
3. Re-read action items and decisions with real names.
4. If a mapping feels wrong based on context, flag it.

## Context-based inference

Sometimes the transcript itself gives strong clues:

- "ผมจะสร้าง user ให้" → this speaker is likely admin/dev
- "ค่ะ เข้าใจแล้วค่ะ" → likely the person being trained
- Someone addressed by name → the next speaker is likely that person

Rules:
- If confidence is high, apply the mapping and note it.
- If confidence is medium, suggest the mapping but do not apply silently.
- If confidence is low, keep Speaker labels.

## Accumulating speaker knowledge

If the user has mapped speakers in a previous meeting with the same participants:
- Check `references/known-names.md` for prior mappings.
- Suggest reusing the same map if participant context matches.
- Do not auto-apply across different projects/clients without confirmation.
