# Memory DB — SQLite + sqlite-vec

A structured memory layer that indexes your second-brain markdown files into a searchable SQLite database with vector embeddings.

## Why

Markdown files are great for human-readable memory, but as your brain grows:
- **Recall accuracy drops** — semantic search on flat files misses edge cases
- **Structured queries are impossible** — "all decisions about X in the last 30 days" requires LLM grep
- **Scale concerns** — hundreds of daily notes + learnings = slow context loading

Memory DB solves this with a single `.db` file that provides both **full-text search** (FTS5) and **vector similarity search** (sqlite-vec) — zero infrastructure, zero servers.

## Setup

```bash
pip install sqlite-vec
```

That's it. SQLite is built into Python. No Docker, no servers.

## Usage

```bash
# Full index (first time or after major changes)
python3 scripts/ghost_memory_db.py index

# Incremental index (only changed files — fast)
python3 scripts/ghost_memory_db.py index --incremental

# Search (hybrid: FTS + vector)
python3 scripts/ghost_memory_db.py search "VAT configuration"

# Full-text search only
python3 scripts/ghost_memory_db.py search "VAT" fts

# Structured query: decisions about a project in the last 30 days
python3 scripts/ghost_memory_db.py query decision --project AWC --days 30

# Raw SQL
python3 scripts/ghost_memory_db.py sql "SELECT item_type, COUNT(*) FROM items GROUP BY item_type"

# Stats
python3 scripts/ghost_memory_db.py stats
```

## What gets indexed

| Source | Item types |
|---|---|
| `memory/decisions.md` | decision |
| `memory/people.md` | person |
| `memory/ideas.md` | idea |
| `memory/commitments.md` | commitment |
| `memory/follow-ups.md` | follow-up |
| `.learnings/LEARNINGS.md` | learning |
| `.learnings/ERRORS.md` | error |
| `.learnings/domains/*.md` | learning |
| `.learnings/projects/*.md` | learning |
| `memory/YYYY-MM-DD.md` | daily_note (per section) |
| `memory/weekly/*.md` | daily_note |

## Schema

- **items** — core knowledge items with type, title, content, dates, status
- **tags** + **item_tags** — many-to-many tag system
- **links** — bi-directional knowledge graph (relates_to, supports, contradicts, etc.)
- **items_fts** — FTS5 full-text search index
- **items_vec** — sqlite-vec vector embeddings for semantic search
- **file_index** — tracks file hashes for incremental indexing

## Embeddings

Default: **local hash-based** embeddings (zero-cost, offline, deterministic). Good for FTS-augmented search and basic similarity.

For production-quality semantic search, set:
```bash
export GHOST_EMBEDDING_PROVIDER=openai  # or gemini
export GHOST_EMBEDDING_API_KEY=sk-...
```
(Requires implementing the API call in `get_embedding()` — the hook is ready.)

## Cron integration

Add to your EOD or morning summary cron:
```bash
python3 scripts/ghost_memory_db.py index --incremental
```

This keeps the DB in sync with your markdown files automatically.

## Architecture decisions

- **Single file** — `.local/ghost_memory.db` — easy to backup, portable
- **No server** — embedded SQLite, runs in-process
- **FTS5 + sqlite-vec** — hybrid search without external services
- **Incremental indexing** — only re-processes changed files (hash-based)
- **Parsers per file type** — each second-brain file has a dedicated parser
- **Zero PII in code** — all personal data lives in the markdown files, not the scripts
