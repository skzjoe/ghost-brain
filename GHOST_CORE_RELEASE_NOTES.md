# GHOST_CORE_RELEASE_NOTES.md

## Ghost core production-grade uplift

This release turns Ghost into a cleaner production-grade product layer on top of OpenClaw without trying to become a separate runtime.

### What improved
- Ghost now has a unified CLI surface via `scripts/ghost_cli.py`
- Ghost now has a formal additive core package under `scripts/ghost_core/`
- recall is more evidence-first, explainable, and automation-friendly
- learning loop outputs are more structured and state-aware
- workspace/path handling is more consistent across Ghost scripts
- Ghost now has a first-class session-context surface for current work focus, blockers, next actions, and commitments due
- Ghost now exposes a CLI session-context view for humans and automation

### What did not change
- OpenClaw still owns runtime/platform concerns
- memory file locations did not move
- Obsidian merge-first workflow did not change
- existing CLIs and script entrypoints remain usable

### Main benefits
- safer automation contracts
- cleaner internal boundaries
- easier future refactors without breaking current behavior
- better explainability for recall and learning state
- stronger foundation for Ghost health, proactive surfaces, and product packaging

### Operator note
This is intentionally an additive upgrade. Existing scripts still work, but new Ghost-facing integrations should prefer `ghost_core.*` over ad hoc direct imports or local path assumptions.

### Suggested commit title
`feat(ghost): add production-grade ghost_core interfaces and runtime adapters`

### Suggested commit body
- add additive ghost_core package with contracts, ports, errors, adapters, and defaults
- harden unified recall and learning loop with structured automation surfaces
- centralize workspace resolution across Ghost scripts
- preserve Obsidian compatibility and existing memory layout
- add migration notes, interface docs, and contract tests
