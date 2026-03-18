# 👻 Ghost Brain

**Your AI forgets everything every session. Ghost Brain fixes that.**

An AI second brain for [OpenClaw](https://github.com/openclaw/openclaw) — self-learning memory, automated routines, and structured recall that make your AI assistant permanently smarter.

---

## The Problem

Every AI session starts from zero. Your assistant doesn't remember last week's decisions, forgets the same mistakes, misses deadlines, and burns tokens re-reading context. You end up being your AI's memory — which defeats the purpose.

## The Solution

Ghost Brain gives your AI assistant a persistent, self-organizing memory system:

| Capability | What it does |
|---|---|
| 🧠 **Auto-Capture** | Decisions, people, ideas, commitments, follow-ups — captured from normal conversation |
| 📚 **Self-Learning** | Errors logged once, patterns promoted to rules. Your AI stops repeating mistakes |
| 🔄 **Learning Review** | Critical learnings resurface on interval-based review until mastered |
| 🗄️ **Memory DB** | SQLite + vector search — SQL queries + semantic search in one zero-infra file |
| 🕸️ **Knowledge Graph** | Auto-linked relationships. Ask "what do I know about X" and get connected context |
| ⏰ **10 Automated Routines** | Morning briefing, EOD summary, commitment alerts, weekly distill, backups |
| 💰 **Token Efficiency** | Rate limiting, context discipline, lean memory — save 30-50% on API costs |
| 🔍 **13-Part Audit** | System-wide health check with scoring + actionable improvement suggestions |

## Before / After

| | Without Ghost Brain | With Ghost Brain |
|---|---|---|
| New session | Re-explain everything | AI knows your context |
| Same mistake | Repeats every time | Learns, never repeats |
| Deadlines | Forget until someone asks | Alerts 2 days before |
| API costs | Uncontrolled | 30-50% reduction |
| End of day | Nothing saved | Auto-summarized daily note |
| Weekly review | Manual effort | Auto-generated brief |
| Old decisions | Lost in chat history | Searchable with reasoning |
| Knowledge decay | Never reviewed | Stale alerts + resurfacing |

## Quick Start

```bash
git clone https://github.com/skzjoe/ghost-brain.git
cd ghost-brain
bash install.sh
```

That's it. Installs dependencies, indexes your memory, and initializes the learning system.

**Optional:** Set `GEMINI_API_KEY` for semantic vector search (free at [ai.google.dev](https://ai.google.dev)):
```bash
export GEMINI_API_KEY=your_key_here
bash install.sh
```
Without it, full-text search still works — you just don't get semantic similarity.

Set up automated routines:
```bash
bash setup-crons.sh
# Interactive — asks your timezone, preferred model, and Obsidian preference
```

## What Gets Installed

| Component | Count | Location |
|---|---|---|
| Skills (commands) | 16 | `~/.openclaw/workspace/skills/` |
| Knowledge docs | 8 | `~/.openclaw/workspace/memory/reference/` |
| Memory templates | 6 | `~/.openclaw/workspace/memory/` |
| Learnings structure | 3 | `~/.openclaw/workspace/.learnings/` |
| Cron prompts | 10 | `~/.openclaw/workspace/scripts/` |
| Memory tools | 3 | `~/.openclaw/workspace/scripts/` |

**Non-destructive** — won't overwrite existing files. Use `--force` to update code files (your data files are always protected).

## Daily Usage

Ghost Brain works in the background. Here's the only workflow you need:

### 1. Just chat
Talk to your AI like normal. Ghost Brain auto-captures decisions, people, ideas, and commitments as they come up in conversation. No special syntax, no commands — just talk.

### 2. `/logs` before `/new` — the safety net
Auto-capture catches most things in real-time, but `/logs` is your safety net. It scans the entire session and catches anything that slipped through — then files everything to the right brain files.

Think of it like **autosave vs Ctrl+S**: autosave works in the background, but you still save before closing. **Always run `/logs` before `/new`.**

### 3. Correct your AI
When your AI gets something wrong, tell it. The correction gets logged as a learning and won't happen again. Over time, your AI gets noticeably better at your specific workflows.

### 4. Let cron handle the rest
Morning briefing surfaces your priorities. Learning review resurfaces past lessons. EOD summary catches anything you missed. Weekly distill keeps memory lean. You don't need to manage any of this.

**That's it.** Chat → `/logs` → `/new` → repeat. Everything else is automatic.

## Commands

| Command | What it does |
|---|---|
| `/onboard` | Guided first-run setup — populates your brain files from a few questions |
| `/capture` | Quick-capture: `/capture idea: ...`, `/capture decision: ...` |
| `/logs` | Summarize session → daily note + auto-capture to all brain files |
| `/audit` | 13-part system audit with scorecard + 4-pillar improvement suggestions |
| `/health` | Quick health check — memory, capture, cron, security |
| `/weekly` | Weekly review — synthesize patterns, suggest housekeeping |
| `/projects` | Active and dormant workstreams at a glance |
| `/commitments` | Promises and deadlines with urgency indicators |
| `/decisions` | Decision journal with reasoning |
| `/followups` | Follow-up items with staleness (🟢🟡🔴) |
| `/ideas` | Idea parking lot |
| `/people` | Lightweight contact CRM |
| `/fastlanes` | Domain-specific response templates |
| `/conflicts` | Scan for contradictions across brain files |
| `/export` | Portable markdown bundle for backup or migration |

## Knowledge Docs

| Doc | What you learn |
|---|---|
| `TOKEN-EFFICIENCY.md` | Context management, rate limiting, output discipline, anti-patterns |
| `SELF-LEARNING.md` | How to set up `.learnings/` for continuous improvement |
| `PLAYBOOK.md` | Response patterns, critique-by-default, proactive triggers |
| `SECOND-BRAIN.md` | Memory architecture — daily notes + 5 specialized capture files |
| `CRON-PATTERNS.md` | 10 automation patterns with schedules and prompt templates |
| `MEMORY-DB.md` | SQLite + sqlite-vec structured memory layer |
| `LEARNING-REVIEW.md` | Auto-resurface learnings with interval-based recall |
| `CODING-WORKFLOW.md` | Brownfield-safe AI coding workflow with research/plan/implement/compaction |

## Memory DB

Ghost Brain includes a structured memory layer powered by SQLite + [sqlite-vec](https://github.com/asg017/sqlite-vec):

- **Full-text search** (FTS5) + **semantic vector search** in one `.db` file
- **Knowledge graph** — auto-links items (people→decisions→projects→learnings)
- **Deduplication** — finds and merges duplicate entries
- **Temporal intelligence** — tracks access patterns, flags stale knowledge, surfaces hot items
- **Source tracking** — auto-detects where knowledge came from
- **Cross-session context bridge** — generates relevant startup context from DB
- **Zero infrastructure** — single SQLite file, no server, no Docker

```bash
# Search semantically
python3 scripts/ghost_memory_db.py search "deployment errors last month"

# Query by type
python3 scripts/ghost_memory_db.py query decision --days 30

# Full maintenance pipeline
python3 scripts/ghost_memory_db.py pipeline
```

## Automated Routines

| Schedule | Job |
|---|---|
| Daily 08:00 | Morning Briefing — priorities, calendar, blockers |
| Daily 08:15 | Learning Review — resurface 3 learnings |
| Daily 08:30 | Commitment Deadline Alert |
| Daily 23:00 | EOD Session Log — consolidate notes + capture + re-index Memory DB |
| Daily 23:05 | Obsidian Daily Sync (optional) |
| Every 6h | Gateway Healthcheck |
| Sunday 20:00 | Weekly Backup |
| Sunday 21:00 | Weekly Memory Distill — compact + weekly brief |
| Monday 08:30 | Weekly Report |
| 1st of month | Monthly Note Archive |

## How It Works

```
You chat normally with your AI
         ↓
Ghost Brain auto-captures decisions, people, ideas, commitments
         ↓
EOD cron summarizes → structured daily notes → re-indexes Memory DB
         ↓
Morning cron resurfaces 3 learnings based on review intervals
         ↓
Memory DB provides SQL + vector search across all your knowledge
         ↓
Weekly distill compacts memory → weekly brief
         ↓
/audit scores your system health across 13 dimensions
```

## See It In Action

- 📋 [Full audit output](examples/audit-output.md) — 13-dimension scorecard + improvement suggestions
- 📝 [Daily note example](examples/daily-note.md) — what EOD auto-summary produces
- 🧠 [Auto-capture demo](examples/capture-in-action.md) — decisions, people, commitments from normal chat
- 🛠️ [Coding workflow example](examples/coding-workflow-example.md) — research → plan → implement → compaction for a brownfield bug fix

## Customization

| What | Where |
|---|---|
| Response patterns | `memory/reference/PLAYBOOK.md` — add domain-specific fast lanes |
| Cron schedules | `openclaw cron list` → `openclaw cron edit <id>` |
| Capture triggers | Skills: `ghost-capture`, `ghost-logs` |
| Memory templates | `memory/*.md` — edit sections/headers |
| Heartbeat checks | `scripts/heartbeat_pulse.sh` |
| Audit scoring | `skills/ghost-audit/SKILL.md` |
| Coding workflow | `memory/reference/CODING-WORKFLOW.md` + `skills/assets/coding-*-template.md` |

## Obsidian Integration (optional)

Push daily and weekly notes to your Obsidian vault:

1. Set `OBSIDIAN_DAILY_DIR` in `scripts/obsidian_push_daily.sh`
2. Answer "y" to Obsidian during `setup-crons.sh`

## Gateway Watchdog

OS-level monitor that alerts you if OpenClaw gateway goes down (cron jobs can't alert when the gateway itself is offline):

```bash
echo "YOUR_BOT_TOKEN" > ~/.openclaw/workspace/secrets/telegram_bot_token.txt
echo "YOUR_CHAT_ID" > ~/.openclaw/workspace/secrets/telegram_chat_id.txt

# Add to OS crontab (every 2 minutes)
*/2 * * * * bash ~/.openclaw/workspace/scripts/gateway_watchdog.sh
```

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw) 2026.3.x+
- Python 3.10+
- Any LLM provider (Claude, GPT, Gemini, etc.)

## Uninstall

Ghost Brain only adds files — doesn't modify OpenClaw config:

```bash
rm -rf ~/.openclaw/workspace/skills/ghost-*
rm -rf ~/.openclaw/workspace/skills/self-improving-agent
rm -f ~/.openclaw/workspace/memory/reference/{TOKEN-EFFICIENCY,SELF-LEARNING,PLAYBOOK,SECOND-BRAIN,CRON-PATTERNS,MEMORY-DB,LEARNING-REVIEW,CODING-WORKFLOW,CODING-QUICKSTART}.md
rm -f ~/.openclaw/workspace/skills/assets/coding-*-template.md
openclaw cron list  # then: openclaw cron rm <id> for each Ghost Brain job
# Your data files (decisions.md, people.md, etc.) are yours — keep or delete
```

## License

MIT

## Credits

Built by [Joe](https://github.com/skzjoe) with Ghost 👻
g-agent
rm -f ~/.openclaw/workspace/memory/reference/{TOKEN-EFFICIENCY,SELF-LEARNING,PLAYBOOK,SECOND-BRAIN,CRON-PATTERNS,MEMORY-DB,LEARNING-REVIEW,CODING-WORKFLOW}.md
rm -f ~/.openclaw/workspace/skills/assets/coding-*-template.md
openclaw cron list  # then: openclaw cron rm <id> for each Ghost Brain job
# Your data files (decisions.md, people.md, etc.) are yours — keep or delete
```

## License

MIT

## Credits

Built by [Joe](https://github.com/skzjoe) with Ghost 👻
