# GHOST_CORE_MIGRATION_NOTES.md

Purpose: make Ghost more production-grade without breaking existing runtime behavior or Obsidian workflows.

## What changed

Ghost now has an additive package surface under `scripts/ghost_core/`.

Use this layer for new integrations instead of importing implementation details directly from mixed CLI scripts.

Current stable pieces:
- `ghost_cli.py` — unified product-facing CLI over stable Ghost surfaces
- `ghost_core.workspace` — canonical workspace/path resolution
- `ghost_core.contracts` — typed payloads and schema labels
- `ghost_core.ports` — protocol boundaries
- `ghost_core.errors` — stable Ghost-core errors
- `ghost_core.adapters.*` — wrappers over existing recall / learning / memory behavior
- `ghost_core.adapters.session_context` — execution-state snapshot from Ghost-owned work files
- `ghost_core.defaults` — default runtime wiring

## Compatibility policy

These remain valid:
- existing script CLIs
- existing memory file locations
- existing Obsidian push scripts
- existing merge-first daily note behavior
- `scripts/ghost_core_contracts.py` imports

## Obsidian safety rule

Do not change these without an explicit migration:
- daily notes: `memory/YYYY-MM-DD.md`
- structured memory: `memory/*.md`
- learnings: `.learnings/**/*.md`
- push flow: `scripts/obsidian_push_daily.sh`, `scripts/obsidian_push_syntheses.sh`

Ghost core may improve contracts and routing, but should not silently move files or switch merge semantics.

## Preferred imports going forward

Prefer:
- `from ghost_core.workspace import get_workspace_paths`
- `from ghost_core.contracts import ...`
- `from ghost_core.defaults import build_default_runtime`

Avoid for new code:
- ad hoc `Path(__file__).parent.parent`
- ad hoc `~/.openclaw/workspace` path assumptions
- raw dict contracts when a Ghost-core contract exists
- dynamic import path hacks

## Migration approach

Safe order:
1. keep current script CLIs intact
2. move new code to `ghost_core.*`
3. let old scripts delegate gradually via adapters and `ghost_core.defaults`
4. only remove compatibility shims after callers are migrated

Current delegation status:
- `ghost_cli.py` is now the preferred consolidated CLI over recall / capture / user-model / learning / context surfaces
- `ghost_unified_recall.py` CLI now delegates report/capture/user-model flows through `ghost_core.defaults`
- `ghost_learning_loop.py` CLI now delegates reflect/status/digest/promote/detect flows through `ghost_core.defaults`
- `ghost_learning_loop.py check-skill` now delegates through the Ghost-core learning adapter
- `ghost_session_context.py` exposes the Ghost-core execution-state snapshot directly

## Current outcome

Ghost is still a layer on OpenClaw, not a replacement runtime.
The production-grade improvement is in:
- cleaner boundaries
- stable contracts
- consistent workspace resolution
- safer automation surfaces
- preserved Obsidian compatibility
