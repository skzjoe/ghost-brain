# 👻 Ghost Brain

**AI Second Brain for OpenClaw** — self-learning, token efficiency, and automated routines that make your AI assistant smarter every day.

> Your AI forgets everything every session. Ghost Brain fixes that in 30 seconds.

## What it does

🧠 **Second Brain** — 5 auto-capture systems
- Decisions, people, ideas, commitments, follow-ups — all captured automatically from conversations

📝 **Self-Learning** — your AI learns from mistakes
- Errors logged once, never repeated. Patterns promoted to global rules automatically.

💰 **Token Efficiency** — save 30-50% on API costs
- Rate limiting, context management, output discipline rules

⏰ **10 Automated Routines**
- Morning brief, EOD summary, weekly distillation, commitment alerts, health checks, backups

🔧 **16 System Commands**
- `/onboard` — guided first-run setup
- `/capture` — quick-capture to the right brain file
- `/audit` `/health` `/weekly` `/logs`
- `/projects` `/project` `/commitments` `/decisions` `/followups` `/ideas` `/people`
- `/fastlanes` `/conflicts` `/export`

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

That's it. 30 seconds. No dependencies.

## What gets installed

| Component | Count | Location |
|---|---|---|
| Skills | 16 | `~/.openclaw/workspace/skills/` |
| Knowledge docs | 5 | `~/.openclaw/workspace/memory/reference/` |
| Memory templates | 6 | `~/.openclaw/workspace/memory/` |
| Learnings structure | 3 | `~/.openclaw/workspace/.learnings/` |
| Cron prompts | 9 | `~/.openclaw/workspace/scripts/` |

Won't overwrite existing files. Use `--force` to replace all.

## Skills

| Command | What it does |
|---|---|
| `/onboard` | Guided first-run setup — asks a few questions, populates your brain files |
| `/capture` | Quick-capture anything: `/capture idea: ...`, `/capture decision: ...`, etc. |
| `/logs` | Summarize session → daily note + second brain capture |
| `/audit` | Full 12-dimension system audit with weighted scoring |
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

## Automated Routines

Set up all 10 cron jobs in one command:
```bash
# Edit timezone first (default: Asia/Bangkok)
nano setup-crons.sh
bash setup-crons.sh
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
| Monday 08:30 | Weekly report |
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

## License

MIT

## Credits

Built by [Joe](https://github.com/skzjoe) with Ghost 👻
