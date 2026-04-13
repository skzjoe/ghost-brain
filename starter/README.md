# Ghost Brain

**The self-improving second brain for your AI agent.**

Ghost Brain is an opinionated product layer that runs on top of [OpenClaw](https://github.com/openclaw/openclaw). It turns your AI agent into a persistent personal assistant with layered memory, a closed learning loop, proactive workflows, and execution-state tracking.

## What Ghost Brain Does

🧠 **Memory** — Layered memory model with daily notes, decisions, people, ideas, commitments, follow-ups, and a compiled wiki. SQLite + vector search with knowledge graph.

🔄 **Learning Loop** — Captures lessons from every session. Spaced repetition review. Automatic promotion of validated patterns into durable guidance.

📌 **Execution State** — Tracks active workstreams, commitments, follow-ups, and blockers. Surfaces "what matters now" proactively.

💓 **Proactive Systems** — Heartbeat pulse, morning briefings, deadline alerts, stale follow-up nudging, and weekly reviews — all running unattended.

📊 **Capture Pipeline** — Auto-captures decisions, people context, ideas, and commitments during natural conversation.

🎯 **Self-Improvement** — Error taxonomy, structured learnings, spaced repetition review, and automated skill candidate detection.

## Architecture

```
┌─────────────────────────────────────┐
│  Layer 3 — Your workspace adapters  │
│  (Obsidian, ERPNext, custom tools)  │
├─────────────────────────────────────┤
│  Layer 2 — Ghost Brain (this)       │
│  Memory · Learning · Execution      │
│  Workflows · Identity · Health      │
├─────────────────────────────────────┤
│  Layer 1 — OpenClaw runtime         │
│  Gateway · Tools · Channels · Cron  │
└─────────────────────────────────────┘
```

Ghost Brain is the middle layer. It depends on OpenClaw for infrastructure and can be extended with workspace-specific adapters on top.

## Quick Start

```bash
# 1. Install OpenClaw first
# See: https://github.com/openclaw/openclaw

# 2. Install Ghost Brain
curl -fsSL https://raw.githubusercontent.com/skzjoe/ghost-brain/main/install.sh | bash

# 3. Follow the bootstrap checklist
cat BOOTSTRAP.md
```

## Commands

### Memory & Recall
| Command | Description |
|---|---|
| `/recall <query>` | Search all memory layers |
| `/remember <content>` | Auto-route to correct memory file |
| `/capture <type>` | Quick-capture: decision, idea, commitment, follow-up, person |

### Learning & Growth
| Command | Description |
|---|---|
| `/learnings` | Learning loop status and due reviews |

### Execution & Focus
| Command | Description |
|---|---|
| `/projects` | Active workstreams |
| `/commitments` | Promises and deadlines |
| `/followups` | Waiting/blocked items |
| `/ideas` | Idea parking lot |

### Review & Maintenance
| Command | Description |
|---|---|
| `/logs` | Session summary → daily note → learnings |
| `/weekly` | Weekly review and pattern surfacing |
| `/health` | Ghost-layer health check |
| `/audit` | Full 13-dimension system audit |

### People & Context
| Command | Description |
|---|---|
| `/people` | Key contacts |
| `/decisions` | Decision journal |

## Core Scripts

| Script | Purpose |
|---|---|
| `ghost_learning_loop.py` | Reflect, promote, detect skill candidates |
| `ghost_unified_recall.py` | Unified search + smart capture + user model |
| `ghost_memory_db.py` | SQLite + vector DB with knowledge graph |
| `ghost_error_classifier.py` | 12-category structured error taxonomy |
| `ghost_todos.py` | Intra-session todo tracking |
| `memory_content_scanner.py` | Memory write safety scanning |
| `learning_review.py` | Spaced repetition for learnings |
| `model_router.py` | Advisory model routing (cheap/strong/heavy) |
| `heartbeat_pulse.sh` | Bash-first proactive signal detection |
| `ghost_cli.py` | Unified product-facing CLI over recall, learning, context, and research |
| `ghost_session_context.py` | Snapshot active focus, blockers, deadlines, and continuity signals |
| `ghost_working_memory.py` | Build briefings and triage due/stale follow-ups |
| `ghost_research.py` | Eval, safety, regression, continuity, dashboard, and experiment umbrella CLI |

## Testing

```bash
python3 -m pytest tests/ -q
```

The starter now ships targeted tests for recall, Ghost core adapters/contracts, session context, working memory, and research surfaces.

## License

MIT

## Links

- [OpenClaw](https://github.com/openclaw/openclaw) — the runtime substrate
- [Ghost Brain repo](https://github.com/skzjoe/ghost-brain) — this project
