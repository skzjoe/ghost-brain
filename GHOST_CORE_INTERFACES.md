# GHOST_CORE_INTERFACES.md

Purpose: formalize the Ghost-owned product layer without rebuilding runtime concerns that OpenClaw already owns.

## Boundary

Ghost core owns:
- memory semantics and routing
- recall UX and evidence surfaces
- learning loop and promotion lifecycle
- execution-state intelligence
- Ghost-layer health and audit views

Ghost core does **not** own:
- gateway, sessions, tools, browser, MCP, cron engine, models, provider routing
- platform health, doctor, security, or channel infrastructure

## Obsidian compatibility rule

Ghost core must preserve the existing Obsidian-facing memory layout and push workflow:
- daily notes remain under `memory/YYYY-MM-DD.md`
- structured memory remains under `memory/*.md`
- syntheses / pushes remain owned by the existing Obsidian scripts and merge policy
- Ghost core may improve contracts and routing, but should not silently change file locations or overwrite-first behavior

## Production contracts

Ghost core now has an additive package surface under `scripts/ghost_core/`:
- `workspace.py` — canonical path resolution
- `contracts.py` — stable typed Ghost-owned payloads
- `ports.py` — protocol boundaries for memory / recall / learning / capture
- `errors.py` — stable Ghost-core error classes
- `adapters/` — thin wrappers over existing runtime-backed scripts
- `defaults.py` — default wiring for the current workspace/runtime

Compatibility rule:
- existing script CLIs remain valid
- `scripts/ghost_core_contracts.py` stays as a compatibility shim
- migrations should move callers toward `ghost_core.*`, not force a rewrite

## 1) Recall contract
Implemented in:
- `scripts/ghost_core/contracts.py`
- `scripts/ghost_core/adapters/unified_recall.py`
- `scripts/ghost_core_contracts.py` (compat shim)
- `scripts/ghost_unified_recall.py`

Stable fields for each recall result:
- `query`
- `item_type`
- `source_bucket` (`memory|daily|learnings`)
- `source_label`
- `source_detail`
- `file`
- `line`
- `citation`
- `score`
- `confidence`
- `snippet`
- `date`

Stable report fields:
- `query`
- `generated_at`
- `total_results`
- `grouped_counts`
- `strongest_signal`
- `recommendations`
- `results`

Design rule:
Recall should be evidence-first. The caller should always be able to tell where the memory came from and how strong it is.

## 2) Learning digest contract
Implemented in:
- `scripts/ghost_core/contracts.py`
- `scripts/ghost_core/adapters/learning_loop.py`
- `scripts/ghost_core_contracts.py` (compat shim)
- `scripts/ghost_learning_loop.py`

Stable status snapshot fields:
- `total_learnings`
- `by_state`
- `due_for_review`
- `last_captured`
- `skill_candidates_pending`
- `skill_improvements_pending`
- `validated_total`
- `promoted_total`
- `recent_captures_7d`
- `recent_validations_30d`
- `recent_promotions_30d`
- `impact`
- `backlog`
- `recommended_actions`

Stable fields:
- `generated_at`
- `window_days`
- `total_learnings`
- `due_for_review`
- `validated_total`
- `promoted_total`
- `recent_captures`
- `recent_validations`
- `recent_promotions`
- `skill_candidates_pending`
- `skill_improvements_pending`
- `recommended_actions`

Design rule:
Learning should be inspectable by humans and automation. Status is for current state. Digest is for impact over time.

## 3) CLI expectations

### Unified Ghost CLI
- `ghost_cli.py` is the product-facing consolidated CLI over stable Ghost surfaces
- current stable groups:
  - `ghost_cli.py recall ...`
  - `ghost_cli.py capture ...`
  - `ghost_cli.py user-model ...`
  - `ghost_cli.py learning ...`
  - `ghost_cli.py context show`

Design rule:
New user-facing Ghost command surfaces should prefer the unified CLI first, then later packaging/install wrappers can map onto it.

### Recall
- `ghost_unified_recall.py recall ... --json`
- `ghost_unified_recall.py report ... --json`
- default text output stays human-readable

### Learning
- `ghost_learning_loop.py status --json`
- `ghost_learning_loop.py digest --json`
- default text output stays Telegram/terminal friendly

## 4) Future extension points

## 4) Execution-state / session context contract

Implemented in:
- `scripts/ghost_core/contracts.py`
- `scripts/ghost_core/adapters/session_context.py`
- `scripts/ghost_core/defaults.py`

Stable fields:
- `focus`
- `blockers`
- `next_actions`
- `commitments_due`

CLI surface:
- `ghost_session_context.py show`
- `ghost_session_context.py show --json`

Design rule:
This is Ghost's layer-2 view of current work state, derived from Ghost-owned files like `ACTIVE_WORK.md` and memory sources. It should summarize work context, not replace OpenClaw sessions/runtime state.

## 5) Future extension points

These are the next stable Ghost-core interfaces worth formalizing:
- Ghost health report contract
- proactive signal contract (heartbeat / due / stale / blocked)

## Rule of thumb

If a new feature needs runtime plumbing, Ghost should call OpenClaw.
If a new feature changes how Ghost remembers, learns, prioritizes, or explains work, it belongs in Ghost core.
