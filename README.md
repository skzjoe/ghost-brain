# 👻 Ghost Brain

**AI Second Brain for OpenClaw** — self-learning, token efficiency, and automated routines that make your AI assistant smarter every day.

> Your AI forgets everything every session. Ghost Brain fixes that in 30 seconds.

## What it does

🧠 **Second Brain** — 5 auto-capture systems
- Decisions, people, ideas, commitments, follow-ups — all captured automatically from conversations

📝 **Self-Learning** — your AI learns from mistakes
- Errors logged once, never repeated. Patterns promoted to global rules automatically.

🔄 **Spaced Repetition** — learnings resurface automatically
- SM-2-inspired intervals ensure critical rules stick. Items graduate when mastered.

🗄️ **Memory DB** — SQLite + vector search for long-term memory
- Full-text search + semantic vector search in a single `.db` file. Zero infrastructure.

💰 **Token Efficiency** — save 30-50% on API costs
- Rate limiting, context management, output discipline rules

⏰ **12 Automated Routines**
- Morning brief, EOD summary, weekly distillation, commitment alerts, health checks, backups

🔧 **16 System Commands**
- `/onboard` — guided first-run setup
- `/capture` — quick-capture to the right brain file
- `/audit` `/health` `/weekly` `/logs`
- `/projects` `/project` `/commitments` `/decisions` `/followups` `/ideas` `/people`
- `/fastlanes` `/conflicts` `/export`

## See it in action

📋 [Full audit output](examples/audit-output.md) — 12-dimension scorecard + 4-pillar improvement suggestions
📝 [Daily note example](examples/daily-note.md) — what EOD auto-summary produces
🧠 [Auto-capture demo](examples/capture-in-action.md) — how Ghost captures decisions, people, commitments from normal chat

## Quick Install

```bash
git clone https://github.com/skzjoe/ghost-brain.git
cd ghost-brain
bash install.sh
```

Or download and extract:
```bash
tar -xzf ghost-brain.tar.gz
cd ghost-brain
bash install.sh
```

That's it. ~60 seconds. Automatically installs dependencies, indexes your memory, and initializes spaced repetition.

**Optional but recommended:** Set `GEMINI_API_KEY` for semantic search (free at [ai.google.dev](https://ai.google.dev)):
```bash
export GEMINI_API_KEY=your_key_here
bash install.sh
```
Without it, search still works using local embeddings.

## What gets installed

| Component | Count | Location |
|---|---|---|
| Skills | 16 | `~/.openclaw/workspace/skills/` |
| Knowledge docs | 7 | `~/.openclaw/workspace/memory/reference/` |
| Memory templates | 6 | `~/.openclaw/workspace/memory/` |
| Learnings structure | 3 | `~/.openclaw/workspace/.learnings/` |
| Cron prompts | 9 | `~/.openclaw/workspace/scripts/` |
| Memory tools | 2 | `~/.openclaw/workspace/scripts/` |
| Python deps | 2 | `sqlite-vec` + `google-genai` (auto-installed) |

Won't overwrite existing files. Use `--force` to replace all.

## Skills

| Command | What it does |
|---|---|
| `/onboard` | Guided first-run setup — asks a few questions, populates your brain files |
| `/capture` | Quick-capture anything: `/capture idea: ...`, `/capture decision: ...`, etc. |
| `/logs` | Summarize session → daily note + second brain capture |
| `/audit` | Full 13-part system audit with scoring + improvement suggestions |
| `/health` | Quick health check — memory, capture, cron, gateway, security, heartbeat |
| `/weekly` | Weekly review — synthesize daily notes, surface patterns, suggest housekeeping |
| `/project` | Initialize or load project memory: `/project init myapp` |
| `/projects` | Active and dormant workstreams |
| `/commitments` | Promises and deadline tracking with urgency indicators |
| `/decisions` | Decision journal with reasoning |
| `/followups` | Follow-up items with staleness (🟢🟡🔴) |
| `/ideas` | Idea parking lot with age tracking |
| `/people` | Key contacts CRM |
| `/fastlanes` | Show/add/remove domain-specific response templates |
| `/conflicts` | Scan brain files for contradictions and inconsistencies |
| `/export` | Export brain state as portable markdown zip |

Plus `self-improving-agent` — automatically captures errors, corrections, and lessons learned.

## Knowledge Docs

| Doc | What you learn |
|---|---|
| `TOKEN-EFFICIENCY.md` | Context management, rate limiting, output discipline, anti-patterns |
| `SELF-LEARNING.md` | How to set up `.learnings/` for continuous improvement |
| `PLAYBOOK.md` | Response patterns, critique-by-default, proactive triggers |
| `SECOND-BRAIN.md` | Memory architecture — daily notes + 5 specialized capture files |
| `CRON-PATTERNS.md` | 10 automation patterns with schedules and prompt templates |
| `MEMORY-DB.md` | SQLite + sqlite-vec structured memory layer |
| `SPACED-REPETITION.md` | Auto-resurface learnings with SM-2 intervals |

## Automated Routines

Set up all 12 cron jobs interactively:
```bash
bash setup-crons.sh
# Asks: timezone, model, Obsidian (yes/no)
# Creates all 12 cron jobs in ~30 seconds
```

| Schedule | Job |
|---|---|
| Daily 08:00 | Morning summary (priorities, calendar, blockers) |
| Daily 08:30 | Commitment deadline alerts |
| Daily 23:00 | EOD summary (consolidate daily note + second brain capture) |
| Daily 23:05 | Push daily note to Obsidian |
| Every 6h | Gateway health check |
| Sunday 20:00 | Weekly backup |
| Sunday 21:00 | Weekly distillation (memory compaction + weekly brief) |
| Daily 08:15 | Spaced repetition review (3 learnings/day) |
| Monday 08:30 | Weekly report |
| Daily 23:02 | Memory DB incremental index |
| 1st & 15th 10:00 | Biweekly learnings review |
| 1st of month 06:00 | Archive old daily notes |

## How it works

```
You chat normally
    ↓
Ghost Brain auto-captures decisions, people, ideas, commitments
    ↓
Daily: EOD summarizes → structured notes
    ↓
Daily: Spaced repetition resurfaces 3 learnings
    ↓
Memory DB indexes everything → SQL + vector search
    ↓
Weekly: distillation compacts memory → weekly brief
    ↓
Biweekly: learnings reviewed → patterns promoted
    ↓
/audit tells you if everything is working
```

## Gateway Watchdog

OpenClaw cron jobs can't alert you if the gateway itself is down. Ghost Brain includes an OS-level watchdog that monitors independently:

```bash
# Create secrets
echo "YOUR_BOT_TOKEN" > ~/.openclaw/workspace/secrets/telegram_bot_token.txt
echo "YOUR_CHAT_ID" > ~/.openclaw/workspace/secrets/telegram_chat_id.txt

# Add to OS crontab (every 2 minutes)
crontab -e
# Add: */2 * * * * bash ~/.openclaw/workspace/scripts/gateway_watchdog.sh
```

If gateway goes down → you get a Telegram alert within 2 minutes. systemd auto-restarts it in 5 seconds.

## Cron Variables

Cron prompt scripts use `{{USER_NAME}}` as a placeholder. OpenClaw automatically replaces this with your configured agent name at runtime — no manual editing needed.

## Obsidian Integration (optional)

If you use Obsidian for notes, Ghost Brain can push daily and weekly notes to your vault:

1. Edit `scripts/obsidian_push_daily.sh` — set `OBSIDIAN_DAILY_DIR` to your vault's daily notes folder
2. Edit `scripts/obsidian_push_weekly.sh` — set `OBSIDIAN_WEEKLY_DIR` to your vault's weekly folder
3. When running `setup-crons.sh`, answer "y" to the Obsidian question

## Customize

| What | Where | How |
|---|---|---|
| Fast lanes (response patterns) | `memory/reference/PLAYBOOK.md` | Add/edit domain-specific patterns |
| Cron schedules | `openclaw cron list` → `openclaw cron update <id>` | Change time/frequency |
| Capture triggers | Skills: `ghost-capture`, `ghost-logs` | Edit trigger words/patterns |
| Memory templates | `memory/*.md` | Edit headers/sections |
| Heartbeat checks | `scripts/heartbeat_pulse.sh` | Enable/disable individual checks |
| Audit dimensions | `skills/ghost-audit/SKILL.md` | Add checks or adjust scoring |

## Uninstall

Ghost Brain only adds files — it doesn't modify OpenClaw config. To remove:

```bash
# Remove skills
rm -rf ~/.openclaw/workspace/skills/ghost-*
rm -rf ~/.openclaw/workspace/skills/self-improving-agent

# Remove knowledge docs
rm -f ~/.openclaw/workspace/memory/reference/{TOKEN-EFFICIENCY,SELF-LEARNING,PLAYBOOK,SECOND-BRAIN,CRON-PATTERNS}.md

# Remove cron jobs
openclaw cron list  # note the IDs
openclaw cron delete <id>  # for each Ghost Brain cron

# Memory files (decisions.md, people.md, etc.) contain YOUR data — keep or delete as you wish
```

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw) installed and configured
- Any LLM provider (Claude, GPT, Gemini, etc.)

## Before / After

| | Without | With Ghost Brain |
|---|---|---|
| New session | Re-explain everything | AI knows your context |
| Same mistake | Repeats every time | Learns, never repeats |
| Deadlines | Forget until someone asks | Alerts 2 days before |
| API costs | Uncontrolled | 30-50% reduction |
| End of day | Nothing saved | Auto-summarized daily note |
| Weekly review | Manual effort | Auto-generated brief |
| Learnings | Log once, forget | Resurface until mastered |
| Search memory | Scroll through files | SQL + semantic vector search |

## License

MIT

## Credits

Built by [Joe](https://github.com/skzjoe) with Ghost 👻
