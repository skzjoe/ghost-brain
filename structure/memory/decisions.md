# Decision Journal

Important decisions with context and reasoning. Auto-appended by Ghost when significant decisions are made.

Format: `[YYYY-MM-DD] Decision — Reasoning (source)`

**Dedup rule**: before appending, check if the same decision already exists (by content, not date). Skip if duplicate.

---

## Architecture / Stack
<!-- Example entries — replace with your own -->
- [2026-01-15] Use Prisma v6 over v7 — v7 connection URL handling adds unnecessary complexity for our use case. (dev experience)
- [2026-01-10] PostgreSQL over MySQL for new projects — better JSON support, extensions ecosystem. SQLite for local-only tools. (architecture review)

## Workflow / Operations
<!-- Example entries — replace with your own -->
- [2026-01-12] Sub-agents auto-spawn for read-only tasks — notify user but don't ask permission. Write/external actions still need approval. (efficiency policy)
- [2026-01-08] Daily notes over MEMORY.md for session details — MEMORY.md stays compact (<6KB), details go to daily notes. (token efficiency)

## Business / People
<!-- Example entries — replace with your own -->
- [2026-01-05] Flat monthly retainer over hourly billing for support contracts — predictable revenue, less admin overhead. (pricing discussion)
