# 👻 Ghost Brain

**A small assistant workflow layer for [OpenClaw](https://github.com/openclaw/openclaw).**

Ghost provides capture, recall and evidence-based review instructions. OpenClaw owns runtime, tools, permissions, sessions, orchestration and scheduling. Use native Skill Workshop for reusable skill work when available, under its approval policy—not a second automatic promotion pipeline.

## Quick start

Start with an existing, configured OpenClaw workspace. Review the files before installing:

```bash
git clone https://github.com/skzjoe/ghost-brain.git
cd ghost-brain
bash install.sh
bash test.sh
```

Set `OPENCLAW_WORKSPACE` if your workspace is elsewhere. Bash and standard file utilities are sufficient for the default install. It does **not** run OpenClaw, install Python packages, index notes, configure a vault, create schedules or touch credentials.

### What the default installs

| Files | Purpose |
|---|---|
| Four skills: `/audit`, `/capture`, `/recall`, `/remember` | Behavioral review and source-aware memory workflows |
| `memory/reference/PLAYBOOK.md` | Small operating rules and completion boundaries |
| `memory/reference/SECOND-BRAIN.md` | Canonical-source and local-staging rules |
| `AGENTS.md`, `BOOTSTRAP.md` (only if missing) | Generic routing and setup checklist |

Existing files are skipped. `--force` updates packaged skills/reference docs, preserving unrelated files and never replacing existing `AGENTS.md` or `BOOTSTRAP.md`. Back up customizations before using it. If you already have workspace instructions, merge the relevant guidance from [the template](starter/templates/AGENTS.md); the installer does not merge instructions for you. `starter/install.sh` delegates to the same installer from a full clone.

## Everyday use

- **Capture:** ask to remember something, or use `/capture decision: …`. The skill resolves the configured destination, checks duplicates, writes and reads it back.
- **Recall:** use `/recall <question>`. Prefer available native retrieval, verify material claims at their source, and identify missing evidence.
- **Audit:** use `/audit` to review observed behavior across **Understand / Complete / Proactive / Trustworthy / Simple**. Missing proof is not failure; installed files and passing tests are not proof of assistant quality.

These are instructions executed by your configured model and available tools, not an always-on service or a guarantee of automatic capture. Command discovery depends on your OpenClaw setup. Nothing runs merely because a file was copied.

## One canonical knowledge store

When an Obsidian vault is configured, it is canonical. Read its schema and use its approved tools/paths. Local notes are staging until merged and read back; local indexes and active-work summaries are derived. Do not maintain competing authoritative copies.

Without a configured vault, use the workspace's existing memory convention. If none exists, agree on a local destination first. The default install contains **no vault connector, sync service or migration**. The older Python capture CLI writes local files and does not automatically route to Obsidian.

## Existing installations and legacy tools

Nothing is removed or disabled automatically. Existing scripts, skills and schedules remain until you review them. Avoid running legacy promotion/sync routines alongside native Skill Workshop or a canonical-vault workflow.

The older local-memory/SQLite/learning/research bundle remains available for compatibility:

```bash
bash install.sh --legacy
# Explicit, optional compatibility setup only, after reviewing prompts and dependencies:
bash setup-crons.sh --legacy
```

The legacy installer retains package installation and local indexing behavior. It needs Python 3.10+; SQLite/vector features require `sqlite-vec`. Optional Gemini embeddings use `google-genai` and may send note content to the configured provider. Review that privacy boundary before enabling it. No new dependency is required by the default install.

Existing `scripts/ghost_cli.py` entrypoints and tests remain; they are local compatibility tools, not replacements for native runtime orchestration. [AUTO-SKILL.md](AUTO-SKILL.md), [CRON-PATTERNS.md](CRON-PATTERNS.md), older product plans, release notes and learning docs describe that legacy bundle, not today's recommended setup. The bulk cron helper is not idempotent; inspect existing jobs first. Some prompts require your own adapters (for example a backup script).

## Verification

- `bash test.sh` checks only default installed files, without invoking runtime or memory tools.
- `bash test.sh --legacy` runs the older compatibility smoke checks; it may open/create a local database.
- The Python tests cover local code/contracts, not live model behavior or platform compatibility. Run them with an isolated HOME, workspace and session root; some legacy tests write fixtures and research state:

```bash
sandbox=$(mktemp -d)
mkdir -p "$sandbox/home" "$sandbox/workspace" "$sandbox/sessions"
env -i PATH="$PATH" HOME="$sandbox/home" \
  OPENCLAW_WORKSPACE="$sandbox/workspace" \
  OPENCLAW_SESSIONS_ROOT="$sandbox/sessions" GHOST_EMBEDDING_PROVIDER=local \
  python3 -m pytest tests/ -q -p no:cacheprovider
```

Use an interpreter with pytest already installed. Live OpenClaw/model behavior must be verified separately using observed requests, tool receipts and delivery evidence; no blanket version-compatibility or quality score is claimed.

## Removal

Remove only files you know this installer added, after checking for customizations. Keep your notes. Use approved OpenClaw controls to review/remove any separately configured jobs. No runtime configuration is changed by the default installer.

MIT licensed. Built with Ghost 👻
