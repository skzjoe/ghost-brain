# GHOST_CORE_CHANGELOG.md

## Unreleased — Production-grade Ghost core uplift

### Added
- unified `scripts/ghost_cli.py` over stable Ghost surfaces
- additive `scripts/ghost_core/` package with stable import surface
- canonical workspace resolver in `ghost_core.workspace`
- typed contracts in `ghost_core.contracts`
- protocol boundaries in `ghost_core.ports`
- stable Ghost-core errors in `ghost_core.errors`
- runtime-backed adapters for recall, learning loop, memory DB, and session context
- default runtime wiring in `ghost_core.defaults`
- `ghost_session_context.py` CLI for Ghost-owned execution-state snapshots
- migration notes in `GHOST_CORE_MIGRATION_NOTES.md`
- Ghost core interface documentation in `GHOST_CORE_INTERFACES.md`
- session-context snapshot surface derived from `ACTIVE_WORK.md` and `memory/commitments.md`

### Changed
- `ghost_cli.py` is now the recommended product-facing CLI before installable packaging
- `ghost_unified_recall.py` now exposes stronger evidence-first recall results
- `ghost_unified_recall.py` capture path now returns stable machine-readable fields while keeping compatibility fields
- `ghost_learning_loop.py` now exposes stable JSON envelopes for automation surfaces
- main Ghost scripts now delegate more CLI/runtime behavior through `ghost_core.defaults`
- `ghost_learning_loop.py check-skill` now delegates through the Ghost-core learning adapter
- workspace resolution is now centralized across core Ghost scripts instead of mixed local path assumptions

### Fixed
- learning captures now sync review state immediately
- learning state writes are now atomic
- scoped learning IDs no longer collide across files
- grep fallback now scans `.learnings/**/*.md`
- DB-backed recall preserves more explainability metadata

### Compatibility
- Ghost remains a layer on top of OpenClaw, not a replacement runtime
- existing script CLIs remain valid
- existing memory file layout remains unchanged
- existing Obsidian push scripts and merge-first behavior remain unchanged
- `scripts/ghost_core_contracts.py` remains as a compatibility shim

### Tested
- targeted contract/adapter/recall/learning suites passing
- full test suite passing: 271 tests
