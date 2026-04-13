# Known Names & ASR Corrections

Example-only corrections for transcript repair. Replace these with confirmed names from the current workspace before using in a real client context.

## Thai name ASR correction examples

| ASR variants | Correct name | Context / Project | Added |
|---|---|---|---|
| <misheard-name-a>, <misheard-name-b> | <confirmed-name-a> | client training | <date> |

## English/technical term corrections

| ASR output | Correct term | Context |
|---|---|---|
| ควิสต์, ควิซ, ควิส | Quiz | online exam system |
| อะนาลิติก, analytic | Analytics | dashboard/reporting |

## Speaker map examples

| Project / Client | Speaker label | Real name | Confidence | Date |
|---|---|---|---|---|
| <project-alpha> | Speaker A | <person-a> | Confirmed by the user | <date> |
| <project-alpha> | Speaker B | <person-b> | Confirmed by the user | <date> |

## Rules for this file

- Only add entries that the user has confirmed or that have appeared consistently across 2+ transcripts.
- Never add a guess here. Guesses stay in the output's Normalization Notes only.
- Review periodically and remove entries that no longer apply.
- This file is checked during step 0 (transcript repair) to pre-apply known corrections.
