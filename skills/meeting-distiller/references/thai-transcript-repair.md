# Thai Transcript Repair

Apply these rules before any distillation when the transcript contains Thai speech.

## Why this matters

Thai ASR (especially from PLAUD, Whisper, Google STT) frequently produces:
- Misheard proper names (แพร → แพ้, แพร่, พา, พราว)
- Garbled compound phrases (พอเข้าใจ → พาเข้าใจ)
- Wrong tones on short words (ค่ะ → คะ → ครับ confusion)
- Filler merging (อ่ะครับ, แบบว่า, อ๋อ concatenated to next word)
- Thai-English code-switch errors (quiz → ควิสต์ → ควิซ → ควิส)
- Number/unit confusion (50 ข้อ → ห้าสิบข้อ sometimes garbled)
- Sentence boundary errors (no punctuation → run-on lines)

## Repair categories

### Category 1: Names (HIGH CAUTION)

People names, company names, project names, system names.

Rules:
- If the same name appears multiple times in different spellings, pick the most likely correct form.
- Use context to decide: if someone says a clearly misheard Thai name in a login context, normalize it to the confirmed spelling (a person being asked to log in).
- If the user has mentioned the name before in other sessions, use the known correct spelling.
- Always note the correction in Normalization Notes.
- If truly uncertain, keep original + add `[likely: ...]`.

Common Thai name ASR errors:
| ASR output | Likely correct | Clue |
|---|---|---|
| <misheard-name> | <confirmed-name> | common Thai name pattern |
| <variant-a>, <variant-b> | <confirmed-nickname> | common Thai nickname pattern |
| <misheard-user-name> | <user-name> | context: the main speaker |
| บุตรดม | ? | needs more context — could be a course name |

### Category 2: Technical terms (MEDIUM CAUTION)

System terms, UI labels, English loanwords.

Rules:
- English terms embedded in Thai speech are often correct if they sound right: "quiz", "course", "back office", "analytics", "Excel", "save", "refresh".
- Thai transliterations may be garbled: ควิสต์ → Quiz, อะนาลิติก → Analytics.
- Fix obvious transliteration errors silently in the summary but note in Normalization Notes if the original was significantly different.
- UI-specific terms (open link, save, refresh) are usually verbatim — keep as-is.

### Category 3: Fillers and speech artifacts (LOW CAUTION)

Fillers, hedges, false starts, self-corrections.

Rules:
- Strip or compress fillers when summarizing: อ่ะ, แบบว่า, อ๋อ, เอ่อ, ก็คือ, ใช่ไหมครับ (rhetorical).
- Keep fillers only if they signal uncertainty or hedging that matters to the summary.
- Fix run-on sentences by splitting at natural phrase boundaries.
- "ครับ" / "ค่ะ" at line boundaries are usually correct and can be kept or dropped as needed.

### Category 4: Garbled phrases (HIGH CAUTION)

Phrases where the ASR produced something that doesn't make sense.

Rules:
- Try to reconstruct from context.
- If reconstruction is confident, use the fixed version and note it.
- If reconstruction is uncertain, keep original and mark `[unclear]`.
- Never invent meaning that isn't supported by surrounding context.

Examples:
| ASR output | Context | Likely fix | Confidence |
|---|---|---|---|
| ดึงคำอากาศ | speaker was about to edit quiz questions | ดึงคำถาม? | uncertain — mark [unclear] |
| พาเข้าใจประมาณหนึ่งแล้ว | end of session, wrapping up | พอเข้าใจประมาณหนึ่งแล้ว | high |
| มานั่งกดเลือกได้ | describing UI interaction | correct as-is | high |
| ข้อสอบเตรียมบุตรดม | course name context | ข้อสอบเตรียม [course name unclear] | uncertain |

### Category 5: Speaker attribution errors (MEDIUM CAUTION)

Sometimes ASR assigns speech to the wrong speaker.

Rules:
- If Speaker X says something that clearly belongs to Speaker Y's role (e.g. a student saying admin instructions), note the likely misattribution.
- Do not silently reassign speakers.
- In the summary, attribute to the speaker label as given but note if it seems wrong.

## Repair workflow

1. **Check `references/known-names.md` first** — apply any pre-confirmed corrections immediately.
2. Read through the full transcript once.
3. Identify recurring name/term patterns.
4. Build a correction table (even if small).
5. Apply corrections while reading for content.
6. Include Normalization Notes in output.
7. **After the user confirms** corrections in this session, offer to update `references/known-names.md` so the same fix applies automatically next time.

## Output: Normalization Notes format

```
## Normalization Notes
| Original | Corrected to | Category | Confidence |
|---|---|---|---|
| <misheard-name> | <confirmed-name> | Name | High |
| ควิสต์ | Quiz | Tech term | High |
| ดึงคำอากาศ | [unclear] | Garbled | Low |
| พาเข้าใจ | พอเข้าใจ | Garbled phrase | High |
| บุตรดม | [unclear — course name?] | Name | Low |
```

## Key principle

**Repair to make usable, not to make perfect.**

The goal is that the user can read the summary and trust it. Not that every word is linguistically correct. Focus repair effort on:
1. Names (who)
2. Actions (what to do)
3. Deadlines (when)
4. System/project references (where)

Low-value repairs (filler words, casual phrasing) matter less.
