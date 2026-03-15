---
name: health
description: "Run openclaw security audit --deep and openclaw update status, then report findings."
user-invocable: true
---

# /health

Deep security and system health check.

## Instructions

1. `openclaw security audit --deep`
2. `openclaw update status`
3. `ss -ltnp` (listening ports)
4. Check systemd service status: `systemctl --user status openclaw-gateway`
5. Present findings with severity:
   - 🔴 Critical — fix now
   - 🟡 Warning — fix soon
   - 🟢 Info — awareness only
6. Recommend fixes for any issues found
