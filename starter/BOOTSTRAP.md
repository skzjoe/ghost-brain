# Ghost Brain — Bootstrap Checklist

Get Ghost Brain running on top of an existing OpenClaw installation.

## Prerequisites

- [ ] **OpenClaw installed and configured** — `openclaw setup`
- [ ] **At least one channel connected** — `openclaw channels list`
- [ ] **Gateway running** — `openclaw gateway start`

If any prerequisite fails, fix it with OpenClaw first:
```
openclaw doctor --fix
openclaw status
```

## Ghost Layer Setup

### 1. Persona & Identity
- [ ] Edit `SOUL.md` — define your agent's personality and voice
- [ ] Edit `IDENTITY.md` — name, emoji, avatar
- [ ] Edit `USER.md` — describe yourself (name, role, timezone, preferences)

### 2. Memory Seed
- [ ] Edit `MEMORY.md` — add your initial context (work, projects, preferences)
- [ ] Edit `ACTIVE_WORK.md` — list current workstreams

### 3. Operating Rules
- [ ] Review `AGENTS.md` — adjust operating rules to your style
- [ ] Review `GHOST_PLAYBOOK.md` — response patterns and fast lanes
- [ ] Review `GHOST_PRODUCT_PLAN.md` — understand the 3-layer architecture

### 4. Verify
- [ ] Run `/health` — check Ghost layer is operational
- [ ] Run `/audit` — get a baseline system score
- [ ] Run `/onboard` — interactive guided setup (optional, fills in the above)

## Directory Structure

```
workspace/
├── SOUL.md               # Your agent's personality
├── IDENTITY.md           # Name, emoji, avatar
├── USER.md               # About the human
├── MEMORY.md             # Long-term context
├── AGENTS.md             # Operating rules
├── ACTIVE_WORK.md        # Current workstreams
├── GHOST_PLAYBOOK.md     # Response patterns
├── GHOST_PRODUCT_PLAN.md # Product architecture
├── HEARTBEAT.md          # Heartbeat config
├── memory/               # Daily notes + second-brain files
├── .learnings/           # Execution-quality learnings
├── scripts/              # Ghost core scripts
├── skills/               # Ghost skills (ghost-*)
└── tests/                # Automated tests
```

## Recommended Cron Jobs

After setup, configure these cron jobs via `openclaw cron add`:

| Name | Schedule | Purpose |
|---|---|---|
| Heartbeat Pulse | Every 2h | Catch urgent signals |
| Morning Briefing | 08:00 daily | Day priorities + calendar + email |
| Morning Learning Review | 08:15 daily | Spaced repetition for learnings |
| EOD Session Log | 23:00 daily | Auto-summarize daily work |
| Weekly Memory Distill | 21:00 Sunday | Weekly review + promotion |
| Weekly Backup | 20:00 Sunday | Workspace backup |

## What's NOT Included

This starter package is the **generic Ghost product layer**. It does not include:
- Obsidian vault sync (workspace-specific paths)
- ERPNext/Frappe integrations
- Company document templates
- Meta Ads workflows
- Personal secrets or credentials

These can be added as **Layer 3 workspace adapters** — see `GHOST_PRODUCT_PLAN.md`.

## Next Steps

1. Start chatting with your agent
2. Use `/remember` to capture important information
3. Use `/recall` to search across all memory layers
4. Use `/logs` at end of each session to persist work
5. After a week, run `/weekly` for your first review
