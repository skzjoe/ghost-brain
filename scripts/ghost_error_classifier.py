#!/usr/bin/env python3
"""
ghost_error_classifier.py — Ghost structured error taxonomy + recovery hints.

Classifies tool/command/API failures into categories with actionable recovery hints.
Ghost uses this to log structured entries to .learnings/ERRORS.md instead of free-text.

Usage:
    python3 scripts/ghost_error_classifier.py "error message"        # classify + print
    python3 scripts/ghost_error_classifier.py --log "msg" "context"  # classify + append to ERRORS.md
    python3 scripts/ghost_error_classifier.py --list                  # show all categories

From Python:
    from ghost_error_classifier import classify, log_error
"""

import os, sys, re, json, argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace
ERRORS_FILE = _paths.learnings_dir / "ERRORS.md"

# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------

@dataclass
class ErrorClass:
    code: str
    label: str
    retryable: bool
    recovery: str
    escalate: bool = False  # True = worth promoting to LEARNINGS.md


TAXONOMY: list[ErrorClass] = [
    ErrorClass("exec_blocked",     "Exec preflight blocked",       False,
               "Rewrite command: no heredoc, no complex interpreter invocation. Use Write tool for files."),
    ErrorClass("git_lock",         "Git index.lock conflict",      True,
               "Run: rm -f <vault>/.git/index.lock then retry. Usually caused by concurrent git processes."),
    ErrorClass("vault_unmounted",  "Obsidian vault not mounted",   True,
               "iCloud drive may not be accessible from WSL. Check /mnt/c/Users/passa/iCloudDrive/. Retry in ~30s."),
    ErrorClass("python_env",       "Wrong Python runtime",         False,
               "Use /home/linuxbrew/.linuxbrew/bin/python3 for sqlite-vec scripts. Not system python3."),
    ErrorClass("frappe_auth",      "Frappe/MCP auth failure",      True,
               "Check secrets/frappe_mcp.json. Re-run mcporter auth if token expired."),
    ErrorClass("rate_limit",       "API rate limit (429)",         True,
               "Wait 60s then retry. Reduce batch size. Check rate limit rules in AGENTS.md."),
    ErrorClass("browser_unavail",  "Browser not available",        True,
               "Check: openclaw gateway status. WSLg: verify DISPLAY=:0 is set. Restart gateway if needed."),
    ErrorClass("memory_blocked",   "Memory content scanner blocked write", False,
               "Content failed injection/exfil/unicode scan. Review content before forcing write."),
    ErrorClass("tool_timeout",     "Tool/exec timeout",            True,
               "Increase timeout or break into smaller steps. Check if process is hanging."),
    ErrorClass("cron_failed",      "Scheduled cron job failed",    False,
               "Check openclaw cron list. Review cron script for errors. Re-run manually to diagnose."),
    ErrorClass("icloud_sync",      "iCloud sync conflict/delay",   True,
               "Wait 30-60s for iCloud to sync. If persistent, check Windows iCloud app status."),
    ErrorClass("merge_abort",      "Obsidian merge aborted (size sanity)", False,
               "Merged result < 85% of original — possible data loss. Review src/dest manually before retrying."),
    ErrorClass("unknown",          "Unclassified error",           False,
               "Log full error, check .learnings/ERRORS.md for similar patterns. Consider promoting if recurring."),
]

TAXONOMY_MAP = {e.code: e for e in TAXONOMY}

# Patterns for classification (ordered: first match wins)
PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"heredoc|complex interpreter|preflight", re.I), "exec_blocked"),
    (re.compile(r"index\.lock|Another git process", re.I),       "git_lock"),
    (re.compile(r"vault not mounted|iCloudDrive|not accessible", re.I), "vault_unmounted"),
    (re.compile(r"sqlite.vec|linuxbrew.*python|wrong.*runtime", re.I),  "python_env"),
    (re.compile(r"frappe|mcp.*auth|token expired|401", re.I),    "frappe_auth"),
    (re.compile(r"429|rate.?limit|too many requests", re.I),     "rate_limit"),
    (re.compile(r"browser|DISPLAY|WSLg|playwright|chromium", re.I), "browser_unavail"),
    (re.compile(r"injection|exfil|unicode|scanner.*block", re.I),"memory_blocked"),
    (re.compile(r"timeout|timed out|deadline", re.I),            "tool_timeout"),
    (re.compile(r"cron|scheduled.*fail|cron.*error", re.I),      "cron_failed"),
    (re.compile(r"iCloud.*sync|sync.*conflict|icloud", re.I),    "icloud_sync"),
    (re.compile(r"merge.*abort|85%|size sanity", re.I),          "merge_abort"),
]


def classify(error_msg: str) -> ErrorClass:
    """Classify an error message into the nearest ErrorClass."""
    for pattern, code in PATTERNS:
        if pattern.search(error_msg):
            return TAXONOMY_MAP[code]
    return TAXONOMY_MAP["unknown"]


def _next_err_id(path: Path) -> str:
    """Generate next ERR-YYYYMMDD-NNN style ID."""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"ERR-{today}-"
    count = 1
    if path.exists():
        content = path.read_text()
        import re
        matches = re.findall(rf"\[{re.escape(prefix)}(\d+)\]", content)
        if matches:
            count = max(int(m) for m in matches) + 1
    return f"{prefix}{count:03d}"


def format_entry(error_msg: str, context: str, ec: ErrorClass, date: str) -> str:
    err_id = _next_err_id(ERRORS_FILE)
    retryable = "yes" if ec.retryable else "no"
    escalate = "\n**Escalate:** yes — consider promoting to LEARNINGS.md" if ec.escalate else ""
    return (
        f"\n## [{err_id}] {ec.label} (`{ec.code}`)\n"
        f"\n**Logged:** {date}\n"
        f"**Status:** 🔴 open\n"
        f"**Context:** {context.strip() if context else 'n/a'}\n"
        f"**Error:** {error_msg.strip()}\n"
        f"**Retryable:** {retryable}\n"
        f"**Recovery:** {ec.recovery}{escalate}\n"
    )


def log_error(error_msg: str, context: str = "") -> ErrorClass:
    """Classify error and append structured entry to ERRORS.md. Returns the ErrorClass."""
    ec = classify(error_msg)
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = format_entry(error_msg, context, ec, date)

    ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ERRORS_FILE, "a") as f:
        f.write(entry)

    return ec


def main():
    parser = argparse.ArgumentParser(description="Ghost error classifier")
    parser.add_argument("error", nargs="?", help="Error message to classify")
    parser.add_argument("context", nargs="?", default="", help="Context (tool/script/step)")
    parser.add_argument("--log", action="store_true", help="Also append to ERRORS.md")
    parser.add_argument("--list", action="store_true", help="List all error categories")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.list:
        print("\n📋 Ghost Error Taxonomy\n")
        for ec in TAXONOMY:
            r = "↺ retryable" if ec.retryable else "✗ not retryable"
            print(f"  {ec.code:<20} {ec.label} ({r})")
            print(f"    → {ec.recovery[:80]}...")
        print()
        return

    if not args.error:
        parser.print_help()
        sys.exit(1)

    ec = classify(args.error)

    if args.log:
        log_error(args.error, args.context)

    if args.json:
        print(json.dumps({**asdict(ec), "logged": args.log}, ensure_ascii=False, indent=2))
    else:
        r = "↺ retryable" if ec.retryable else "✗ not retryable"
        print(f"\n🔍 {ec.label} ({ec.code}) — {r}")
        print(f"   Recovery: {ec.recovery}\n")


if __name__ == "__main__":
    main()
