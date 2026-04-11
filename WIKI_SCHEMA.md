# WIKI_SCHEMA.md - Canonical LLM Wiki Schema

Purpose: define one durable, agent-agnostic operating model for maintaining a markdown wiki from raw notes and source material.

This file is the single source of truth for wiki behavior. Agent-specific docs should reference it instead of re-defining wiki rules.

## 1) Operating model

The wiki has three layers:

1. Raw sources - immutable source material such as transcripts, exports, screenshots, clipped docs, and notes captured from outside the wiki.
2. Wiki - maintained markdown pages that summarize, connect, compare, and synthesize knowledge from raw sources.
3. Schema - this document. It defines structure, workflows, update rules, and quality bars.

Core principle: do not re-derive everything from raw sources on every question. Read, compile, connect, maintain, and reuse.

## 2) Goals

Optimize for:
- durable knowledge accumulation
- strong cross-linking
- low maintenance overhead
- traceability back to sources
- easy navigation in markdown-based viewers
- compatibility across multiple agents

## 3) Folder conventions

Use these conventions unless the local project explicitly defines a stronger one.

### Generic layout
- `raw/` - immutable source material
- `wiki/` - compiled wiki pages
- `wiki/index.md` - content-oriented catalog of wiki pages
- `wiki/log.md` - append-only chronological operations log
- `wiki/projects/` - project pages
- `wiki/people/` - people pages
- `wiki/topics/` - concept, issue, system, or theme pages
- `wiki/sources/` - source summary pages
- `wiki/decisions/` - durable decision pages
- `wiki/syntheses/` - comparisons, analyses, and higher-level synthesis pages

### Ghost Brain-friendly layout
If the local workspace already keeps its canonical memory under another top-level folder, reuse that structure instead of creating a parallel wiki tree.

Recommended mapping in memory-centric layouts:
- `memory/YYYY-MM-DD.md` - capture layer, daily logs, session summaries
- `memory/projects/` - canonical project pages
- `memory/people.md` or `memory/people/` - canonical people register
- `memory/decisions.md` or `memory/decisions/` - canonical decision register
- `memory/topics/` - recurring topics, systems, issues, workflows, themes
- `memory/syntheses/` - reusable analyses, comparisons, and answers worth keeping
- `memory/wiki-index.md` - content-oriented catalog for the compiled layer
- `memory/wiki-log.md` - append-only chronological wiki maintenance log

Rule: prefer the existing canonical local structure over creating a duplicate tree.

## 4) Update policy

When new material arrives, update existing pages before creating new ones.

Update priorities:
1. source summary page for the new material
2. directly affected entity pages
3. related synthesis pages
4. canonical index page
5. canonical wiki log

When information conflicts with the current wiki:
- preserve the older claim if it still matters historically
- add the new claim
- mark the relationship clearly: contradicts, refines, supersedes, or remains unresolved

## 5) Ingest rule

A mirrored daily note sync into another vault is only a transport step. It does not count as wiki ingest by itself.

Only update ingest trackers when actual extraction, compilation, or canonical page updates were performed.
