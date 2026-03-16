# Changelog

## v1.3.0 — 2026-03-16

### Added
- **SQLite + sqlite-vec Memory DB** (`scripts/ghost_memory_db.py`)
  - Indexes all second-brain markdown files into a searchable SQLite database
  - Full-text search (FTS5) + vector similarity search (sqlite-vec) in a single `.db` file
  - Structured queries: filter by type, project, date range, status
  - Incremental indexing (hash-based change detection)
  - Knowledge graph tables (tags, links) for future bi-directional relationships
  - Zero infrastructure — single file at `.local/ghost_memory.db`
- **Spaced Repetition** (`scripts/sr_review.py`)
  - SM-2-inspired interval ladder: 1 → 3 → 7 → 14 → 30 → 60 → 120 days
  - Priority-weighted resurfacing (critical items appear 2× more often)
  - Graduation system — mastered items stop surfacing
  - Cron integration — surfaces 3 learnings/day after morning summary
  - JSON state file, no external dependencies
- `MEMORY-DB.md` — documentation for the SQLite memory layer
- `SPACED-REPETITION.md` — documentation for the SR system

### Changed
- README updated with Memory DB and Spaced Repetition features
- Knowledge docs count: 5 → 7
- "How it works" flow diagram updated with SR and Memory DB stages

## v1.2.0 — 2026-03-16

### Added
- `/audit` Part 13 — 4-pillar improvement suggestions (Productive, Efficient, Proactive, Critique)
- Product Launch / Sales fast lane in PLAYBOOK.md
- 8 domain-specific fast lanes (ERP, Docs, Debug, Decision, Product Launch, Negotiation, Calendar, Strategy)
- `examples/` directory with real output samples (audit, daily note, auto-capture)
- Interactive `setup-crons.sh` — asks timezone, model, Obsidian preference
- Realistic example entries in all 5 second-brain templates
- MIT LICENSE file
- `.gitignore`
- This CHANGELOG

### Changed
- Cron scripts de-hardcoded — timezone and city references now generic
- `setup-crons.sh` — interactive prompts replace hardcoded values
- README updated with example links, interactive setup docs

### Removed
- Build artifacts (handler.js/ts, extract-skill.sh, .clawhub/, _meta.json)

## v1.1.0 — 2026-03-16

### Added
- 7 new skills: `/capture`, `/conflicts`, `/export`, `/fastlanes`, `/logs`, `/onboard`, `/weekly`
- `/health` upgraded (comprehensive gateway, cron, security checks)
- Heartbeat system with bash-first 0-token design
- Gateway watchdog script

## v1.0.0 — 2026-03-15

### Added
- Initial release: 16 skills, 10 cron patterns, 5 knowledge docs
- Self-improving agent with learnings lifecycle
- 12-dimension audit with weighted scoring
- Second brain (decisions, people, ideas, commitments, follow-ups)
- Token efficiency rules and rate limiting patterns
- install.sh with safe non-destructive install
