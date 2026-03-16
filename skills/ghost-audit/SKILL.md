---
name: audit
description: "Full chain audit — verify Ghost Brain works end-to-end across 12 dimensions: prompt coherence, capture, learning, proactive systems, token efficiency, obligations, infrastructure, and resilience."
user-invocable: true
---

# /audit

Verify Ghost's brain works correctly as a whole system — not just "files exist" but "everything connects and functions."

## North Star
Ghost Brain exists to be the **best personal assistant** — measured by 4 pillars:
1. **Productive** — does the system produce output that moves work forward?
2. **Efficient** — minimum tokens, minimum steps, maximum value?
3. **Proactive** — does it anticipate needs, flag risks, surface context before asked?
4. **Critique** — does it challenge assumptions, catch gaps, push for better decisions?

Every check below should be evaluated against these 4 pillars.

## Instructions

Run all checks, then compose the output.

---

### Part 1 — 🔗 Boot Chain
AGENTS.md tells Ghost to read GHOST_PLAYBOOK.md + ACTIVE_WORK.md on startup. Verify:
- [ ] All core files exist and non-empty: AGENTS.md, GHOST_PLAYBOOK.md, ACTIVE_WORK.md, SOUL.md, IDENTITY.md, USER.md, MEMORY.md, HEARTBEAT.md, TOOLS.md
- [ ] ACTIVE_WORK.md workstreams match MEMORY.md workstreams — flag mismatches
- [ ] SOUL.md + IDENTITY.md + USER.md — no contradictions
- [ ] AGENTS.md policies still make sense

### Part 2 — 📋 Prompt Effectiveness
GHOST_PLAYBOOK.md drives response behavior. Verify:
- [ ] Fast lanes cover current active workstreams (new domain without fast lane = gap)
- [ ] Capture triggers (decisions, people, ideas, commitments, follow-ups) — target files exist with expected format
- [ ] Proactive maintenance triggers — still relevant?
- [ ] Quick commands — all referenced files/skills exist?
- [ ] Any dead references in playbook to removed tools/files?

### Part 3 — 🧠 Capture Systems
Are all 5 second-brain files actively being used?

| File | Check | Healthy | Warning |
|---|---|---|---|
| `decisions.md` | Entries from last 7 days | >0 recent | 0 recent |
| `people.md` | Last update date | <14 days | >30 days |
| `ideas.md` | Active idea count | Has active | 0 or stale >30d |
| `commitments.md` | Active entries when customers active | Has entries | Empty with active customer projects |
| `follow-ups.md` | Active items tracked, none stale | Active items, 0 stale >14d | Stale items or 0 when work active |

### Part 4 — 📝 Memory Freshness
- [ ] MEMORY.md `_Last updated:` — fresh (<14 days)?
- [ ] Daily notes: count last 7 days (expect 5+)
- [ ] Today's note: missing after 12:00 = ⚠️ (before noon = normal)
- [ ] `wc -c MEMORY.md` — size check (flag if >15KB = bloat risk)

### Part 5 — 🔄 Learning Lifecycle
Full cycle: capture → scope → promote → archive → review

| Stage | Check | Healthy |
|---|---|---|
| Capture | `.learnings/ERRORS.md` entry count + last date | Within 14 days |
| Scope | `domains/*.md` + `projects/*.md` — non-empty, cover active work | Coverage matches active projects |
| Promote | `LEARNINGS.md` rule count | >0 promoted |
| Archive | `archive/` has content | Used at least once |
| Review | `REVIEW.md` exists + has recent entry | Exists with date |

### Part 6 — 💓 Proactive Coverage
Are proactive systems actually firing?
- [ ] Heartbeat pulse script exists + executable
- [ ] heartbeat-state.json exists + valid
- [ ] Commitment Deadline Alert cron exists + status ok/idle (not errored)
- [ ] Morning Summary cron exists + last run <24h on workdays
- [ ] EOD Summary cron exists + last run <24h
- [ ] Follow-up nudge: heartbeat-state.json tracks cooldowns
- [ ] Weekly Memory Distill cron exists + status ok/idle

### Part 7 — ⏰ Obligation Health
- [ ] Overdue commitments (deadline < today, not fulfilled) — count
- [ ] Stale follow-ups (active, since >14 days) — count + list
- [ ] Active customer projects with NO commitments or follow-ups tracked — flag
- [ ] Follow-ups referencing completed/dormant projects — flag

### Part 8 — 💡 Token Efficiency
- [ ] `wc -c MEMORY.md` — flag if >15KB (it's in every message)
- [ ] Cron models — should be cost-efficient (gpt-5.4 or similar), not premium unless needed
- [ ] MEMORY.md vs ACTIVE_WORK.md — check for fully duplicated paragraphs (some overlap is OK, full duplicate = waste)
- [ ] Heartbeat design — verify bash-first (0 tokens when idle)
- [ ] Any cron running premium model unnecessarily?

### Part 9 — ⚡ Runtime
- [ ] `openclaw gateway status` — running + RPC ok
- [ ] PID stable, no crash indicators

### Part 10 — ⚙️ Automation
- [ ] `openclaw cron list` — count jobs, flag any status=error/failed
- [ ] All expected crons present (EOD Session Log, Morning Briefing, Morning Learning Review, Obsidian Daily Sync, Weekly Backup, Weekly Memory Distill, Commitment Deadline Alert, Gateway Healthcheck, Weekly Report, Monthly Note Archive)
- [ ] Heartbeat cron configured

### Part 11 — 🛡️ Resilience
- [ ] Backup freshness: `ls -lt backups/ | head -3`
- [ ] Git: last commit age (<7 days = healthy)
- [ ] Obsidian: today/yesterday note in vault
- [ ] TOOLS.md referenced paths all exist
- [ ] Skills count
- [ ] Workspace root hygiene (only durable files, no temp/loose files)

### Part 12 — 🔒 Security
- [ ] `openclaw security audit` — count critical/warn/info
- [ ] Flag critical findings

---

## Output Format

```
👻 Ghost Audit — {date}

━━━ 🧠 Brain Health ━━━

🔗 Boot Chain: {details}
📋 Prompts: {details}
🧠 Capture: {X}/5 active — {details}
📝 Memory: {details}
🔄 Learning: capture {✅/⚠️} → scope {✅/⚠️} → promote {✅/⚠️} → archive {✅/⚠️} → review {✅/⚠️}
💓 Proactive: {details}
⏰ Obligations: {details}
💡 Efficiency: {details}

━━━ 🏗️ Infrastructure ━━━

⚡ Runtime: {details}
⚙️ Automation: {details}
🛡️ Resilience: {details}
🔒 Security: {details}

━━━ 📊 Scorecard ━━━

| Area | Score | Detail |
|---|---|---|
| 🔗 Boot Chain | X/10 | {1-line} |
| 📋 Prompt Effectiveness | X/10 | {1-line} |
| 🧠 Capture Systems | X/10 | {1-line} |
| 📝 Memory Freshness | X/10 | {1-line} |
| 🔄 Learning Lifecycle | X/10 | {1-line} |
| 💓 Proactive Coverage | X/10 | {1-line} |
| ⏰ Obligation Health | X/10 | {1-line} |
| 💡 Token Efficiency | X/10 | {1-line} |
| ⚡ Runtime | X/10 | {1-line} |
| ⚙️ Automation | X/10 | {1-line} |
| 🛡️ Resilience | X/10 | {1-line} |
| 🔒 Security | X/10 | {1-line} |
| | | |
| 🧠 **Brain** | **X/10** | weighted avg (brain dims × 2) |
| 🏗️ **Infra** | **X/10** | weighted avg (infra dims × 1) |
| 🏆 **Overall** | **X/10** | combined |

━━━ 🔴 Alerts ━━━
{only if problems}

━━━ 📋 Recommendations ━━━
{top 1-3, ordered by impact}
```

### Scoring Guide

| Area | 10 | 8 | 6 | 4 |
|---|---|---|---|---|
| 🔗 Boot Chain | All files present + policies current | 1 stale ref | Missing file or broken instruction | Boot would fail |
| 📋 Prompt Effectiveness | Fast lanes match work + triggers valid + no dead refs | 1 gap | Multiple gaps or stale triggers | Playbook misaligned |
| 🧠 Capture Systems | 5/5 active | 4/5 | 3/5 | Most idle |
| 📝 Memory Freshness | <7d + 6+/7 notes | <14d or 5/7 | >14d or <5/7 | Stale + poor coverage |
| 🔄 Learning Lifecycle | All 5 stages active + coverage matches work | 4/5 stages | Capture only | Barely used |
| 💓 Proactive Coverage | All systems verified working | 1 unconfigured | Multiple not firing | Proactive dead |
| ⏰ Obligation Health | 0 overdue + 0 stale + all customers tracked | 0 overdue, 1-2 gaps | Overdue or untracked | Multiple overdue |
| 💡 Token Efficiency | Lean MEMORY + efficient models + no redundancy | Minor bloat | Significant bloat | Wasteful |
| ⚡ Runtime | Up + RPC ok | Doctor warnings | Degraded | Down |
| ⚙️ Automation | All ok/idle | 1 failure | Multiple failures | Broken |
| 🛡️ Resilience | All fresh (<24h backup, <7d git, Obsidian synced) | 1 stale | 2 stale | No backups |
| 🔒 Security | 0 critical + 0 warn | Warns only | Critical findings | Unpatched critical |

### Overall Calculation
- **Brain score** = weighted avg of 8 brain dims (Boot, Prompt, Capture, Memory, Learning, Proactive, Obligation, Efficiency) — **weight 2x**
- **Infra score** = weighted avg of 4 infra dims (Runtime, Automation, Resilience, Security) — **weight 1x**
- **Overall** = (Brain × 2 + Infra × 1) / 3

---

## Part 13 — 🚀 Improvement Suggestions (4 Pillars)

After completing the scorecard, analyze the audit findings and generate **actionable improvement suggestions** mapped to the 4 North Star pillars. This is the most valuable part — the audit exists to drive improvement, not just report status.

### How to generate suggestions

For each pillar, look at:
- **Scores below 9** — what's dragging it down?
- **Missing coverage** — what workstreams/domains lack fast lanes, learnings, or project memory?
- **System gaps** — what proactive/capture/critique behaviors could exist but don't?
- **Patterns from daily notes** — recurring pain points or manual steps that could be automated?
- **Comparison to ideal** — if this system were perfect, what would it do that it doesn't today?

### Output format for suggestions

```
━━━ 🚀 Improvement Suggestions ━━━

### 🏭 Productive — increase output that moves real work forward
| # | Suggestion | Impact | Effort |
|---|---|---|---|
| P1 | {specific suggestion} | High/Med/Low | High/Med/Low |
...

### ⚡ Efficient — reduce waste, increase value per token
| # | Suggestion | Impact | Effort |
|---|---|---|---|
| E1 | {specific suggestion} | High/Med/Low | High/Med/Low |
...

### 🔮 Proactive — anticipate needs before the user asks
| # | Suggestion | Impact | Effort |
|---|---|---|---|
| R1 | {specific suggestion} | High/Med/Low | High/Med/Low |
...

### 🎯 Critique — challenge assumptions, catch gaps
| # | Suggestion | Impact | Effort |
|---|---|---|---|
| C1 | {specific suggestion} | Impact | Effort |
...

━━━ ⚡ Quick Wins (can do right now) ━━━
{Top 3-5 suggestions sorted by impact/effort ratio — things that can be done in this session}
```

### Rules for suggestions
- **Be specific** — not "improve proactive systems" but "add drift detection check to Morning Summary cron that flags ACTIVE_WORK.md staleness >5 days"
- **Reference actual findings** — tie each suggestion to a specific audit score, gap, or pattern found
- **Prioritize by leverage** — fewer high-impact suggestions > long list of small tweaks
- **Include quick wins** — always end with 3-5 things that can be implemented immediately
- **Avoid repeating what already works** — focus on gaps and growth areas, not praise
- **Mix structural + behavioral** — some suggestions improve files/crons, others improve response patterns
- **2-4 suggestions per pillar** — enough to be useful, not so many they're overwhelming
