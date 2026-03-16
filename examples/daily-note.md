# Example: Daily Note

This is what a typical daily note looks like after EOD summary runs:

```markdown
# 2026-01-20 (Monday)

## 🧠 Log
- Morning: reviewed PR #142, found edge case in batch processing
- 10:00 call with Tom (Acme) — wants UAT by end of month, confirmed feasible
- Afternoon: refactored API auth middleware, added rate limiting
- Debugged flaky test — was a timezone issue in date comparison

## ✅ Done
- PR #142 reviewed + approved
- Auth middleware refactored (3 files)
- Flaky test fixed
- Sent Tom the UAT timeline

## 🧾 Decisions
- [2026-01-20] Rate limit at 100 req/min per API key — generous enough for normal use, catches abuse. (API design)
- [2026-01-20] Use date-fns over moment.js for new code — smaller bundle, better tree-shaking. (tech decision)

## 📌 Next Actions
- Deploy auth changes to staging
- Write migration script for legacy API keys
- Prep Thursday demo for Acme

## 🤝 Follow-ups
- Tom to confirm server specs by Wednesday
- Sarah to review migration script when ready

## 📎 Artifacts
- `projects/api/middleware/rate-limiter.ts` — new rate limiting middleware
```
