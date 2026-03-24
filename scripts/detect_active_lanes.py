#!/usr/bin/env python3
"""Detect which GHOST_PLAYBOOK fast lanes are most relevant this week.
Scans recent daily notes for keyword signals and outputs ranked lanes.
Zero LLM cost — pure keyword matching."""

import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
    os.path.expanduser("~/.openclaw/workspace")))

# Fast lane keywords — each lane has trigger words
LANE_SIGNALS = {
    "ERP / Frappe": ["erpnext", "frappe", "doctype", "custom script", "client script", "server script", "print format", "naming series", "workflow", "stock entry", "sales invoice", "purchase", "item master", "bom"],
    "Docs / Specs": ["documentation", "manual", "mdx", "nextra", "spec", "artifact", "template", "document"],
    "Debug": ["error", "bug", "fix", "traceback", "exception", "failed", "broken", "debug", "issue"],
    "Decision Support": ["decision", "should we", "which option", "compare", "tradeoff", "recommend"],
    "Marketing / Ads": ["meta ads", "facebook", "campaign", "ad set", "creative", "audience", "landing page", "conversion"],
    "Negotiation": ["negotiation", "proposal", "quote", "pricing", "contract", "deal", "quotation"],
    "Calendar / Email Triage": ["calendar", "meeting", "email", "schedule", "appointment", "invite"],
    "CTO Planning": ["priority", "roadmap", "strategy", "planning", "next quarter", "okr", "kpi"],
    "Team Management": ["1:1", "expectation", "performance", "team", "ba ", "developer", "training"],
    "Trading / EA": ["mt5", "ea ", "backtest", "drawdown", "profit factor", "trading"],
    "Product Launch / Sales": ["launch", "pricing", "gumroad", "lemonsqueezy", "checkout", "payment link", "sales page"],
    "WordPress / Client Delivery": ["wordpress", "elementor", "zipwp", "piyapodok", "client delivery", "hosting"],
    "Product / System Ops": ["cron", "audit", "heartbeat", "ghost brain", "memory db", "pipeline", "backup", "resilience"],
}

def scan_recent_notes(days=7):
    """Read last N days of daily notes and return combined text."""
    texts = []
    for i in range(days):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        note = WORKSPACE / "memory" / f"{d}.md"
        if note.exists():
            texts.append(note.read_text().lower())
    return "\n".join(texts)

def detect_lanes(text, top_n=5):
    """Score each lane by keyword hits and return ranked list."""
    scores = Counter()
    for lane, keywords in LANE_SIGNALS.items():
        for kw in keywords:
            count = text.count(kw.lower())
            if count > 0:
                scores[lane] += count
    return scores.most_common(top_n)

def main():
    text = scan_recent_notes(7)
    if not text.strip():
        print("No recent notes found")
        return

    ranked = detect_lanes(text)
    if not ranked:
        print("No lane signals detected")
        return

    # Write to file
    out_path = WORKSPACE / ".local" / "active_lanes.txt"
    lines = []
    for lane, score in ranked:
        lines.append(f"{lane} ({score})")
    out_path.write_text("\n".join(lines))

    print(f"Top {len(ranked)} active fast lanes (from last 7 days):")
    for lane, score in ranked:
        print(f"  {lane}: {score} signals")

if __name__ == "__main__":
    main()
