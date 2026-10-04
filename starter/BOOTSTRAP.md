# Ghost Brain setup checklist

1. Configure OpenClaw using its own supported controls. Ghost does not configure the gateway, accounts, models, channels or approvals.
2. Review your existing `AGENTS.md`. If it already existed at install time, merge the relevant packaged guidance yourself; it was not overwritten. Preserve your security and project rules.
3. Choose knowledge ownership: a configured Obsidian vault is canonical; otherwise use an agreed local memory destination. Review `memory/reference/SECOND-BRAIN.md`. No connector or sync service was installed.
4. From the repository, run `bash test.sh` for default file checks. This does not prove runtime behavior.
5. Try a harmless capture and recall in an approved destination; inspect the readback. Use `/audit` for a bounded review of observed assistant behavior.

The default install adds four skills and generic guidance only. No schedules, indexes, Python dependencies, persona files or credentials are created. Use existing native OpenClaw capabilities and Skill Workshop where available.

For an older Ghost installation, review legacy scripts, skills and schedules separately. The installer does not disable or migrate them. Do not run automatic promotion or local sync alongside a new canonical workflow without reviewing ownership and effects.
