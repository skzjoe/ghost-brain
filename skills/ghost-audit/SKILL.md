---
name: audit
description: "Full chain audit — verify Ghost's brain works end-to-end: prompt coherence from /new to EOD, cross-file consistency, self-learning lifecycle, plus infrastructure health."
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

Every check below should be evaluated against these 4 pillars. Not just "does it exist" but "does it serve productivity, efficiency, proactivity, or critique?"

## Instructions

Run all checks, then compose the output. Use sub-agents for parallel reads if needed.

---

### Part 1 — 🧠 Brain Coherence (main focus)

Verify the prompt/MD chain works end-to-end across a full day cycle.

#### 1A. Session Boot (`/new`)
AGENTS.md tells Ghost to read GHOST_PLAYBOOK.md + ACTIVE_WORK.md on startup. Verify:
- [ ] Both files exist and are non-empty
- [ ] ACTIVE_WORK.md workstreams match MEMORY.md `### Key workstreams` — flag mismatches (project in one but not the other, status contradictions)
- [ ] SOUL.md + IDENTITY.md + USER.md — no contradictions between them
- [ ] AGENTS.md policies still make sense (sub-agent rules, daily note format, etc.)

#### 1B. During-session prompts
GHOST_PLAYBOOK.md drives response behavior. Verify:
- [ ] Fast lanes cover the current active workstreams (e.g., if a new domain appeared in ACTIVE_WORK.md, is there a relevant fast lane?)
- [ ] Capture triggers (decisions, people, ideas, commitments, follow-ups) — read each trigger definition and verify the target file has the structure those triggers expect (headers, table format, etc.)
- [ ] Proactive maintenance triggers — still relevant to current work context?
- [ ] Quick commands list — all referenced files/skills still exist?

#### 1C. Heartbeat
HEARTBEAT.md drives between-cron checks. Verify:
- [ ] Checks listed still match current reality (e.g., does it reference files/tools that exist?)
- [ ] heartbeat_pulse.sh exists and is executable (or verify heartbeat works without it per HEARTBEAT.md rules)
- [ ] heartbeat-state.json — exists? Format still valid?

#### 1D. EOD & Weekly cycle
Cron jobs handle EOD summary, Obsidian push, weekly distillation, weekly backup. Verify:
- [ ] Cron jobs exist for: EOD summary, Obsidian push, weekly distillation, weekly backup
- [ ] EOD cron target matches AGENTS.md `/logs` behavior expectations
- [ ] Weekly distillation output (MEMORY.md) — does `_Last updated` show the distillation is actually running?
- [ ] Obsidian push script exists at path referenced in TOOLS.md

#### 1E. Cross-file consistency
The real test — do files agree with each other?
- [ ] **ACTIVE_WORK.md vs follow-ups.md** — any active project missing from follow-ups that should have tracked items? Any follow-up referencing a project now completed/dormant?
- [ ] **ACTIVE_WORK.md vs commitments.md** — active customer projects with no commitments tracked (⚠️ if customer-facing work)
- [ ] **MEMORY.md vs ACTIVE_WORK.md** — workstreams section in MEMORY.md vs ACTIVE_WORK.md entries. Flag duplicated info that drifted, contradictions, or stale entries in either
- [ ] **GHOST_PLAYBOOK.md vs AGENTS.md** — any conflicting policies? (e.g., sub-agent approval rules, response patterns)
- [ ] **TOOLS.md** — referenced paths/scripts still exist?

---

### Part 2 — 🔄 Self-Learning Verification

Not just "files exist" but "the learning loop actually works."

#### 2A. Capture → is Ghost actually logging lessons?
- `.learnings/ERRORS.md` — count entries, date of most recent. >14 days since last = ⚠️
- `.learnings/FEATURE_REQUESTS.md` — count open items

#### 2B. Scope → are lessons going to the right place?
- `.learnings/domains/*.md` — list files, check not empty (<100 bytes = empty). Do domain files cover the active workstreams? (e.g., if ERP work is active, `erp.md` should exist and have content)
- `.learnings/projects/*.md` — list files. Do they match active projects? Missing project file for a major active project = ⚠️

#### 2C. Promote → are recurring patterns being elevated?
- `.learnings/LEARNINGS.md` — count promoted rules. 0 = never promoted = ⚠️
- Check: any domain/project entries that appear 3+ times but haven't been promoted? (quick grep for repeated patterns)

#### 2D. Archive → is cleanup happening?
- `.learnings/archive/` — has content? If LEARNINGS.md is growing but nothing archived = lifecycle incomplete
- `.learnings/REVIEW.md` — exists? Has recent review date?

#### 2E. Feedback loop → do learnings actually influence behavior?
- Quick spot-check: pick 1-2 rules from LEARNINGS.md and verify they're still relevant (not about a completed/archived project, not contradicted by newer info)
- Any learnings that reference tools/paths that no longer exist?

---

### Part 3 — 🏗️ Infrastructure & Resilience (quick pass)

Report only problems — if all green, one line summary.

**Infrastructure:**
1. `openclaw gateway status` → running + RPC ok
2. `openclaw cron list` → count, flag failures
3. `openclaw security audit` → flag critical/warn

**Resilience:**
4. Backups: `ls -lt backups/ | head -3` — freshness
5. Git: last commit age
6. Obsidian: today/yesterday note in vault
7. Skills count + workspace root hygiene

---

### Part 4 — ⏰ Obligations (brief)

- Overdue commitments (deadline < today)
- Stale follow-ups (>14 days active)
- Active follow-up count

---

## Output Format

```
👻 Ghost Audit — {date}

━━━ 🧠 Brain Coherence ━━━

🔗 Boot chain: {✅ all connected / ⚠️ issues}
  {list any mismatches found}

📋 Session prompts: {✅ aligned / ⚠️ gaps}
  {list any fast lane gaps, broken trigger targets, missing referenced files}

💓 Heartbeat: {✅ valid / ⚠️ issues}

🌙 EOD/Weekly cycle: {✅ running / ⚠️ issues}
  {list any cron/script issues}

🔀 Cross-file consistency: {✅ consistent / ⚠️ drifts found}
  {list specific contradictions or gaps between files}

━━━ 🔄 Self-Learning ━━━

Capture: {✅/⚠️} — {N} errors logged, last {date}
Scope: {✅/⚠️} — domains: {list} | projects: {list}
Promote: {✅/⚠️} — {N} global rules
Archive: {✅/⚠️} — {status}
Feedback: {✅/⚠️} — {spot-check result}

━━━ 🏗️ Infrastructure ━━━
{one line if healthy, or bullet list of issues}

━━━ ⏰ Obligations ━━━
Overdue: {N} | Stale: {N} | Active: {N}
{list items if any issues}

━━━ Overall ━━━

🧠 Coherence {score}/10 · 🔄 Learning {score}/10 · 🏗️ Infra {score}/10

{🔴 Issues that need fixing now}
{📋 Recommendations}
```

### Scoring

**🧠 Coherence:**
- 10: all files consistent, no contradictions, boot chain clean, triggers valid, cross-file aligned
- 8: minor drift (1-2 stale references) but no contradictions
- 6: contradictions found or significant gaps in cross-file alignment
- 4: major inconsistencies — brain is giving conflicting instructions to itself

**🔄 Learning:**
- 10: full lifecycle active + spot-check passes + domain/project coverage matches active work
- 8: capture+scope working, promotion/archive not regular
- 6: capture only, scoping incomplete
- 4: barely used or stale

**🏗️ Infra:**
- 10: all green
- 8: minor warnings
- 6: failures present
- 4: critical issues
