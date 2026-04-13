# Ghost Brain v1.3.0 Release Notes

Date: 2026-04-13
Tag: `v1.3.0`

## Summary

Ghost Brain v1.3.0 makes the product substantially more usable as a day-to-day second brain. It adds transcript-aware conversation recall, uncaptured-work guardrails, markdown-to-SQLite memory-sync checks, stronger local skill matching, and a final routing/ranking polish pass so transcript recall is useful without polluting default recall behavior.

## Highlights

### 1. Conversation recall is now a real product surface
- `scripts/ghost_conversation_memory.py` adds transcript search and recent-session recovery over OpenClaw session logs
- `ghost_cli.py conversation search|recent` exposes the surface directly for interactive and automation use
- transcript recall strips metadata wrappers and internal-context noise before ranking results

### 2. Recall routing is conservative by default
- default recall still prefers structured memory, daily notes, and learnings
- transcript history is used only when requested explicitly or when Ghost detects a transcript-seeking query and durable evidence is too weak
- recall reports now include routing metadata so source choice is visible and testable

### 3. Self-discipline and freshness gaps are closed
- `scripts/ghost_guardrails.py` detects uncaptured-work risk and can block `/new`-style resets when recent work has not been logged
- `scripts/ghost_memory_sync.py` verifies markdown↔SQLite freshness, drift, and orphaned rows instead of assuming Memory DB health
- session-context and working-memory surfaces now expose guardrail and memory-sync state directly

### 4. Local matching and transcript ranking are sharper
- `scripts/ghost_auto_skill.py` now uses weighted local matching instead of raw keyword overlap alone
- conversation search deduplicates repeated snippets, spreads top hits across sessions, and filters more single-term noise for multi-term queries

### 5. Public product surfaces are aligned
- README now documents recall-routing examples for default recall, explicit transcript search, and explicit transcript-only recall
- changelog and release metadata now reflect the post-`v1.2.0` public state on `main`

## Validation
- `bash -n install.sh`
- `bash -n starter/install.sh`
- `bash -n test.sh`
- `/home/linuxbrew/.linuxbrew/bin/python3 -m pytest tests -q` → `177 passed`

## Upgrade notes
- markdown memory remains the canonical store
- Memory DB remains a derived/indexed layer and should be maintained with the provided pipeline wrapper
- transcript recall stays conservative by design; use explicit conversation search when wording/history matters
- no breaking installer/layout changes are required for existing users
