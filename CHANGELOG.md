# Changelog

## Unreleased

### Added
- **Auto Skill Pipeline** (`scripts/ghost_auto_skill.py`) — immune-system skill lifecycle: detect → create → match → record → improve → auto-promote/retire. Zero human review needed. Skills earn active status through real usage (3+ successes ≥90%) and auto-retire when failing (<50% after 3 uses). See `AUTO-SKILL.md`
- `AUTO-SKILL.md` — documentation for the auto skill pipeline
- `scripts/ghost_error_classifier.py` — 12-category structured error taxonomy with retryable flags + recovery hints. Logs `[ERR-YYYYMMDD-NNN]` format entries to `.learnings/ERRORS.md`
- `scripts/ghost_todos.py` — intra-session todo store (JSON-backed, survives context compression). Commands: add, done, list, status, clear
- `scripts/obsidian_merge.py` — shared section-aware merge engine with source attribution (`*(Ghost)*` markers) and data-loss protection (85% size sanity check, atomic writes)
- `BEHAVIORAL-RULES.md` — on-demand behavioral rules (model routing, error handling, todos, vault writes). Read only when relevant, not at startup
- `memory/now.md` template for a shared 24–72 hour execution lens across briefing, heartbeat, EOD, and weekly review
- `scripts/run_memory_pipeline.sh` wrapper for automation-safe Memory DB maintenance

### Changed
- `scripts/obsidian_push_daily.sh` — refactored to use `obsidian_merge.py` (merge-not-overwrite policy). Configurable via env vars (`GHOST_DEST_DAILY`, `GHOST_VAULT`)
- Heartbeat pulse — deadline-aware follow-up threshold (5d if deadline ≤7d, else 7d) + urgent alert format
- Playbook trimmed (~19KB → ~17KB) by splitting behavioral rules into separate on-demand file
- Memory DB docs now distinguish interactive direct script use from cron/automation wrapper use
- Second Brain docs now document NOW layer usage and stricter follow-up normalization rules
- Playbook now includes follow-up hygiene guidance and short-horizon refresh behavior
- Cron docs and prompts now prefer wrapper-based Memory DB runs and acknowledge fully-qualified messaging targets in automation
- Install flow now ships `now.md`, `run_memory_pipeline.sh`, `detect_active_lanes.py`, and `generate_context_bridge.sh`
- Follow-up skill guidance now suggests re-scoping vague or non-closure-oriented items

### Vault Safety
- Merge-everywhere policy: all Obsidian vault writes must be merge/append, never blind overwrite
- Git safety snapshots before every write (recoverable via `git checkout`)
- Source attribution on appended content (HTML comments) for multi-agent traceability
- Size sanity check aborts if merged result < 85% of original (prevents silent data loss)

## v1.0.0 — 2026-03-17

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

## [1.1.0] — 2026-04-12

### Added
- GHOST_PRODUCT_PLAN.md — Ghost Product Master Plan v1 (3-layer architecture)
- starter/ — complete starter distribution with templates, install.sh, and bootstrap checklist
- /health skill — consolidated Ghost product health view (memory, learning, execution state, proactive, capture)
- /audit Part 14 — Product Health dimension (13 dimensions total)
- /recall skill — unified memory search
- /remember skill — smart capture routing
- /learnings skill — learning loop status
- ghost_learning_loop.py — reflect, promote, detect skill candidates
- ghost_unified_recall.py — unified search + smart capture + user model
- ghost_usage_insights.py — session/activity analytics
- model_router.py — advisory model routing (cheap/strong/heavy)

### Changed
- /health now reports Ghost-layer concerns only (no overlap with openclaw status/doctor)
- /audit scoring updated for 13 dimensions including Product Health
- README.md in starter/ has full command reference and architecture diagram

