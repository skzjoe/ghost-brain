# Changelog

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
- Compatibility shim retained: `scripts/sr_review.py` forwards to `scripts/learning_review.py`
- Gateway watchdog script for OS-level monitoring

### Infrastructure
- MIT License
- Example outputs (audit, daily note, auto-capture)
- All cron scripts timezone/city-generic with `{{USER_NAME}}` placeholder
