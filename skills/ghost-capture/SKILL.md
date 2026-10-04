---
name: capture
description: "Save a requested decision, idea, commitment, follow-up or contact to the configured knowledge store, with readback."
user-invocable: true
---

# /capture

Usage: `/capture decision: use the existing database for the prototype`

1. Parse the type and content. Supported types include decision, idea, commitment, follow-up and person. Ask only if ambiguity affects the destination or meaning; do not invent names, dates or obligations.
2. Read existing workspace knowledge instructions and `memory/reference/SECOND-BRAIN.md`. If Obsidian is configured, read its schema and resolve the canonical destination. Otherwise use the agreed local convention; if none exists, ask where to save before writing.
3. Check the destination for duplicates. Update an existing entry only within the user's requested scope; otherwise ask when a conflict requires a decision.
4. Use available approved file/knowledge tools to preserve unrelated content and write the entry. Do not interpolate user text into shell commands. Keep private facts in their intended context, not public skills or repositories.
5. Read back the saved entry. Confirm the actual path, short summary and whether it is canonical or local staging. If the write or readback fails, report the exact gap rather than claiming completion.

A configured but unavailable vault is a blocker. Local staging requires authorization and must be labeled pending; do not claim it synced. Do not call legacy capture/index/promotion scripts merely because they exist, or create a second authoritative copy in a daily note.
