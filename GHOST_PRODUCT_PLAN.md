# Ghost Product Master Plan v1

**Date:** 2026-04-12  
**Owner:** (you)  
**Status:** Active  
**Architecture:** Ghost product layer on top of OpenClaw runtime

---

## Guiding principle

**Ghost does not replace OpenClaw. Ghost is the opinionated product layer on top.**

OpenClaw owns: runtime, gateway, sessions, tools, exec, browser, MCP, cron scheduling, channels, models, config, doctor, status, health, security, memory indexing, skills framework, onboarding.

Ghost owns: memory model, learning loop, recall UX, capture UX, execution-state tracking, proactive behavior, artifact workflows, product identity.

When in doubt: if OpenClaw already does it, Ghost calls it — Ghost does not rebuild it.

---

## Three-layer architecture

```
┌─────────────────────────────────────────────┐
│  Layer 3 — Workspace adapters               │
│  User-specific: Obsidian, Frappe, company     │
│  docs, project packs, custom skills          │
│  (separable, not part of product core)       │
├─────────────────────────────────────────────┤
│  Layer 2 — Ghost core product layer          │
│  Memory model · Learning loop · Recall UX    │
│  Capture UX · Execution state · Health       │
│  Proactive behavior · Artifact standards     │
│  Product identity · Packaging                │
├─────────────────────────────────────────────┤
│  Layer 1 — OpenClaw runtime substrate        │
│  Gateway · Sessions · Tools · Exec · Browser │
│  MCP · Cron · Channels · Models · Config     │
│  Doctor · Status · Health · Security         │
│  Memory indexing · Skills framework          │
│  Onboarding · Setup                          │
└─────────────────────────────────────────────┘
```

---

## Step 1 — Product boundary and subsystem map

### Ghost core subsystems

#### A. Memory subsystem
**What it owns:**
- MEMORY.md — long-term durable context
- USER.md — user model
- memory/*.md — daily notes, second-brain files (decisions, people, ideas, commitments, follow-ups)
- memory/projects/, memory/topics/, memory/syntheses/ — compiled wiki
- memory/reference/ — stable archives
- Memory routing rules (what goes where)
- Memory safety scanning (injection/exfil prevention)
- Memory DB (SQLite + vector, knowledge graph, dedup)

**What it does NOT own (OpenClaw handles):**
- `openclaw memory` — file indexing, chunk storage, vector/FTS search
- Memory search tool — semantic retrieval from indexed files

**Boundary rule:** Ghost defines _what_ gets stored and _where_. OpenClaw handles _how_ it gets indexed and retrieved.

#### B. Learning subsystem
**What it owns:**
- `.learnings/` — all scoped learning files
- Learning loop engine (`ghost_learning_loop.py`)
- Learning review + spaced repetition (`learning_review.py`)
- Promotion lifecycle: proposed → observed → validated → promoted → archived
- Self-improvement hooks and error taxonomy
- `/learnings` command

**Boundary rule:** This is 100% Ghost. OpenClaw has no learning system.

#### C. Execution-state subsystem
**What it owns:**
- ACTIVE_WORK.md — workstream register
- memory/commitments.md — promises and deadlines
- memory/follow-ups.md — waiting/blocked items
- memory/now.md — focus layer (generated)
- Heartbeat pulse logic
- Stale/due detection and nudging
- Intra-session todos (`ghost_todos.py`)

**What it does NOT own:**
- `openclaw cron` — scheduling infrastructure
- `openclaw tasks` — task queue management

**Boundary rule:** Ghost defines _what needs attention_. OpenClaw handles _when to run checks_.

#### D. Workflow UX subsystem
**What it owns:**
- `/recall` — unified search across all memory layers
- `/remember` — smart capture routing
- `/capture` — quick-capture by type
- `/logs` — session summary → daily note → learnings → Obsidian
- `/learnings` — learning loop status
- `/health` — Ghost-layer health (memory freshness, learning backlog, execution state)
- `/audit` — full-system audit across 12 dimensions
- `/weekly` — weekly review and pattern surfacing
- `/new` — session reset (with mandatory log-first guard)
- Docs Toolkit — structured artifact generation

**What it does NOT own:**
- `openclaw doctor` — gateway, channels, config fixes
- `openclaw status` — runtime overview
- `openclaw health` — gateway process health
- `openclaw setup` / `openclaw configure` / `openclaw onboard` — runtime setup
- `openclaw security` — security audit

**Boundary rule:** Ghost commands are about _your work and memory_. OpenClaw commands are about _the platform_.

#### E. Product identity subsystem
**What it owns:**
- SOUL.md — persona and voice
- IDENTITY.md — name, avatar, creature
- GHOST_PLAYBOOK.md — response patterns and operating rules
- GHOST_BEHAVIORAL_RULES.md — behavioral contracts

**Boundary rule:** This defines what makes Ghost _Ghost_, not just "an agent on OpenClaw."

---

## Step 2 — Workflow map

### User-facing Ghost workflows

```
Memory & Recall
  /recall <query>     → search all memory layers, return merged results
  /remember <content> → auto-detect type, route to correct file
  /capture <type>     → quick-capture: decision, idea, commitment, follow-up, person

Learning & Growth
  /learnings          → learning loop status, due items, promotion state
  (auto)              → reflect after tasks, promote after repetition, detect skill candidates

Execution & Focus
  /projects           → active workstreams from ACTIVE_WORK.md
  /commitments        → promises and deadlines
  /followups          → waiting/blocked items with staleness
  /ideas              → idea parking lot

Review & Maintenance
  /logs               → session summary → daily note → learnings → Obsidian push
  /weekly             → weekly review: patterns, archive/promote/drop suggestions
  /health             → Ghost-layer health check (memory, learnings, execution state)
  /audit              → full 12-dimension system audit

Session
  /new                → reset (must /logs first)
  /summary            → compress current session context

People & Context
  /people             → key contacts
  /decisions          → recent decision journal
```

### What Ghost delegates to OpenClaw (not Ghost commands)

| Need | OpenClaw command |
|---|---|
| Platform health | `openclaw status`, `openclaw health` |
| Fix config issues | `openclaw doctor --fix` |
| Channel setup | `openclaw configure`, `openclaw channels` |
| Cron management | `openclaw cron list/add/remove` |
| Model switching | `/model` (OpenClaw built-in) |
| Skills browsing | `openclaw skills list` |
| Security audit | `openclaw security audit` |
| Memory reindex | `openclaw memory reindex` |

---

## Step 3 — Consolidated status surface

### `/health` — Ghost product health (complements `openclaw status`)

Ghost `/health` should report on **Ghost-layer concerns only**:

```
Ghost Health Report
═══════════════════

Memory
  MEMORY.md           : 14.2 KB (ok)
  Daily notes (30d)   : 28 files
  Last capture         : 2h ago
  Memory DB            : 174 items, 326 links, last indexed 6h ago

Learning Loop
  Total learnings      : 37
  Overdue for review   : 20
  Pending promotion    : 3
  Last reflection      : today

Execution State
  Active workstreams   : 7
  Commitments due ≤7d  : 1 (PIYAPODOK)
  Stale follow-ups     : 2
  Focus layer          : generated 18h ago

Proactive Systems
  Heartbeat            : ok, last run 52m ago
  Morning briefing     : ok, last run 9h ago
  EOD log              : ok, last run 18h ago
  Weekly distill       : ok, last run 7d ago

Capture Pipeline
  Decisions captured   : 3 (last 7d)
  People updated       : 0 (last 7d)
  Ideas captured       : 1 (last 7d)
  Commitments tracked  : 1 active

Overall: 🟢 Healthy (20 learning reviews overdue — run /learnings)
```

**Implementation:** The `/health` skill already exists (`skills/ghost-health/`). Extend it to produce this consolidated view by reading:
- file sizes and dates from `memory/`
- learning review state from `.learnings/learning-review-state.json`
- execution state from `ACTIVE_WORK.md`, `memory/commitments.md`, `memory/follow-ups.md`
- cron status from `openclaw cron list` (delegate, don't reimplement)

**What `/health` does NOT check** (OpenClaw's job):
- gateway reachability
- channel connectivity
- model availability
- config validity
- security posture

---

## Step 4 — Ghost-layer setup / operator story

### ⚠️ Design constraint: do not overlap with OpenClaw

OpenClaw already provides:
- `openclaw setup` — config, credentials, workspace init
- `openclaw configure` — interactive config
- `openclaw onboard` — guided first-time setup
- `openclaw doctor` — config validation and fixes
- `openclaw status` — full platform overview

Ghost should **NOT** duplicate any of these. Instead:

### Ghost operator concerns (what OpenClaw doesn't cover)

| Concern | Ghost's job | How |
|---|---|---|
| Memory model health | Are memory files well-structured? | `/health` memory section |
| Learning system state | Are learnings being reviewed? | `/health` learning section |
| Content safety | Is memory free of injection? | `memory_content_scanner.py --scan-all` |
| Execution state drift | Are commitments/follow-ups current? | `/health` execution section |
| Cron coverage | Are Ghost-critical crons healthy? | Heartbeat check 6 (already exists) |
| Obsidian sync | Is vault in sync? | Check in `/health` or EOD cron |
| Product boundary | Is Ghost layer clean? | Periodic audit via `/audit` |

### Ghost "doctor" equivalent

Instead of a separate `ghost doctor` command, add a **Ghost layer section** to the existing `/audit` skill:

```
/audit → existing 12 dimensions + new "Product Health" dimension:
  - Memory model: files exist, sizes ok, no stale captures
  - Learning loop: review queue manageable, promotions current
  - Execution state: no zombie commitments, follow-ups not abandoned
  - Content safety: last scan result
  - Workspace hygiene: root clean, no loose temp files
```

This avoids building a parallel doctor and keeps everything in one Ghost audit story.

### Ghost setup for new users

For the starter distribution, Ghost needs a **bootstrap checklist** (not a parallel setup wizard):

```markdown
# Ghost Bootstrap Checklist

Prerequisites:
- [ ] OpenClaw installed and configured (`openclaw setup`)
- [ ] At least one channel connected (`openclaw channels`)
- [ ] Gateway running (`openclaw gateway start`)

Ghost layer setup:
- [ ] SOUL.md — customize persona
- [ ] USER.md — describe yourself
- [ ] IDENTITY.md — name and avatar
- [ ] MEMORY.md — seed with initial context
- [ ] AGENTS.md — review operating rules
- [ ] memory/ directory — daily notes will auto-populate
- [ ] .learnings/ directory — created by first learning capture
- [ ] Run /health — verify Ghost layer is operational
- [ ] Run /audit — baseline system score
```

This is a **checklist that points to files**, not a competing interactive wizard.

---

## Step 5 — Starter distribution

### What ships in a Ghost starter package

```
ghost-brain-starter/
├── SOUL.md.template          # Customize your persona
├── IDENTITY.md.template      # Name, avatar
├── USER.md.template          # Describe yourself
├── MEMORY.md.template        # Seed memory
├── AGENTS.md                 # Operating rules (generic)
├── GHOST_PLAYBOOK.md         # Response patterns (generic)
├── GHOST_PRODUCT_PLAN.md     # This document
├── ACTIVE_WORK.md.template   # Workstream tracker
├── HEARTBEAT.md              # Heartbeat config
├── memory/
│   ├── template.md           # Daily note template
│   ├── decisions.md          # Empty, ready
│   ├── people.md             # Empty, ready
│   ├── ideas.md              # Empty, ready
│   ├── commitments.md        # Empty, ready
│   └── follow-ups.md         # Empty, ready
├── .learnings/
│   ├── LEARNINGS.md          # Empty, ready
│   ├── ERRORS.md             # Empty, ready
│   └── FEATURE_REQUESTS.md   # Empty, ready
├── scripts/
│   ├── ghost_learning_loop.py
│   ├── ghost_unified_recall.py
│   ├── ghost_memory_db.py
│   ├── ghost_error_classifier.py
│   ├── ghost_todos.py
│   ├── memory_content_scanner.py
│   ├── learning_review.py
│   ├── model_router.py
│   ├── heartbeat_pulse.sh
│   └── obsidian_merge.py
├── skills/
│   ├── ghost-capture/
│   ├── ghost-recall/
│   ├── ghost-remember/
│   ├── ghost-learnings/
│   ├── ghost-health/
│   ├── ghost-audit/
│   ├── ghost-logs/
│   ├── ghost-weekly/
│   ├── ghost-commitments/
│   ├── ghost-decisions/
│   ├── ghost-followups/
│   ├── ghost-ideas/
│   ├── ghost-people/
│   ├── ghost-projects/
│   └── ghost-onboard/
├── tests/
│   └── (210 tests)
├── install.sh                # Bootstrap script
├── BOOTSTRAP.md              # Setup checklist
├── CHANGELOG.md
└── README.md                 # Product docs
```

### What does NOT ship (User-specific adapters)

- Obsidian push scripts (vault-path-dependent)
- Frappe/ERPNext skills
- Company document skills
- Meta ads skills
- Project-specific memory files
- User's MEMORY.md content
- User's secrets/

### install.sh behavior

```bash
# 1. Check OpenClaw is installed
# 2. Copy templates to workspace
# 3. Create directory structure
# 4. Run openclaw memory reindex
# 5. Print bootstrap checklist
# 6. Suggest: "Run /onboard to set up your persona and seed memory"
```

No competing setup wizard. Just file placement + a pointer to OpenClaw and Ghost commands.

---

## Implementation priority

| # | Work item | Effort | Impact | Depends on |
|---|---|---|---|---|
| 1 | This document (product boundary) | ✅ Done | Foundation | — |
| 2 | Extend `/health` to consolidated view | 1-2h | High | Step 3 spec above |
| 3 | Extend `/audit` with product health dimension | 1-2h | High | Step 4 spec above |
| 4 | Clean up scripts → canonical Ghost subsystems | 3-5h | Medium | Steps 1-2 |
| 5 | Starter distribution packaging | 2-3h | High | Steps 1-4 |
| 6 | README + BOOTSTRAP.md for starter | 1-2h | High | Step 5 |
| 7 | Sync to ghost-brain repo | 1h | Medium | Steps 4-6 |

Total estimated effort: **~10-15 hours** to reach a shippable Ghost Product v1 on OpenClaw.

---

## Decision log

| Decision | Rationale |
|---|---|
| Ghost stays on OpenClaw | Runtime rewrite is high-cost, low-leverage |
| 3-layer architecture | Clean separation of concerns |
| No parallel doctor/setup | OpenClaw already covers platform ops |
| Ghost /health reports Ghost concerns only | Avoids confusing overlap |
| Starter ships templates, not user's data | Clean separation of product vs personal |
| install.sh delegates to OpenClaw for platform setup | One setup path, not two |

---

_Last updated: 2026-04-12_
