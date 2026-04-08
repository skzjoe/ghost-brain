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

For interactive local experiments, calling the script directly is fine.

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
python3 scripts/ghost_memory_db.py query decision --project myproject --days 30

# Knowledge graph — auto-link items by content
python3 scripts/ghost_memory_db.py links --rebuild

# Find duplicates
python3 scripts/ghost_memory_db.py dedup

# Find and merge duplicates
python3 scripts/ghost_memory_db.py dedup --merge

# Full maintenance pipeline (index→dedup→links→report)
python3 scripts/ghost_memory_db.py pipeline

# Analytics dashboard
python3 scripts/ghost_memory_db.py stats

# Export as JSON (for automation)
python3 scripts/ghost_memory_db.py search "query" --json
python3 scripts/ghost_memory_db.py stats --json
python3 scripts/ghost_memory_db.py export decision --json

# Raw SQL
python3 scripts/ghost_memory_db.py sql "SELECT item_type, COUNT(*) FROM items GROUP BY item_type"
```

For automation and cron, prefer the wrapper so the runtime picks a Python interpreter that actually has `sqlite-vec` installed:

```bash
bash scripts/run_memory_pipeline.sh pipeline
bash scripts/run_memory_pipeline.sh check
bash scripts/run_memory_pipeline.sh smoke
bash scripts/run_memory_pipeline.sh stats
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

## Features

### Knowledge Graph
Auto-links items by analyzing content:
- **documented_in** — decisions linked to daily notes from the same date
- **relates_to** — learnings linked to decisions with matching keywords
- **mentioned_in** — people linked to items that mention their name
- **tracks** — follow-ups/commitments linked to related decisions and notes

### Deduplication
Finds potential duplicates using Jaccard word similarity (default threshold: 85%).
Can auto-merge: keeps the item with more content, removes the other.

### Analytics Dashboard
- Item counts by type, area, status
- Activity chart (last 14 days)
- Top tags
- Date range
- Pending duplicates count

### Python API
```python
from ghost_memory_db import GhostMemory

mem = GhostMemory()
item_id = mem.add_item("decision", "Use SQLite", "Reasoning...", "memory/decisions.md")
results = mem.search_hybrid("database choice")
links = mem.get_links(item_id)
stats = mem.get_analytics()
mem.close()
```

## Schema

- **items** — core knowledge items with type, title, content, dates, status
- **tags** + **item_tags** — many-to-many tag system
- **links** — bi-directional knowledge graph with confidence scores
- **duplicates** — detected duplicate pairs with similarity scores
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

For scheduled jobs, use the wrapper instead of raw `python3`:
```bash
bash scripts/run_memory_pipeline.sh pipeline
```

This keeps the DB in sync with your markdown files while avoiding interpreter drift across environments.

## Architecture decisions

- **Single file** — `.local/ghost_memory.db` — easy to backup, portable
- **No server** — embedded SQLite, runs in-process
- **FTS5 + sqlite-vec** — hybrid search without external services
- **Incremental indexing** — only re-processes changed files (hash-based)
- **Parsers per file type** — each second-brain file has a dedicated parser
- **Zero PII in code** — all personal data lives in the markdown files, not the scripts
