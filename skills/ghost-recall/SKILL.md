---
name: recall
description: "Find relevant evidence using available native retrieval, then verify important claims at the configured source."
user-invocable: true
---

# /recall

1. Parse the question; ask for a topic only if none is supplied.
2. Read workspace knowledge instructions and `memory/reference/SECOND-BRAIN.md`. Respect private, team and customer boundaries.
3. Prefer available native memory/search tools and their actual schemas. Search narrowly, then read only the needed source passages. When Obsidian is configured, verify material claims at the canonical vault source; an index or local status view is only a retrieval aid.
4. Use session-history tools only when the question needs wording or chronology. Do not scan raw transcript stores or unrelated personal notes by default.
5. Answer concisely with source references and uncertainty. Distinguish no search hit from evidence that something did not happen. If tools or source access are missing, name the gap; do not claim exhaustive recall.

Recall is read-only. Do not index, sync, promote or write notes as a side effect, and do not invoke legacy local-memory scripts automatically. Use already-supplied context when it answers the question without retrieval.
