# Ghost Brain v1.2.0 Release Notes

Date: 2026-04-13
Tag: `v1.2.0`

## Summary

Ghost Brain v1.2.0 turns the product into a more complete layer on top of OpenClaw: cleaner core interfaces, a unified CLI, working-memory helpers, a measurable research stack, stronger memory safety, and a public-repo hygiene pass before release.

## Highlights

### 1. Ghost core is now a first-class internal product surface
- additive `scripts/ghost_core/` package
- formal contracts, adapters, defaults, and workspace resolution
- cleaner boundaries between product logic and runtime/platform concerns

### 2. Unified CLI + working-memory surfaces
- `ghost_cli.py` for recall, capture, learning, context, working memory, and research
- `ghost_session_context.py` for focus/blockers/deadlines
- `ghost_working_memory.py` for `brief` and due/stale follow-up triage

### 3. Research and eval stack
- Ghost-native eval, safety, regression, continuity, trajectory logging, dashboarding, and experiment tracking
- split CLIs plus shared runtime in `ghost_research_lib.py`
- focus reports that turn eval data into next-best-action style recommendations

### 4. Reliability hardening
- atomic writes and locked JSONL appends for research state
- memory content scanning + duplicate/size protection
- cleaner automation-friendly outputs and safer path handling

### 5. Release hygiene and genericization
- User-specific, client-specific, and workspace-specific examples scrubbed from public-facing product files
- PII sweep run before release
- repo docs/install/test surfaces aligned with current product state

## Validation
- `pytest -q tests` → `129 passed`
- public-repo PII sweep complete, with only intentional public ownership references left (repo URL / LICENSE)

## Upgrade notes
- existing memory paths stay the same
- existing CLIs remain usable
- new integrations should prefer `ghost_core.*` and `ghost_cli.py`
- markdown memory remains the canonical store; SQLite memory stays a derived/indexed layer

## Recommended next milestone

### P0
1. self-discipline guardrails
2. markdown-vs-DB drift/freshness checks
3. targeted data-critical test expansion

### P1
4. lightweight L2 conversation memory

### P2
5. stronger local skill matching beyond raw keyword overlap
