# Example: `/audit` output

Synthetic illustration only—not a report about a real user or a measured product score.

## Verdict: PARTIAL

The inspected request completed correctly, but background delivery and active-stop behavior lack relevant evidence.

| Outcome | Verdict | Evidence / gap |
|---|---|---|
| Understand | PASS | Trace A: supplied destination retained; no redundant clarification |
| Complete | PARTIAL | Trace A: write receipt and readback agree; no background-delivery example |
| Proactive | UNVERIFIED | No concrete opportunity in the inspected request |
| Trustworthy | PARTIAL | Trace A: claims match receipts; active interruption not observed |
| Simple | PASS | Trace A: direct request-to-result flow, no duplicate mechanism in scope |

Scope: one synthetic capture interaction. These narrow PASS results do not generalize to every task or runtime. Code/file checks, if run, would be reported separately.

Smallest next step: review an existing background task with both completion and user-visible delivery evidence. No new external probe was created.

Obsidian and memory maintenance, business/project status, configuration and schedule changes were outside scope. Nothing changed.
