# Changelog

## Unreleased

## [1.3.0] — 2026-04-13

### Added
- `scripts/ghost_conversation_memory.py`, `scripts/ghost_guardrails.py`, and `scripts/ghost_memory_sync.py` plus matching `ghost_cli.py` commands for transcript recall, uncaptured-work guardrails, and markdown↔SQLite drift checks
- Public pytest coverage for conversation recall, guardrails, memory sync, and the updated context/working-memory surfaces

### Changed
- `scripts/ghost_auto_skill.py` now uses weighted local matching instead of raw keyword overlap alone
- Conversation recall now keeps durable-memory sources first and only falls back to transcript history for transcript-seeking queries when primary evidence is weak
- Conversation-search ranking now deduplicates repeated snippets, spreads top hits across sessions, and filters more single-term transcript noise on multi-term queries
- `scripts/ghost_session_context.py` and `scripts/ghost_working_memory.py` now surface guardrail and memory-sync signals
- Conversation recall stays explicit and opt-in instead of being mixed into default recall-all behavior
- Root installer and smoke test now provision and verify the new product scripts

### Fixed
- Transcript recall now strips untrusted metadata wrappers and internal-context blocks before ranking snippets
- Root and starter installers now copy `BOOTSTRAP.md` into the workspace and align starter packaging with repo-root layouts
- Public install/docs now match the actually shipped command surface (`/recall`, `/remember`, `/learnings`) and no longer advertise `/auto-skills` as a slash command
- Product docs no longer carry stale skill-count, audit-numbering, or old test-count references

## [1.2.0] — 2026-04-13

### Added
- **Auto Skill Pipeline** (`scripts/ghost_auto_skill.py`) — immune-system skill lifecycle: detect → create → match → record → improve → auto-promote/retire. Zero human review needed. Skills earn active status through real usage (3+ successes ≥90%) and auto-retire when failing (<50% after 3 uses). See `AUTO-SKILL.md`
- `AUTO-SKILL.md` — documentation for the auto skill pipeline
- `scripts/ghost_error_classifier.py` — 12-category structured error taxonomy with retryable flags + recovery hints
- `scripts/ghost_todos.py` — intra-session todo store (JSON-backed, survives context compression)
- `scripts/obsidian_merge.py` — shared section-aware merge engine with source attribution and data-loss protection
- `BEHAVIORAL-RULES.md` — on-demand behavioral rules for model routing, vault safety, error handling, and todos
- `memory/now.md` template for a shared 24–72 hour execution lens across briefing, heartbeat, EOD, and weekly review
- `scripts/run_memory_pipeline.sh` wrapper for automation-safe Memory DB maintenance
- `scripts/memory_content_scanner.py` — content safety scanning and duplicate/size guardrails for memory writes
- `scripts/ghost_cli.py` — unified product-facing CLI over recall, learning, context, working-memory, and research surfaces
- `scripts/ghost_core/` — additive Ghost core package with contracts, ports, defaults, workspace resolver, and adapters
- `scripts/ghost_session_context.py` — Ghost-owned execution-state snapshot CLI
- `scripts/ghost_working_memory.py` — briefings and due/stale follow-up triage
- Ghost research stack: `ghost_research.py`, `ghost_research_lib.py`, `ghost_eval.py`, `ghost_regression.py`, `ghost_safety_benchmark.py`, `ghost_trajectory_log.py`, `ghost_continuity_benchmark.py`, `ghost_dashboard.py`, `ghost_experiments.py`
- Release/interface docs: `GHOST_CORE_INTERFACES.md`, `GHOST_CORE_MIGRATION_NOTES.md`, `GHOST_CORE_CHANGELOG.md`, `GHOST_CORE_RELEASE_NOTES.md`, `GHOST_RESEARCH_STACK.md`
- Automated pytest coverage for Ghost core contracts/adapters, unified recall, session context, working memory, and research surfaces

### Changed
- `scripts/obsidian_push_daily.sh` now uses `obsidian_merge.py` (merge-not-overwrite policy) with configurable env vars
- Heartbeat pulse now uses deadline-aware follow-up thresholds and clearer urgent alert formatting
- Install flow now ships `now.md`, `run_memory_pipeline.sh`, `detect_active_lanes.py`, `generate_context_bridge.sh`, the Ghost core package, unified CLI, and research surfaces
- `scripts/ghost_unified_recall.py` now provides more explainable recall, related recall, capture tags, and cleaner automation output
- `scripts/ghost_learning_loop.py` now emits structured/state-aware automation surfaces and immediate review-state sync on capture
- `scripts/ghost_usage_insights.py` now supports command-log overrides and cleaner generic theme labels
- `README.md`, `starter/README.md`, `install.sh`, and `test.sh` updated to reflect the current product surface
- Public repo examples, fixtures, and reference files were scrubbed to generic/product-safe examples before release

### Safety & Reliability
- Merge-everywhere policy: all Obsidian vault writes must be merge/append, never blind overwrite
- Git safety snapshots before every vault write (recoverable via `git checkout`)
- Memory writes now have duplicate detection, size checks, and content scanning
- Research storage now uses atomic writes, locked JSONL appends, baseline validation, and manifest drift warnings
- Product repo got an explicit PII hygiene sweep before release

## [1.1.0] — 2026-04-12

### Added
- `GHOST_PRODUCT_PLAN.md` — Ghost Product Master Plan v1 (3-layer architecture)
- `starter/` — complete starter distribution with templates, install.sh, and bootstrap checklist
- `/health` skill — consolidated Ghost product health view (memory, learning, execution state, proactive, capture)
- `/audit` Product Health dimension added to the 13-dimension audit
- `/recall` skill — unified memory search
- `/remember` skill — smart capture routing
- `/learnings` skill — learning loop status
- `ghost_learning_loop.py` — reflect, promote, detect skill candidates
- `ghost_unified_recall.py` — unified search + smart capture + user model
- `ghost_usage_insights.py` — session/activity analytics
- `model_router.py` — advisory model routing (cheap/strong/heavy)

### Changed
- `/health` now reports Ghost-layer concerns only (no overlap with OpenClaw status/doctor)
- `/audit` scoring updated for 13 dimensions including Product Health
- `starter/README.md` has full command reference and architecture diagram

## [1.0.0] — 2026-03-17

**First stable release.** Ghost Brain has been in daily production use since February 2026. This release consolidates all features into a single installable package ready for distribution.

### Core Systems
- **5 Auto-Capture Systems** — decisions, people, ideas, commitments, follow-ups captured from normal conversation
- **Self-Learning Lifecycle** — errors → scoped learnings → domain patterns → global rules → archive
- **Learning Review** — interval ladder (1→3→7→14→30→60→120d), 3 learnings/day, priority-weighted
- **Memory DB** — SQLite + sqlite-vec, full-text + semantic vector search, zero infrastructure
- **Knowledge Graph** — auto-linked relationships (documented_in, relates_to, mentioned_in, tracks)

### Memory DB Features
- Gemini embedding-001 (256d) with auto-fallback to local hash
- Incremental indexing (hash-based change detection)
- Deduplication with word similarity matching
- Source tracking (daily_log, conversation, meeting, email, etc.)
- Temporal intelligence (stale detection, hot items, access tracking)
- Cross-session context bridge (dynamic startup context from DB)
- GhostMemory class API for programmatic use
- Full analytics dashboard, JSON output, export support
- Maintenance pipeline: `index → dedup → links → report`

### Commands (16)
- `/onboard` `/capture` `/logs` `/audit` `/health` `/weekly`
- `/projects` `/project` `/commitments` `/decisions` `/followups` `/ideas` `/people`
- `/fastlanes` `/conflicts` `/export`

### Automation (10 cron jobs)
- Morning Briefing (08:00) + Learning Review (08:15) + Commitment Alerts (08:30)
- EOD Session Log (23:00) with auto Memory DB re-index
- Obsidian Daily Sync (23:05, optional)
- Gateway Healthcheck (every 6h)
- Weekly Backup + Memory Distill + Weekly Report
- Monthly Note Archive

### Audit System
- 13-dimension scoring (boot chain, prompts, capture, memory, learning, proactive, obligations, efficiency, runtime, automation, resilience, security, improvement suggestions)
- 4-pillar improvement framework (Productive, Efficient, Proactive, Critique)
- Weighted Brain/Infra/Overall scoring

### Knowledge Docs (7)
- TOKEN-EFFICIENCY.md, SELF-LEARNING.md, PLAYBOOK.md, SECOND-BRAIN.md
- CRON-PATTERNS.md, MEMORY-DB.md, LEARNING-REVIEW.md

### Installation
- `install.sh` — non-destructive, auto-installs deps (sqlite-vec, google-genai), indexes memory, inits Learning Review
- `install.sh --force` — updates code files, never overwrites user data (`safe_copy_data()`)
- `setup-crons.sh` — interactive setup (timezone, model, Obsidian preference)
- Gateway watchdog script for OS-level monitoring

### Infrastructure
- MIT License
- Example outputs (audit, daily note, auto-capture)
- All cron scripts timezone/city-generic with `{{USER_NAME}}` placeholder
