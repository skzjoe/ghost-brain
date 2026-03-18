# Coding Quickstart — Use This for Non-Trivial Coding Tasks

A one-page quickstart for using Ghost Brain's coding workflow in real work.

---

## Use this workflow when

Use the full workflow if any are true:
- you are working in an older / unfamiliar codebase,
- more than 1–2 files will likely change,
- debugging spans multiple layers,
- business logic or side effects matter,
- the task could drift if the agent improvises.

If the change is tiny and obvious, skip to direct execution.

---

## The workflow

## 1) Research
Before coding, find the real system slice.

Capture:
- objective,
- relevant files,
- key flow,
- confirmed truths from code,
- unknowns/risks.

Template:
- `skills/assets/coding-research-template.md`

---

## 2) Plan
Turn the research into an explicit implementation path.

Capture:
- files to change,
- intended edits,
- order of operations,
- validation/test plan,
- rollback/risk notes.

Template:
- `skills/assets/coding-plan-template.md`

---

## 3) Implement
Execute from the plan.

Rules:
- do not expand scope casually,
- validate after meaningful steps,
- record deviations if the plan changes.

Template:
- `skills/assets/coding-implementation-summary-template.md`

---

## 4) Compact and restart when needed
If the thread becomes noisy or correction-heavy, stop and create a handoff.

Capture:
- current objective,
- confirmed truths,
- completed work,
- pending steps,
- failed paths to avoid,
- best next starting point.

Template:
- `skills/assets/coding-compaction-handoff-template.md`

---

## Fast decision rule

### Use direct execute if:
- tiny fix,
- low risk,
- obvious file,
- easy rollback.

### Use Research → Plan → Implement if:
- brownfield,
- medium/high risk,
- unclear file/flow,
- multiple files,
- likely long-running task.

---

## Recommended prompt pattern

For a non-trivial coding task, start with:

> Treat this as a brownfield coding task. Start with research, then produce a plan, then implement only after the plan is clear. Use compaction if the thread gets noisy.

---

## What success looks like

A good run should leave behind:
- a research artifact,
- a plan artifact,
- an implementation summary,
- and, if needed, a compaction handoff.

That gives you:
- less slop,
- better reviewability,
- safer delegation,
- easier restarts.
