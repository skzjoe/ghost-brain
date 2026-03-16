# Changelog

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
