---
name: health
description: "Quick health check — memory freshness, capture activity, cron status, security, and heartbeat. Lighter than /audit."
user-invocable: true
---

# /health

Quick system health check. Lighter and faster than /audit — focuses on "is everything working?" not "how good is the system?"

## Instructions

Run all checks, then compose the output.

### Checks

1. **Memory freshness**
   - `MEMORY.md` last updated date
   - Today's daily note exists?
   - Daily notes written in last 7 days (count)

2. **Capture activity** (last 7 days)
   - Decisions logged (count entries with dates in last 7d)
   - People updated (any entries with "Last mentioned" in last 7d)
   - Ideas captured (count with dates in last 7d)
   - Commitments tracked (active count)
   - Follow-ups active (count + any stale >14d)

3. **Cron health**
   - Run `openclaw cron list` (NOT `crontab -l` — OpenClaw has its own cron system)
   - Count total jobs, count status=ok, count status=error/failed
   - Flag any errored jobs by name

4. **Gateway status**
   - Run `openclaw gateway status`
   - Report: running/stopped, RPC ok/fail, any doctor warnings

5. **Security**
   - Run `openclaw security audit`
   - Report: critical/warn/info counts

6. **Heartbeat**
   - `heartbeat-state.json` → lastRunAt (how long ago?)
   - heartbeat_pulse.sh exists and executable?

7. **Disk/workspace**
   - `MEMORY.md` size (flag if >15KB)
   - `backups/` latest file date
   - Git last commit date

### Output Format

```
👻 Health Check — {date time}

🧠 Memory: {status emoji} {detail}
📋 Capture: {X}/5 active | {detail}
⚙️ Cron: {ok count}/{total} healthy | {errors if any}
⚡ Gateway: {running/stopped} | RPC {ok/fail}
🔒 Security: {critical}c · {warn}w · {info}i
💓 Heartbeat: last run {time ago} | {status}
💾 Workspace: MEMORY {size} | backup {age} | git {age}

{only if problems:}
🔴 Issues:
- {issue 1}
- {issue 2}
```

### Health Emoji Guide
- ✅ = healthy
- ⚠️ = degraded / attention needed
- ❌ = broken / critical
