# Knowledge ownership

## Resolve the source before using it

1. Read the workspace's existing knowledge instructions and configured destinations.
2. If an Obsidian vault is configured, read its schema. The vault is the canonical knowledge store; do not guess paths or create a parallel wiki.
3. Without a vault, follow the existing local memory convention. If none exists, agree on a destination with the user before the first write.

## Capture

Capture durable facts, decisions and requested notes within the user's scope. Check the destination for duplicates, preserve unrelated content, and read back the saved entry. Report the actual path and whether it is canonical or only local staging. An unavailable vault is a blocker, not permission to claim a completed sync.

When local staging is authorized, label it pending; merge and read back the canonical entry before declaring completion. Do not invent a background sync path.

## Recall

Use available native memory/search tools first, then inspect the relevant source passage. Search results and local indexes are retrieval aids, not independent authority. Use transcript history only when wording or chronology requires it, and keep private/personal context separate from team or customer contexts.

If tools, access or evidence are missing, state the gap. Never equate absence of a search hit with proof that an event did not happen.

## Derived views and compatibility

`ACTIVE_WORK.md`, local follow-up summaries and SQLite indexes are derived when a canonical vault exists. Keep source references rather than creating a second authority. Bootstrap files are operating instructions, not a knowledge database.

The legacy Python CLIs and push scripts are retained compatibility utilities. They do not implement automatic canonical-vault routing or conflict-safe migration. Review their destinations and effects before any use; do not run them merely because they are present.
