#!/usr/bin/env python3
"""
ghost_usage_insights.py — Ghost Brain Usage Analytics
Parses commands.log + daily notes to surface session patterns, model usage, and work themes.

Usage:
    python3 scripts/ghost_usage_insights.py              # last 30 days
    python3 scripts/ghost_usage_insights.py --days 7     # last 7 days
    python3 scripts/ghost_usage_insights.py --week       # current week
    python3 scripts/ghost_usage_insights.py --month      # current month
    python3 scripts/ghost_usage_insights.py --json       # machine-readable output
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter

from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace
COMMANDS_LOG = Path(os.environ.get("OPENCLAW_COMMANDS_LOG", str(Path.home() / ".openclaw/logs/commands.log")))
MEMORY_DIR = _paths.memory_dir

MODEL_ALIASES = {
    "sonnet": "claude-sonnet",
    "opus": "claude-opus",
    "claude-sonnet": "claude-sonnet",
    "claude-opus": "claude-opus",
    "gpt-5.4": "gpt-5.4",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
}

AGENT_LABELS = {
    "agent:main:main": "Ghost (main)",
    "agent:main:telegram": "Ghost (Telegram group)",
    "agent:ops": "Ops agent",
    "agent:lab": "Lab agent",
    "agent:general": "General agent",
    "agent:team": "Team agent",
    "agent:phantom": "Personal agent",
    "agent:phantom-fam": "Family agent",
}

def label_agent(key: str) -> str:
    for prefix, label in AGENT_LABELS.items():
        if key.startswith(prefix):
            return label
    return key.split(":")[1] if ":" in key else key


def load_sessions(since: datetime) -> list[dict]:
    if not COMMANDS_LOG.exists():
        return []
    sessions = []
    with open(COMMANDS_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("timestamp", "")
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= since:
                    sessions.append({**entry, "_ts": ts})
            except Exception:
                continue
    return sessions


def parse_daily_notes(since: datetime) -> dict:
    """Extract model mentions and session themes from daily notes."""
    model_counts = Counter()
    themes = Counter()
    work_days = set()
    errors_found = 0

    since_date = since.date()
    for note_file in sorted(MEMORY_DIR.glob("20*.md")):
        # Extract date from filename
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", note_file.name)
        if not m:
            continue
        note_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        if note_date < since_date:
            continue

        text = note_file.read_text(errors="replace")
        work_days.add(note_date)

        # Model mentions
        for alias, canon in MODEL_ALIASES.items():
            count = len(re.findall(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE))
            if count:
                model_counts[canon] += count

        # Theme keywords
        keywords = {
            "Business Systems": ["erpnext", "frappe", "doctype", "erp", "crm"],
            "Marketing Ops": ["meta ads", "facebook", "campaign", "ads manager", "advertising"],
            "Ghost Brain": ["ghost brain", "ghost", "memory", "heartbeat", "learning"],
            "Client Delivery": ["project atlas", "client delivery", "migration", "handoff"],
            "LifeOps": ["phantom", "fam fund"],
            "Coding": ["claude code", "codex", "script", "python", "deploy"],
            "Docs": ["document", "pdf", "manual", "เอกสาร"],
            "Northstar": ["awc", "aw client"],
        }
        for theme, kws in keywords.items():
            for kw in kws:
                if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
                    themes[theme] += 1
                    break

        # Error indicators
        errors_found += len(re.findall(r"\b(error|failed|fix|bug|broken|issue)\b", text, re.IGNORECASE))

    return {
        "model_counts": dict(model_counts),
        "themes": dict(themes),
        "work_days": sorted(str(d) for d in work_days),
        "error_signal": errors_found,
    }


def analyze_sessions(sessions: list[dict]) -> dict:
    by_day: dict[str, list] = defaultdict(list)
    by_hour: Counter = Counter()
    by_agent: Counter = Counter()
    by_source: Counter = Counter()

    for s in sessions:
        ts = s["_ts"].astimezone()
        day = ts.strftime("%Y-%m-%d")
        hour = ts.hour
        agent = label_agent(s.get("sessionKey", "unknown"))
        source = s.get("source", "unknown")

        by_day[day].append(s)
        by_hour[hour] += 1
        by_agent[agent] += 1
        by_source[source] += 1

    # Busiest day
    busiest_day = max(by_day, key=lambda d: len(by_day[d])) if by_day else None
    busiest_hour = by_hour.most_common(1)[0][0] if by_hour else None

    # Sessions per day average
    if by_day:
        total = sum(len(v) for v in by_day.values())
        avg_per_day = total / len(by_day)
    else:
        avg_per_day = 0

    return {
        "total_sessions": len(sessions),
        "active_days": len(by_day),
        "avg_sessions_per_day": round(avg_per_day, 1),
        "busiest_day": busiest_day,
        "busiest_day_count": len(by_day[busiest_day]) if busiest_day else 0,
        "busiest_hour": f"{busiest_hour:02d}:00" if busiest_hour is not None else None,
        "by_agent": dict(by_agent.most_common()),
        "by_source": dict(by_source.most_common()),
        "sessions_by_day": {d: len(v) for d, v in sorted(by_day.items())},
    }


def format_bar(value: int, max_value: int, width: int = 20) -> str:
    if max_value == 0:
        return ""
    filled = int(value / max_value * width)
    return "█" * filled + "░" * (width - filled)


def print_insights(session_stats: dict, note_stats: dict, days: int):
    print(f"\n{'='*55}")
    print(f"  👻 Ghost Usage Insights — Last {days} days")
    print(f"{'='*55}\n")

    # Session overview
    print("📊 Sessions")
    print(f"  Total:        {session_stats['total_sessions']}")
    print(f"  Active days:  {session_stats['active_days']}")
    print(f"  Avg/day:      {session_stats['avg_sessions_per_day']}")
    if session_stats["busiest_day"]:
        print(f"  Busiest day:  {session_stats['busiest_day']} ({session_stats['busiest_day_count']} sessions)")
    if session_stats["busiest_hour"]:
        print(f"  Peak hour:    {session_stats['busiest_hour']}")

    # Agent breakdown
    if session_stats["by_agent"]:
        print("\n🤖 By Agent")
        max_v = max(session_stats["by_agent"].values())
        for agent, count in session_stats["by_agent"].items():
            bar = format_bar(count, max_v, 15)
            print(f"  {bar} {count:3d}  {agent}")

    # Sessions by day (mini sparkline)
    if session_stats["sessions_by_day"]:
        print("\n📅 Daily Activity (recent)")
        items = list(session_stats["sessions_by_day"].items())[-14:]  # last 14 days
        max_v = max(v for _, v in items) if items else 1
        for day, count in items:
            bar = format_bar(count, max_v, 12)
            print(f"  {day}  {bar} {count}")

    # Model usage (from daily note mentions)
    if note_stats["model_counts"]:
        print("\n🧠 Model Mentions (from daily notes)")
        max_v = max(note_stats["model_counts"].values())
        for model, count in sorted(note_stats["model_counts"].items(), key=lambda x: -x[1]):
            bar = format_bar(count, max_v, 15)
            print(f"  {bar} {count:3d}  {model}")
    else:
        print("\n🧠 Model Mentions: none found in notes")

    # Work themes
    if note_stats["themes"]:
        print("\n🎯 Work Themes (from daily notes)")
        max_v = max(note_stats["themes"].values())
        for theme, count in sorted(note_stats["themes"].items(), key=lambda x: -x[1]):
            bar = format_bar(count, max_v, 15)
            print(f"  {bar} {count:3d}  {theme}")

    # Error signal
    if note_stats["error_signal"] > 0:
        print(f"\n⚠️  Error signal: {note_stats['error_signal']} error/fix/bug mentions in notes")

    print(f"\n{'='*55}")
    print("  💡 Tip: no native token counts (OpenClaw doesn't expose API)")
    print(f"{'='*55}\n")


def main():
    parser = argparse.ArgumentParser(description="Ghost usage insights")
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days (default: 30)")
    parser.add_argument("--week", action="store_true", help="Current week (Mon–today)")
    parser.add_argument("--month", action="store_true", help="Current month")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    if args.week:
        days = (now.weekday()) + 1  # days since Monday
        args.days = max(days, 1)
    elif args.month:
        args.days = now.day

    since = now - timedelta(days=args.days)

    sessions = load_sessions(since)
    session_stats = analyze_sessions(sessions)
    note_stats = parse_daily_notes(since)

    if args.json:
        print(json.dumps({
            "period_days": args.days,
            "since": since.isoformat(),
            "sessions": session_stats,
            "notes": note_stats,
        }, ensure_ascii=False, indent=2))
    else:
        print_insights(session_stats, note_stats, args.days)


if __name__ == "__main__":
    main()
