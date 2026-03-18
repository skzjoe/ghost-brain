# Coding Workflow — Brownfield AI Engineering

A practical workflow for using coding agents on real codebases without drifting into slop.

This is optimized for:
- brownfield / legacy repos,
- multi-file changes,
- debugging across layers,
- refactors,
- long-running coding tasks.

---

## Why this exists

AI coding tools often look productive while quietly creating churn:
- too much rework,
- bloated context windows,
- weak reviewability,
- changes that are hard for humans to follow.

This workflow fixes that by making context a managed engineering resource.

---

## Core principles

### 1. Context is scarce
Do not maximize context size.
Maximize **relevant context density**.

### 2. Research before changing unfamiliar systems
If the agent does not understand the system slice yet, it should not be implementing.

### 3. Plans are execution contracts
A plan is not just a prompt. It is a reviewer aid, an alignment tool, and a change contract.

### 4. Subagents are for context isolation
Use them to scan, trace, and compress findings from a large codebase.
Do not use them as fake org roles unless that separation actually reduces context pollution.

### 5. Reset before the thread collapses
If the session is getting noisy, correction-heavy, or bloated, create a compaction handoff and restart clean.

### 6. Use the smallest valid process
Do not force a heavy workflow on trivial edits.

---

## Workflow tiers

## Tier 0 — Direct Execute
Use when all are true:
- tiny change,
- scope obvious,
- files already known,
- low risk,
- rollback easy.

Examples:
- typo fixes,
- label/copy tweaks,
- one-line config changes,
- tiny known-file fixes.

Output:
- short implementation summary,
- validation note if relevant.

---

## Tier 1 — Light Research → Plan → Implement
Use when:
- moderate scope,
- multiple files likely,
- repo area is somewhat known,
- implementation is bounded.

Examples:
- medium bug fix,
- small feature extension,
- refactor inside a familiar subsystem.

Artifacts:
- short research notes,
- short plan,
- implementation summary.

---

## Tier 2 — Full Research → Plan → Implement + Compaction
Use when any are true:
- brownfield / legacy repo,
- unfamiliar subsystem,
- cross-cutting change,
- debugging across layers,
- long task likely to overflow one clean context,
- risky or hard-to-rollback change,
- handoff between agents likely.

Artifacts:
- research artifact,
- plan artifact,
- compaction handoff when needed,
- implementation summary.

---

## Canonical flow

## 1) Research
Goal: compress truth from the codebase.

Research should capture:
- task objective,
- subsystem boundaries,
- relevant files,
- key functions/classes/routes/events,
- confirmed truths from code,
- risks and unknowns.

Use subagents here for:
- repo scanning,
- tracing flows,
- locating the real files involved,
- summarizing read-heavy exploration.

Move on only when:
- the relevant system slice is identified,
- the files that matter are known,
- the main unknowns are explicit.

---

## 2) Plan
Goal: compress intent into something both humans and agents can execute.

A plan should include:
- objective,
- files to change,
- intended edits by file,
- order of operations,
- validation path,
- rollback / risk notes,
- open questions.

A plan is good enough when:
- a reviewer can understand the direction quickly,
- a coding agent can execute with low ambiguity,
- the validation path is explicit.

---

## 3) Implement
Goal: execute with low ambiguity and low drift.

Rules:
- follow the plan,
- avoid opportunistic scope creep,
- validate after meaningful steps,
- note any deviations.

If implementation changes the direction materially, update the plan.

---

## 4) Compact and restart when needed
Create a compaction handoff when:
- the thread is too long,
- exploration noise is polluting the context,
- the agent has taken multiple wrong turns,
- you want a clean handoff to a fresh session.

A compaction handoff should include:
- current objective,
- confirmed truths,
- relevant files and anchors,
- work completed so far,
- pending steps,
- failed paths to avoid,
- blockers,
- next best starting point.

---

## Anti-slop rules

- No coding before basic truth exists.
- No endless correction spirals in one thread.
- No fake subagent theater.
- No hidden validation.
- No silent scope expansion.

---

## Templates

Use these templates for non-trivial coding work:
- `skills/assets/coding-research-template.md`
- `skills/assets/coding-plan-template.md`
- `skills/assets/coding-compaction-handoff-template.md`
- `skills/assets/coding-implementation-summary-template.md`

---

## Quick start

For a brownfield coding task:
1. Start with research.
2. Save a plan before major edits.
3. Execute from the plan.
4. Compact before context quality collapses.

This workflow is not bureaucracy.
It is how you keep coding agents useful in messy real-world systems.
