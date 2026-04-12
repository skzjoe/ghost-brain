#!/usr/bin/env python3
"""
Ghost Brain — Unified Recall Layer

Combines multiple memory sources (SQLite+vec DB, file grep, structured files)
into one ranked result set. Importable AND CLI-usable.

Usage:
  ghost_unified_recall.py recall 'query' [--limit 10] [--sources all]
  ghost_unified_recall.py summary 'query'
  ghost_unified_recall.py capture 'content' [--context 'optional context']
  ghost_unified_recall.py user-model [--update type 'data'] [--show]
"""

import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

WORKSPACE = Path(os.environ.get(
    "OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace")))

USER_MODEL_PATH = WORKSPACE / "memory" / "user-model.md"

STRUCTURED_FILES = {
    "decision": WORKSPACE / "memory" / "decisions.md",
    "idea": WORKSPACE / "memory" / "ideas.md",
    "commitment": WORKSPACE / "memory" / "commitments.md",
    "follow-up": WORKSPACE / "memory" / "follow-ups.md",
    "person": WORKSPACE / "memory" / "people.md",
}

DAILY_NOTE_DIR = WORKSPACE / "memory"
LEARNINGS_DIR = WORKSPACE / ".learnings"

# Source filter sets
SOURCE_FILTERS = {
    "memory": {"memory"},
    "learnings": {"learnings"},
    "daily": {"daily"},
    "all": {"memory", "learnings", "daily"},
}

# ---------------------------------------------------------------------------
# GhostMemory import with graceful fallback
# ---------------------------------------------------------------------------

_ghost_memory_cls = None


def _get_ghost_memory():
    global _ghost_memory_cls
    if _ghost_memory_cls is not None:
        return _ghost_memory_cls
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from ghost_memory_db import GhostMemory
        _ghost_memory_cls = GhostMemory
        return GhostMemory
    except (ImportError, Exception):
        _ghost_memory_cls = False
        return False


def _get_scanner():
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from memory_content_scanner import scan_content, check_duplicate, check_file_size
        return scan_content, check_duplicate, check_file_size
    except ImportError:
        return None, None, None


# ---------------------------------------------------------------------------
# 1a. unified_recall
# ---------------------------------------------------------------------------

def unified_recall(
    query: str, limit: int = 10, sources: Optional[list] = None
) -> list[dict]:
    """Search across all memory layers, merge, deduplicate, and rank."""
    if not query or not query.strip():
        return []

    allowed = set()
    for s in (sources or ["all"]):
        allowed |= SOURCE_FILTERS.get(s, {"memory", "learnings", "daily"})

    results_by_key: dict[str, dict] = {}
    futures = {}

    with ThreadPoolExecutor(max_workers=3) as pool:
        if "memory" in allowed or "learnings" in allowed or "daily" in allowed:
            futures[pool.submit(_search_db, query, limit * 2)] = "db"
        if "memory" in allowed or "daily" in allowed:
            futures[pool.submit(_search_grep, query, limit * 2)] = "grep"

        for future in as_completed(futures):
            try:
                for item in future.result():
                    key = _dedup_key(item)
                    existing = results_by_key.get(key)
                    if existing is None or item.get("score", 0) > existing.get("score", 0):
                        results_by_key[key] = item
            except Exception:
                pass

    results = list(results_by_key.values())
    results = _filter_by_source(results, allowed)
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return results[:limit]


def _classify_source(file_path: str) -> str:
    if ".learnings" in file_path:
        return "learnings"
    if re.search(r"\d{4}-\d{2}-\d{2}", Path(file_path).name):
        return "daily"
    return "memory"


def _filter_by_source(results: list[dict], allowed: set) -> list[dict]:
    return [r for r in results if _classify_source(r.get("file", "")) in allowed]


def _dedup_key(item: dict) -> str:
    file_val = item.get("file", "")
    line_val = item.get("line", 0)
    snippet = item.get("snippet", "")[:80]
    return f"{file_val}:{line_val}:{snippet}"


def _search_db(query: str, limit: int) -> list[dict]:
    GhostMemory = _get_ghost_memory()
    if not GhostMemory:
        return []
    try:
        gm = GhostMemory()
        try:
            results = gm.search_hybrid(query, limit)
        except Exception:
            results = gm.search_fts(query, limit)
        finally:
            gm.close()

        out = []
        for r in results:
            match_type = r.get("match", "fts")
            if match_type == "both":
                score = 1.0
            elif match_type == "vec":
                score = 0.8
            else:
                score = 0.6
            out.append({
                "source": f"db:{match_type}",
                "file": r.get("source", ""),
                "line": 0,
                "snippet": r.get("snippet", r.get("title", "")),
                "score": score,
                "item_type": r.get("type", "unknown"),
                "date": r.get("date", ""),
            })
        return out
    except Exception:
        return []


def _search_grep(query: str, limit: int) -> list[dict]:
    out = []
    search_terms = query.lower().split()
    if not search_terms:
        return out

    scan_paths = []
    for md in DAILY_NOTE_DIR.glob("*.md"):
        scan_paths.append(md)
    for structured in STRUCTURED_FILES.values():
        if structured.exists():
            scan_paths.append(structured)

    for fpath in scan_paths:
        try:
            lines = fpath.read_text(encoding="utf-8").splitlines()
        except (OSError, IOError):
            continue
        rel = str(fpath.relative_to(WORKSPACE))
        for i, line in enumerate(lines, 1):
            lower_line = line.lower()
            matched = sum(1 for t in search_terms if t in lower_line)
            if matched == 0:
                continue
            score = 0.3 * (matched / len(search_terms))
            item_type = _guess_item_type_from_file(rel)
            date = _extract_date_from_path(rel)
            out.append({
                "source": "grep",
                "file": rel,
                "line": i,
                "snippet": line.strip()[:200],
                "score": score,
                "item_type": item_type,
                "date": date,
            })
        if len(out) >= limit:
            break

    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:limit]


def _guess_item_type_from_file(rel_path: str) -> str:
    name = Path(rel_path).stem
    type_map = {
        "decisions": "decision",
        "people": "person",
        "ideas": "idea",
        "commitments": "commitment",
        "follow-ups": "follow-up",
    }
    for key, val in type_map.items():
        if key in name:
            return val
    if re.match(r"\d{4}-\d{2}-\d{2}", name):
        return "daily_note"
    if ".learnings" in rel_path:
        return "learning"
    return "note"


def _extract_date_from_path(rel_path: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", rel_path)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# 1b. recall_summary
# ---------------------------------------------------------------------------

def recall_summary(query: str, limit: int = 5) -> str:
    """Format unified_recall results as a clean markdown summary."""
    results = unified_recall(query, limit=limit)
    if not results:
        return f"No results found for: **{query}**"

    grouped: dict[str, list[dict]] = {}
    for r in results:
        src = _classify_source(r.get("file", ""))
        grouped.setdefault(src, []).append(r)

    label_map = {
        "memory": "Structured Memory",
        "learnings": "Learnings",
        "daily": "Daily Notes",
    }

    parts = [f"## Recall: {query}\n"]
    for src_key in ("memory", "daily", "learnings"):
        items = grouped.get(src_key, [])
        if not items:
            continue
        parts.append(f"### {label_map.get(src_key, src_key)}")
        for item in items:
            file_ref = item.get("file", "?")
            snippet = item.get("snippet", "").strip()
            date = item.get("date", "")
            date_str = f" ({date})" if date else ""
            parts.append(f"- {snippet}{date_str}  \n  _Source: `{file_ref}`_")
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1c. smart_capture
# ---------------------------------------------------------------------------

_CAPTURE_PATTERNS = [
    ("decision", re.compile(
        r"\b(decided|decision|chose|picked|went with|settled on)\b", re.I)),
    ("commitment", re.compile(
        r"\b(promise|commit|will deliver|by friday|deadline|must ship|guaranteed)\b", re.I)),
    ("follow-up", re.compile(
        r"\b(waiting on|follow up|check with|pending from|remind me|get back to)\b", re.I)),
    ("person", re.compile(
        r"\b(คุณ\w+|role:|works at|contact:|reports to)\b", re.I)),
    ("learning", re.compile(
        r"\b(learned|mistake|better way|should have|next time|lesson|gotcha|pitfall)\b", re.I)),
    ("idea", re.compile(
        r"\b(idea|might|could try|what if|experiment|brainstorm|explore)\b", re.I)),
]

_TARGET_FILES = {
    "decision": "memory/decisions.md",
    "idea": "memory/ideas.md",
    "commitment": "memory/commitments.md",
    "follow-up": "memory/follow-ups.md",
    "person": "memory/people.md",
    "learning": ".learnings/LEARNINGS.md",
    "daily-log": None,
}


def smart_capture(content: str, context: str = "") -> dict:
    """Auto-detect content type and route to the correct memory file."""
    if not content or not content.strip():
        return {"type": "error", "file": "", "entry_text": "",
                "duplicate_warning": "Empty content"}

    detected_type = _detect_content_type(content)
    target_file = _resolve_target_file(detected_type)
    entry_text = _format_entry(detected_type, content, context)

    scan_content_fn, check_dup_fn, check_size_fn = _get_scanner()

    if scan_content_fn:
        scan_result = scan_content_fn(entry_text)
        if not scan_result.safe:
            return {"type": detected_type, "file": target_file,
                    "entry_text": entry_text,
                    "duplicate_warning": f"BLOCKED: {scan_result.reason}"}

    duplicate_warning = ""
    if check_dup_fn:
        abs_path = str(WORKSPACE / target_file)
        dup_result = check_dup_fn(abs_path, entry_text)
        if not dup_result.safe:
            duplicate_warning = dup_result.reason

    if not duplicate_warning:
        _append_to_file(target_file, entry_text)

    return {
        "type": detected_type,
        "file": target_file,
        "entry_text": entry_text,
        "duplicate_warning": duplicate_warning,
    }


def _detect_content_type(content: str) -> str:
    for type_name, pattern in _CAPTURE_PATTERNS:
        if pattern.search(content):
            return type_name
    return "daily-log"


def _resolve_target_file(content_type: str) -> str:
    explicit = _TARGET_FILES.get(content_type)
    if explicit:
        return explicit
    today = datetime.now().strftime("%Y-%m-%d")
    return f"memory/{today}.md"


def _format_entry(content_type: str, content: str, context: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    ctx = f" — {context}" if context else ""
    if content_type == "daily-log":
        return f"\n- {content}{ctx}\n"
    return f"\n## [{today}] {content}{ctx}\n"


def _append_to_file(rel_path: str, entry_text: str) -> None:
    abs_path = WORKSPACE / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "a", encoding="utf-8") as f:
        f.write(entry_text)


# ---------------------------------------------------------------------------
# 1d. update_user_model
# ---------------------------------------------------------------------------

_USER_MODEL_SECTIONS = [
    "Communication Preferences",
    "Technical Preferences",
    "Work Patterns",
    "Recurring Topics",
    "Corrections & Pet Peeves",
    "Decision Patterns",
]

_SIGNAL_TO_SECTION = {
    "correction": "Corrections & Pet Peeves",
    "preference": "Communication Preferences",
    "pattern": "Work Patterns",
    "feedback": "Corrections & Pet Peeves",
    "technical": "Technical Preferences",
    "topic": "Recurring Topics",
    "decision": "Decision Patterns",
}


def update_user_model(signal_type: str, signal_data: str) -> None:
    """Add a signal to the user model under the appropriate section."""
    if not signal_data or not signal_data.strip():
        return

    section = _SIGNAL_TO_SECTION.get(signal_type, "Corrections & Pet Peeves")
    model = _read_user_model_raw()
    model = _add_to_section(model, section, signal_data.strip())
    model = _enforce_line_limit(model, 100)
    model = _update_timestamp(model)
    USER_MODEL_PATH.write_text(model, encoding="utf-8")


def _read_user_model_raw() -> str:
    if USER_MODEL_PATH.exists():
        return USER_MODEL_PATH.read_text(encoding="utf-8")
    return _default_user_model()


def _add_to_section(model: str, section_name: str, bullet: str) -> str:
    header = f"## {section_name}"
    if header not in model:
        model = model.rstrip() + f"\n\n{header}\n- {bullet}\n"
        return model

    lines = model.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            insert_idx = i + 1
            while insert_idx < len(lines) and (
                lines[insert_idx].startswith("- ") or lines[insert_idx].strip() == ""
            ):
                insert_idx += 1
            break

    if insert_idx is not None:
        lines.insert(insert_idx, f"- {bullet}")
    return "\n".join(lines)


def _enforce_line_limit(model: str, max_lines: int) -> str:
    lines = model.split("\n")
    if len(lines) <= max_lines:
        return model
    return "\n".join(lines[:max_lines]) + "\n"


def _update_timestamp(model: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    pattern = r"_Auto-maintained by Ghost Brain\. Last updated: [^_]*_"
    replacement = f"_Auto-maintained by Ghost Brain. Last updated: {today}_"
    if re.search(pattern, model):
        return re.sub(pattern, replacement, model)
    return model.rstrip() + f"\n\n{replacement}\n"


def _default_user_model() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""# User Model

## Communication Preferences
- Concise, accurate, direct
- Wants advanced frameworks, not basic advice
- Thai + English mix in conversation
- Prefers actionable output over explanations

## Technical Preferences
- ERPNext/Frappe ecosystem
- Prisma v6 (avoid v7)
- Python for scripts, Node.js for apps
- WSL2 development environment

## Work Patterns
- (your role here)
- Multiple concurrent projects
- Prefers reactive support over proactive micromanagement on stable projects
- Values critique-by-default

## Recurring Topics
- ERPNext customization
- Client project delivery
- Ghost Brain system improvement
- Meta Ads automation

## Corrections & Pet Peeves
- Don't promote notes to commitments without explicit signal
- Don't guess when info is incomplete — ask
- Preserve exact project names from source material
- OpenClaw cron ≠ system crontab

## Decision Patterns
- Pragmatic — picks working solution over theoretically perfect one
- Values speed to delivery
- Willing to park things that aren't urgent
- Prefers recoverable actions over destructive ones

_Auto-maintained by Ghost Brain. Last updated: {today}_
"""


# ---------------------------------------------------------------------------
# 1e. get_user_model
# ---------------------------------------------------------------------------

def get_user_model() -> dict:
    """Parse memory/user-model.md into a structured dict."""
    model_text = _read_user_model_raw()

    result = {
        "preferences": {},
        "patterns": {},
        "corrections": [],
        "topics": [],
    }

    section_mapping = {
        "Communication Preferences": ("preferences", "communication"),
        "Technical Preferences": ("preferences", "technical"),
        "Work Patterns": ("patterns", "work"),
        "Decision Patterns": ("patterns", "decision"),
        "Recurring Topics": ("topics", None),
        "Corrections & Pet Peeves": ("corrections", None),
    }

    current_section = None
    for line in model_text.splitlines():
        header_match = re.match(r"^## (.+)$", line.strip())
        if header_match:
            current_section = header_match.group(1).strip()
            continue

        if not current_section:
            continue

        bullet_match = re.match(r"^- (.+)$", line.strip())
        if not bullet_match:
            continue
        value = bullet_match.group(1).strip()

        mapping = section_mapping.get(current_section)
        if not mapping:
            continue

        target_key, sub_key = mapping
        if target_key in ("topics", "corrections"):
            result[target_key].append(value)
        elif sub_key:
            result[target_key].setdefault(sub_key, [])
            result[target_key][sub_key].append(value)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghost_unified_recall",
        description="Ghost Brain unified recall layer")
    sub = parser.add_subparsers(dest="command")

    p_recall = sub.add_parser("recall", help="Search all memory layers")
    p_recall.add_argument("query", help="Search query")
    p_recall.add_argument("--limit", type=int, default=10)
    p_recall.add_argument("--sources", default="all")

    p_summary = sub.add_parser("summary", help="Formatted recall summary")
    p_summary.add_argument("query", help="Search query")
    p_summary.add_argument("--limit", type=int, default=5)

    p_capture = sub.add_parser("capture", help="Smart capture content")
    p_capture.add_argument("content", help="Content to capture")
    p_capture.add_argument("--context", default="")

    p_um = sub.add_parser("user-model", help="View or update user model")
    p_um.add_argument("--show", action="store_true", help="Show parsed model")
    p_um.add_argument("--update", nargs=2, metavar=("TYPE", "DATA"),
                       help="Update model: --update correction 'data'")

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "recall":
        src_list = [s.strip() for s in args.sources.split(",")]
        results = unified_recall(args.query, limit=args.limit, sources=src_list)
        if not results:
            print("No results found.")
            return
        for r in results:
            score = r.get("score", 0)
            print(f"[{score:.2f}] {r.get('item_type', '?'):12s} "
                  f"{r.get('file', '?'):40s} {r.get('snippet', '')[:80]}")

    elif args.command == "summary":
        print(recall_summary(args.query, limit=args.limit))

    elif args.command == "capture":
        result = smart_capture(args.content, context=args.context)
        print(f"Type:    {result['type']}")
        print(f"File:    {result['file']}")
        if result.get("duplicate_warning"):
            print(f"Warning: {result['duplicate_warning']}")
        else:
            print("Status:  captured")

    elif args.command == "user-model":
        if args.update:
            signal_type, signal_data = args.update
            update_user_model(signal_type, signal_data)
            print(f"Updated user model ({signal_type}): {signal_data}")
        else:
            import json
            model = get_user_model()
            print(json.dumps(model, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
