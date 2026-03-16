#!/usr/bin/env python3
"""
Ghost Brain — Spaced Repetition for Learnings
Surfaces due learnings based on simplified SM-2 intervals.
No external DB — uses a JSON state file alongside existing markdown learnings.

Usage:
  python3 learning_review.py due          # Show items due for review today
  python3 learning_review.py reinforce ID # Mark a learning as applied/reinforced
  python3 learning_review.py init         # Scan all learnings and initialize state
  python3 learning_review.py stats        # Show Learning Review statistics
  python3 learning_review.py dismiss ID   # Dismiss (skip) a learning for this cycle
  python3 learning_review.py scan         # Re-scan learnings and sync state
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
    os.path.expanduser("~/.openclaw/workspace")))
LEARNINGS_DIR = WORKSPACE / ".learnings"
STATE_FILE = LEARNINGS_DIR / "learning-review-state.json"

# Interval ladder (days): each successful review advances to next level
INTERVALS = [1, 3, 7, 14, 30, 60, 120]
MAX_LEVEL = len(INTERVALS) - 1

# Priority weights — higher priority = more frequent resurfacing
PRIORITY_WEIGHT = {
    "critical": 0.5,   # halve intervals
    "high": 0.75,
    "medium": 1.0,
    "low": 1.5,        # stretch intervals
}


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"items": {}, "last_scan": None, "version": 1}


def save_state(state):
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def scan_learnings():
    """Parse all learning entries from markdown files."""
    items = {}
    files_to_scan = [
        LEARNINGS_DIR / "LEARNINGS.md",
        LEARNINGS_DIR / "ERRORS.md",
    ]
    # Add domain files
    domains_dir = LEARNINGS_DIR / "domains"
    if domains_dir.exists():
        files_to_scan.extend(domains_dir.glob("*.md"))
    # Add project files (skip README)
    projects_dir = LEARNINGS_DIR / "projects"
    if projects_dir.exists():
        files_to_scan.extend(p for p in projects_dir.glob("*.md") if p.name != "README.md")

    for filepath in files_to_scan:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        pattern = r'## \[((?:LRN|ERR)-\d{8}-\d{3})\]\s+(\S+).*?\n(.*?)(?=\n## \[|$)'
        for match in re.finditer(pattern, content, re.DOTALL):
            entry_id = match.group(1)
            block = match.group(3)

            summary = ""
            priority = "medium"
            status = "active"
            area = ""

            for line in block.split("\n"):
                if line.startswith("**Priority**:"):
                    priority = line.split(":", 1)[1].strip().strip("*")
                elif line.startswith("**Status**:"):
                    status = line.split(":", 1)[1].strip().strip("*")
                elif line.startswith("**Area**:"):
                    area = line.split(":", 1)[1].strip().strip("*")
                elif not summary and line.strip() and not line.startswith("**") and not line.startswith("###") and not line.startswith("- "):
                    summary = line.strip()

            if status in ("active", "pending", "promoted"):
                source_file = str(filepath.relative_to(LEARNINGS_DIR))
                items[entry_id] = {
                    "id": entry_id,
                    "summary": summary[:200] if summary else f"[{entry_id}] in {source_file}",
                    "priority": priority,
                    "area": area,
                    "source": source_file,
                }
    return items


def init_state(state, items):
    today = datetime.now().strftime("%Y-%m-%d")
    new_count = 0
    for item_id in items:
        if item_id not in state["items"]:
            state["items"][item_id] = {
                "level": 0,
                "next_review": today,
                "last_reviewed": None,
                "times_surfaced": 0,
                "times_reinforced": 0,
                "graduated": False,
            }
            new_count += 1

    stale = [k for k in state["items"] if k not in items]
    for k in stale:
        del state["items"][k]

    state["last_scan"] = today
    return new_count, len(stale)


def get_due_items(state, items, limit=5):
    today = datetime.now().strftime("%Y-%m-%d")
    due = []
    for item_id, sr in state["items"].items():
        if sr.get("graduated"):
            continue
        if sr["next_review"] <= today and item_id in items:
            due.append({**items[item_id], "sr": sr})

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    due.sort(key=lambda x: (priority_order.get(x["priority"], 2), x["sr"]["next_review"]))
    return due[:limit]


def reinforce(state, item_id):
    if item_id not in state["items"]:
        print(f"❌ Unknown item: {item_id}")
        return False

    sr = state["items"][item_id]
    today = datetime.now().strftime("%Y-%m-%d")
    sr["last_reviewed"] = today
    sr["times_reinforced"] = sr.get("times_reinforced", 0) + 1

    if sr["level"] < MAX_LEVEL:
        sr["level"] += 1
    else:
        sr["graduated"] = True
        sr["next_review"] = "9999-12-31"
        print(f"🎓 {item_id} graduated! (reviewed {sr['times_reinforced']} times)")
        return True

    interval = INTERVALS[sr["level"]]
    next_date = datetime.now() + timedelta(days=interval)
    sr["next_review"] = next_date.strftime("%Y-%m-%d")
    print(f"✅ {item_id} reinforced → level {sr['level']}, next review: {sr['next_review']}")
    return True


def dismiss(state, item_id):
    if item_id not in state["items"]:
        print(f"❌ Unknown item: {item_id}")
        return False

    sr = state["items"][item_id]
    today = datetime.now().strftime("%Y-%m-%d")
    sr["last_reviewed"] = today
    sr["times_surfaced"] = sr.get("times_surfaced", 0) + 1

    interval = INTERVALS[min(sr["level"], MAX_LEVEL)]
    next_date = datetime.now() + timedelta(days=interval)
    sr["next_review"] = next_date.strftime("%Y-%m-%d")
    print(f"⏭️ {item_id} dismissed → same level {sr['level']}, next review: {sr['next_review']}")
    return True


def show_stats(state, items):
    total = len(state["items"])
    graduated = sum(1 for s in state["items"].values() if s.get("graduated"))
    today = datetime.now().strftime("%Y-%m-%d")
    due = sum(1 for s in state["items"].values() if not s.get("graduated") and s["next_review"] <= today)

    levels = {}
    for s in state["items"].values():
        if not s.get("graduated"):
            lvl = s["level"]
            levels[lvl] = levels.get(lvl, 0) + 1

    print(f"📊 Learning Review Stats")
    print(f"   Total tracked: {total}")
    print(f"   Due today: {due}")
    print(f"   Graduated: {graduated}")
    print(f"   Level distribution:")
    for lvl in sorted(levels.keys()):
        bar = "█" * levels[lvl]
        print(f"     L{lvl} ({INTERVALS[lvl]}d): {levels[lvl]} {bar}")


def format_due_for_cron(due_items):
    if not due_items:
        print("HEARTBEAT_OK")
        return
    print(f"🔄 {len(due_items)} learning(s) due for review:")
    print()
    for item in due_items:
        sr = item["sr"]
        emoji = "🔴" if item["priority"] == "critical" else "🟡" if item["priority"] == "high" else "⚪"
        print(f"{emoji} [{item['id']}] {item['summary']}")
        print(f"   Area: {item['area']} | Level: {sr['level']}/{MAX_LEVEL} | Source: {item['source']}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    state = load_state()
    items = scan_learnings()

    if cmd == "init":
        new, stale = init_state(state, items)
        save_state(state)
        print(f"✅ Initialized: {new} new, {stale} removed, {len(state['items'])} total")

    elif cmd == "due":
        if not state["items"]:
            init_state(state, items)
            save_state(state)
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        due = get_due_items(state, items, limit=limit)
        format_due_for_cron(due)

    elif cmd == "reinforce":
        if len(sys.argv) < 3:
            print("Usage: learning_review.py reinforce <ID>"); return
        reinforce(state, sys.argv[2])
        save_state(state)

    elif cmd == "dismiss":
        if len(sys.argv) < 3:
            print("Usage: learning_review.py dismiss <ID>"); return
        dismiss(state, sys.argv[2])
        save_state(state)

    elif cmd == "stats":
        if not state["items"]:
            init_state(state, items)
            save_state(state)
        show_stats(state, items)

    elif cmd == "scan":
        new, stale = init_state(state, items)
        save_state(state)
        print(f"🔍 Scanned: {new} new, {stale} removed, {len(state['items'])} total")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
