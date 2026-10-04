---
name: remember
description: "Save a requested durable note using the existing capture workflow and configured canonical destination."
user-invocable: true
---

# /remember

Parse the requested note. If empty, ask what to remember in the user's language.

Read and follow `skills/ghost-capture/SKILL.md` for destination resolution, duplicate checking, scoped write and readback. This is the same capture workflow, not a second memory pipeline. If that skill is unavailable, report the missing dependency rather than falling back to a legacy script.

Preserve the user's meaning. Do not turn a correction or an ordinary successful task into automatic skill creation. Reusable procedure work belongs in native Skill Workshop when available, under its approval policy; notes belong in the configured knowledge store.
