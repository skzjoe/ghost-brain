# Example: Auto-Capture in Action

Ghost Brain captures context automatically during normal conversation. Here's what happens behind the scenes:

## You say:
> "คุยกับ Tom เรื่อง UAT timeline — เขาบอกต้องได้ environment ภายในสิ้นเดือน ผมรับปากแล้ว"

## Ghost Brain auto-captures:

### → `memory/people.md` (updated)
```markdown
### Acme Corp — Tom (IT Director)
- **Project:** ERP implementation
- **Context:** Decision-maker. Wants UAT by end of Jan.
- **Last mentioned:** 2026-01-20
```

### → `memory/commitments.md` (appended)
```markdown
| 2026-01-20 | Acme Corp (Tom) | UAT environment by end of January | Verbal commitment during call |
```

### → `memory/follow-ups.md` (appended)
```markdown
| Deliver UAT environment to Tom | Me | 2026-01-20 | 2026-01-31 | Committed; need server specs first |
```

### → Today's daily note (appended to 🧠 Log)
```markdown
- Call with Tom (Acme) — confirmed UAT delivery by end of month
```

---

Ghost Brain auto-captures context as you chat — no `/capture` command needed. It uses LLM understanding to detect commitments, people, and decisions from natural conversation. No special keywords required.

**`/logs` is your safety net.** Auto-capture catches most things in real-time, but running `/logs` before `/new` scans the full session and picks up anything that slipped through. Think of it like autosave + Ctrl+S before you close.

You can also capture manually:
```
/capture decision: Use PostgreSQL for the new project — better JSON support
/capture idea: Maybe build a client portal someday
/capture commitment: Told Sarah I'll review her PR within 24h
```
