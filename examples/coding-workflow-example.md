# Coding Workflow Example — Brownfield Bug Fix

A concrete example of how to use Ghost Brain's coding workflow on a non-trivial bug in an existing codebase.

---

## Scenario

Task:
> Fix duplicate webhook processing in an existing billing integration.

Context:
- Existing production codebase
- Multiple files involved
- Side effects matter (double charges / duplicate invoices)
- Debugging spans API route, service layer, and persistence

This is **not** a Tier 0 task.
It should use **Research → Plan → Implement**.

---

## Step 1 — Research

Use `skills/assets/coding-research-template.md`.

Example:

```markdown
# Coding Research — Prevent duplicate webhook processing

**Date:** 2026-03-18
**Owner:** Ghost
**Project/Repo:** billing-service
**Tier:** Tier 2

## 1) Objective
- Prevent duplicate webhook events from creating duplicate invoices.

## 2) Scope / System Slice
- Subsystem(s): webhook ingestion, billing service, invoice persistence
- In scope: webhook route, dedup logic, invoice creation path
- Out of scope: payment provider retry policy changes

## 3) Confirmed truths from code
- Webhook events enter via `src/api/webhooks.ts`.
- Invoice creation is triggered in `src/services/billing/processWebhook.ts`.
- There is currently no persisted idempotency check for provider event IDs.

## 4) Relevant files / anchors
- `src/api/webhooks.ts` — request entry point
- `src/services/billing/processWebhook.ts` — main business flow
- `src/db/invoices.ts` — persistence layer

## 5) Flow notes
- Entry point: POST `/api/webhooks/provider`
- Key transitions/events: route → validation → processWebhook → invoice insert
- Dependencies/integrations: payment provider payload, DB write

## 6) Risks / Unknowns
- Existing retries may rely on current behavior.
- Duplicate prevention may need schema support.

## 7) Likely implementation directions
- Option A: in-memory dedup cache
- Option B: persisted event-id idempotency check
- Recommended direction: Option B
```

---

## Step 2 — Plan

Use `skills/assets/coding-plan-template.md`.

Example:

```markdown
# Coding Plan — Prevent duplicate webhook processing

**Date:** 2026-03-18
**Owner:** Ghost
**Project/Repo:** billing-service
**Based on research:** docs/research/webhook-dedup.md

## 1) Objective
- Ensure each provider event ID is processed at most once.

## 2) Implementation strategy
- Persist provider event IDs and short-circuit duplicate processing before invoice creation.

## 3) Files to change
- `src/api/webhooks.ts` — pass provider event ID through explicitly
- `src/services/billing/processWebhook.ts` — add idempotency check before invoice creation
- `src/db/invoices.ts` — add lookup/insert helpers for event ID tracking

## 4) Ordered steps
1. Add provider event ID extraction at webhook entry point.
2. Add DB helper to check whether event ID already exists.
3. Short-circuit processing if event was already handled.
4. Add tests for duplicate delivery.

## 5) Validation / Test plan
- [ ] Duplicate webhook event does not create second invoice
- [ ] New webhook event still creates invoice successfully
- [ ] Existing event flow remains unchanged for valid first delivery
- [ ] Manual verification: replay same payload twice in local/dev
```

---

## Step 3 — Implement

Then execute the plan.

Good implementation behavior:
- stay within the files listed,
- validate after meaningful steps,
- record deviations if the plan changes.

---

## Step 4 — Compact if the thread drifts

If the coding session becomes noisy, create a handoff using `skills/assets/coding-compaction-handoff-template.md`.

Example:

```markdown
# Coding Compaction Handoff — Prevent duplicate webhook processing

**Date:** 2026-03-18
**Prepared by:** Ghost
**Project/Repo:** billing-service
**Reason for compaction:** large test/debug output and multiple exploratory branches

## 1) Current objective
- Finish persisted webhook idempotency protection.

## 2) Confirmed truths
- Duplicate invoices are caused by repeated provider deliveries.
- The route does not currently short-circuit duplicates.
- The invoice table already stores a provider reference that can anchor dedup support.

## 4) Work completed so far
- Event ID extraction added at route layer.
- DB helper for existing-event lookup added.
- Initial test scaffold created.

## 5) Pending plan steps
1. Complete service-layer short-circuit logic.
2. Finish duplicate-delivery test.
3. Run regression verification.
```

---

## What this example demonstrates

This workflow keeps the agent from jumping straight into code without understanding:
- where the bug really lives,
- what files matter,
- what the intended change path is,
- how success will be verified.

That is the point of the workflow:
**less slop, more traceability, safer changes in old codebases.**
