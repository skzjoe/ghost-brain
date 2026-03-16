# Morning Briefing — Cron Prompt

Run at 08:00 local time. Compose a concise morning briefing for {{USER_NAME}}.

## Steps

1) **Read prior context**
   - Determine today (your configured timezone); set YESTERDAY = today - 1 day.
   - Read `~/.openclaw/workspace/memory/YESTERDAY.md` (skip if missing).
   - Read `ACTIVE_WORK.md` for current workstreams, blockers, and watchlist.
   - Read `memory/commitments.md` — check for any commitments due today or overdue.
   - Extract: 📌 Next Actions + 🤝 Follow-ups + blockers + commitments due + critical IDs/codes/URLs.

2) **Blocker Nudge**
   - Check each blocker in ACTIVE_WORK.md.
   - If any blocker present 3+ days → proactively ask {{USER_NAME}}.
   - Skip items already in `memory/follow-ups.md` (heartbeat handles those).

3) **Follow-ups & Commitments check**
   - Read `memory/follow-ups.md` — list any Active items with `Since` date > 7 days ago.
   - Read `memory/commitments.md` — flag any commitments due today, this week, or overdue.
   - Include stale follow-ups and due commitments prominently in the briefing under "⏰ Attention Needed".

4) **Check today signals**
   - Calendar (next 24h): `gog calendar events --account {{GOG_ACCOUNT}} --all --days 1 --max 50`, filter to `{{CALENDAR_EMAIL}}`.
   - Unread {{COMPANY}} emails: `gog gmail search "from:{{COMPANY_DOMAIN}} is:unread" --max 10 --account {{GOG_ACCOUNT}}`.
   - Weather for your location: notify only if rain or severe weather.

5) **Email Triage** (if unread >= 1)
   - One-line summary per email + suggested action (reply/delegate/defer/FYI).
   - Flag urgent items at top.

6) **Meeting Prep** (if meeting within 4h)
   - Pull context from ACTIVE_WORK.md + recent daily notes.
   - Prepare 3-5 bullet talking points.

7) **Compose output**
   - Top 3 priorities for today.
   - ⚠️ Commitments due today or overdue (from commitments.md).
   - Blocker nudges (if any stale 3+ days).
   - Meeting prep (if applicable).
   - Email triage summary.
   - Risks / Follow-ups waiting on others.
   - Keep critical details in Artifacts section.

8) **Save to daily note**
   - Append morning briefing summary to `memory/TODAY.md` under a `## 🌅 Morning Briefing` section.
   - If the daily note doesn't exist yet, create it with standard template (🧠 Log / ✅ Done / 🧾 Decisions / 📌 Next Actions).
   - This ensures the Obsidian Push cron (23:05) will include morning context in the daily note.

## Tooling
- GOG_HOME={{GOG_HOME}}
- GOG_KEYRING_BACKEND=file
- GOG_KEYRING_PASSWORD: read from `{{WORKSPACE_PATH}}/secrets/gog_password.txt`

Present as a friendly morning briefing.
