#!/usr/bin/env python3
"""
Ghost Brain — Unified Recall Layer

Combines multiple memory sources (SQLite+vec DB, file grep, structured files)
into one ranked result set. Importable AND CLI-usable.

Usage:
  ghost_unified_recall.py recall 'query' [--limit 10] [--sources all]
  ghost_unified_recall.py summary 'query'
  ghost_unified_recall.py report 'query' [--limit 10] [--sources all] [--json]
  ghost_unified_recall.py capture 'content' [--context 'optional context']
  ghost_unified_recall.py user-model [--update type 'data'] [--show]
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

from ghost_core_contracts import (
    RecallEvidence,
    RecallReport,
    SOURCE_LABELS,
    build_citation,
    confidence_from_score,
)
from ghost_core.contracts import CaptureRequest, RecallQuery, UserModelSignal
from ghost_core.defaults import build_default_runtime
from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace

USER_MODEL_PATH = _paths.user_model_path

STRUCTURED_FILES = {
    "decision": WORKSPACE / "memory" / "decisions.md",
    "idea": WORKSPACE / "memory" / "ideas.md",
    "commitment": WORKSPACE / "memory" / "commitments.md",
    "follow-up": WORKSPACE / "memory" / "follow-ups.md",
    "person": WORKSPACE / "memory" / "people.md",
}

DAILY_NOTE_DIR = _paths.memory_dir
LEARNINGS_DIR = _paths.learnings_dir


def _runtime():
    return build_default_runtime(str(WORKSPACE))

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
        from ghost_memory_db import GhostMemory
        _ghost_memory_cls = GhostMemory
        return GhostMemory
    except (ImportError, Exception):
        _ghost_memory_cls = False
        return False


def _get_scanner():
    try:
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

    query_terms = _normalize_query_terms(query)
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
                    key = _candidate_key(item)
                    existing = results_by_key.get(key)
                    if existing is None:
                        results_by_key[key] = item
                    else:
                        results_by_key[key] = _merge_result(existing, item)
            except Exception:
                pass

    results = list(results_by_key.values())
    results = _filter_by_source(results, allowed)
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return [_finalize_result(query, item, query_terms) for item in results[:limit]]


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


def _normalize_query_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[\w-]+", query.lower()) if term]


def _normalize_snippet(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())[:160]


def _candidate_key(item: dict) -> str:
    item_id = item.get("id")
    if item_id:
        return f"id:{item_id}"
    return f"{item.get('file', '')}:{_normalize_snippet(item.get('snippet') or item.get('title', ''))}"


def _merge_result(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    merged["score"] = max(existing.get("score", 0), incoming.get("score", 0))
    merged["source_labels"] = sorted(set(existing.get("source_labels", []) + incoming.get("source_labels", [])))
    merged["evidence"] = existing.get("evidence", []) + incoming.get("evidence", [])
    if len(merged["source_labels"]) > len(existing.get("source_labels", [])):
        merged["score"] = min(1.0, merged["score"] + 0.05)
    if not merged.get("snippet") and incoming.get("snippet"):
        merged["snippet"] = incoming["snippet"]
    if not merged.get("line") and incoming.get("line"):
        merged["line"] = incoming["line"]
    return merged


def _finalize_result(query: str, item: dict, query_terms: list[str]) -> dict:
    enriched = _enrich_result(query, item)
    matched_terms = sorted({
        term for evidence in enriched.get("evidence", [])
        for term in evidence.get("matched_terms", [])
    })
    if not matched_terms:
        snippet_text = _normalize_snippet(enriched.get("snippet", ""))
        matched_terms = [term for term in query_terms if term in snippet_text]
    if len(enriched.get("source_labels", [])) > 1:
        enriched["explanation"] = (
            f"Corroborated by {', '.join(enriched['source_labels'])}; matched terms: {', '.join(matched_terms[:4]) or 'n/a'}."
        )
    else:
        enriched["explanation"] = (
            f"Best signal from {enriched['source_label']}; matched terms: {', '.join(matched_terms[:4]) or 'n/a'}."
        )
    return enriched


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
        query_terms = _normalize_query_terms(query)
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
                "id": r.get("id"),
                "title": r.get("title", ""),
                "status": r.get("status", ""),
                "match": match_type,
                "distance": r.get("distance"),
                "file": r.get("source", ""),
                "line": 0,
                "snippet": r.get("snippet", r.get("title", "")),
                "score": score,
                "item_type": r.get("type", "unknown"),
                "date": r.get("date", ""),
                "source_labels": ["Structured Memory"],
                "evidence": [{
                    "kind": "db",
                    "label": f"DB {match_type} match",
                    "matched_terms": [term for term in query_terms if term in _normalize_snippet(r.get("snippet", r.get("title", "")))],
                    "file": r.get("source", ""),
                    "line": 0,
                }],
            })
        return out
    except Exception:
        return []


def _search_grep(query: str, limit: int) -> list[dict]:
    out = []
    search_terms = _normalize_query_terms(query)
    if not search_terms:
        return out

    scan_paths = []
    for md in DAILY_NOTE_DIR.glob("*.md"):
        scan_paths.append(md)
    for structured in STRUCTURED_FILES.values():
        if structured.exists():
            scan_paths.append(structured)
    if LEARNINGS_DIR.exists():
        scan_paths.extend(sorted(LEARNINGS_DIR.rglob("*.md")))

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
                "source_labels": [SOURCE_LABELS.get(_classify_source(rel), _classify_source(rel).title())],
                "evidence": [{
                    "kind": "grep",
                    "label": "File text match",
                    "matched_terms": [t for t in search_terms if t in lower_line],
                    "file": rel,
                    "line": i,
                }],
            })

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


def _enrich_result(query: str, item: dict) -> dict:
    """Normalize recall results into a stable evidence contract."""
    file_path = item.get("file", "")
    line = int(item.get("line", 0) or 0)
    source_bucket = _classify_source(file_path)
    source_label = SOURCE_LABELS.get(source_bucket, source_bucket.title())
    score = float(item.get("score", 0) or 0)

    evidence = RecallEvidence(
        query=query,
        item_type=item.get("item_type", "unknown"),
        source_bucket=source_bucket,
        source_label=source_label,
        source_detail=item.get("source", ""),
        file=file_path,
        line=line,
        citation=build_citation(file_path, line if line > 0 else None),
        score=score,
        confidence=confidence_from_score(score),
        snippet=item.get("snippet", ""),
        date=item.get("date", ""),
        id=str(item.get("id", "") or ""),
        title=item.get("title", ""),
        status=item.get("status", ""),
        match=item.get("match", ""),
        distance=item.get("distance"),
    )
    payload = evidence.to_dict()
    payload["source_labels"] = item.get("source_labels", [source_label])
    payload["evidence"] = item.get("evidence", [])
    return payload


def build_recall_report(
    query: str, limit: int = 10, sources: Optional[list] = None,
) -> dict:
    """Return a structured, evidence-first recall report."""
    raw_results = unified_recall(query, limit=limit, sources=sources)
    results = [
        item if "source_bucket" in item and "confidence" in item and "citation" in item
        else _enrich_result(query, item)
        for item in raw_results
    ]
    grouped_counts = {key: 0 for key in SOURCE_LABELS}
    for item in results:
        grouped_counts[item["source_bucket"]] = grouped_counts.get(item["source_bucket"], 0) + 1

    strongest_signal = results[0]["source_label"] if results else "none"
    recommendations = _build_recall_recommendations(results)

    report = RecallReport(
        query=query,
        generated_at=datetime.now().isoformat(),
        total_results=len(results),
        grouped_counts=grouped_counts,
        strongest_signal=strongest_signal,
        recommendations=recommendations,
        results=results,
    )
    return report.to_dict()


def _build_recall_recommendations(results: list[dict]) -> list[str]:
    if not results:
        return [
            "Broaden the query or try a project/person name.",
            "Escalate to Ghost Memory DB graph or temporal queries if you need cross-file recall.",
        ]

    recs = []
    top = results[0]
    if top["source_bucket"] == "daily":
        recs.append("Top evidence is still in daily notes, promote durable facts into structured memory if this will matter again.")
    if all(r["confidence"] == "low" for r in results[:3]):
        recs.append("Evidence is weak, refine the query with a specific project, person, or date.")
    if any(r["source_bucket"] == "learnings" for r in results):
        recs.append("A prior learning matches this topic, reuse the proven workflow before improvising.")
    if not recs:
        recs.append("Use the top cited evidence first, it already points to the most relevant durable context.")
    return recs


def build_related_recall(query: str, limit: int = 10, sources: Optional[list] = None, per_group: int = 2) -> dict:
    report = build_recall_report(query, limit=limit, sources=sources)
    results = report.get("results", [])
    top_hits = results[: min(3, len(results))]
    grouped: dict[str, list[dict]] = {}
    for item in results:
        item_type = item.get("item_type", "note")
        grouped.setdefault(item_type, [])
        if len(grouped[item_type]) < per_group:
            grouped[item_type].append(item)

    ordered_types = ["decision", "commitment", "follow-up", "person", "idea", "learning", "daily_note", "note"]
    related = [
        {"item_type": item_type, "count": len(grouped[item_type]), "items": grouped[item_type]}
        for item_type in ordered_types if grouped.get(item_type)
    ]
    seen_types = set(ordered_types)
    related.extend(
        {"item_type": item_type, "count": len(items), "items": items}
        for item_type, items in grouped.items() if item_type not in seen_types
    )

    report["mode"] = "related"
    report["top_hits"] = top_hits
    report["related"] = related
    report["cross_file_signals"] = len({item.get("item_type", "note") for item in results})
    if report["cross_file_signals"] > 1:
        report.setdefault("recommendations", []).append("Cross-file signals found, use the linked decision/follow-up/person entries together instead of only the top hit.")
    return report


# ---------------------------------------------------------------------------
# 1b. recall_summary
# ---------------------------------------------------------------------------

def related_recall_summary(query: str, limit: int = 8) -> str:
    report = build_related_recall(query, limit=limit)
    if not report.get("results"):
        return f"No related memory found for: **{query}**"

    parts = [
        f"## Related Recall: {query}\n",
        f"Top signal: **{report.get('strongest_signal', 'none')}** across **{report.get('cross_file_signals', 0)}** memory type(s).\n",
    ]

    if report.get("top_hits"):
        parts.append("### Top hits")
        for item in report["top_hits"][:3]:
            parts.append(f"- {item.get('snippet', '').strip()}  \n  _Source: `{item.get('citation', item.get('file', '?'))}` · {item.get('item_type', 'note')}_")
        parts.append("")

    for group in report.get("related", []):
        label = group.get("item_type", "note").replace("_", " ").title()
        parts.append(f"### Related {label} ({group.get('count', 0)})")
        for item in group.get("items", [])[:2]:
            parts.append(f"- {item.get('snippet', '').strip()}  \n  _Source: `{item.get('citation', item.get('file', '?'))}`_")
        parts.append("")

    return "\n".join(parts)


def recall_summary(
    query: str, limit: int = 5, *, show_confidence: bool = True, show_evidence: bool = False,
) -> str:
    """Format unified_recall results as a clean markdown summary."""
    report = build_recall_report(query, limit=limit)
    results = report["results"]
    if not results:
        return f"No results found for: **{query}**"

    grouped: dict[str, list[dict]] = {}
    for r in results:
        src = r.get("source_bucket", _classify_source(r.get("file", "")))
        grouped.setdefault(src, []).append(r)

    parts = [
        f"## Recall: {query}\n",
        f"Found **{report['total_results']}** result(s). Strongest signal: **{report['strongest_signal']}**.\n",
    ]
    for src_key in ("memory", "daily", "learnings"):
        items = grouped.get(src_key, [])
        if not items:
            continue
        parts.append(f"### {SOURCE_LABELS.get(src_key, src_key)} ({len(items)})")
        for item in items:
            file_ref = item.get("citation", item.get("file", "?"))
            snippet = item.get("snippet", "").strip()
            date = item.get("date", "")
            date_str = f" ({date})" if date else ""
            confidence = item.get("confidence", "low")
            prefix = f"[{confidence}] " if show_confidence else ""
            parts.append(f"- {prefix}{snippet}{date_str}  \n  _Source: `{file_ref}` · {item.get('item_type', 'note')}_")
            if show_evidence:
                for ev in item.get("evidence", [])[:2]:
                    parts.append(f"  - evidence: {ev.get('label', 'match')} @ {ev.get('file', '?')}:{ev.get('line', 0)}")
        parts.append("")

    if report["recommendations"]:
        parts.append("### Next")
        for rec in report["recommendations"][:2]:
            parts.append(f"- {rec}")

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
        return {
            "type": "error",
            "file": "",
            "path": "",
            "entry_text": "",
            "duplicate_warning": "Empty content",
            "added": False,
            "duplicate": False,
            "message": "Empty content",
            "tags": [],
        }

    detected_type = _detect_content_type(content)
    target_file = _resolve_target_file(detected_type)
    tags = _extract_tags(content, context=context)
    entry_text = _format_entry(detected_type, content, context, tags=tags)

    scan_content_fn, check_dup_fn, check_size_fn = _get_scanner()

    if scan_content_fn:
        scan_result = scan_content_fn(entry_text)
        if not scan_result.safe:
            warning = f"BLOCKED: {scan_result.reason}"
            return {
                "type": detected_type,
                "file": target_file,
                "path": target_file,
                "entry_text": entry_text,
                "duplicate_warning": warning,
                "added": False,
                "duplicate": False,
                "message": warning,
                "tags": tags,
            }

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
        "path": target_file,
        "entry_text": entry_text,
        "duplicate_warning": duplicate_warning,
        "added": not bool(duplicate_warning),
        "duplicate": bool(duplicate_warning),
        "message": duplicate_warning or "captured",
        "tags": tags,
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


_TAG_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have", "will", "would", "should", "could",
    "waiting", "check", "review", "follow", "decided", "decision", "build", "use", "using", "keep",
    "had", "normal", "note", "notes", "context", "meeting", "brainstorm", "perf", "next", "first",
}


def _extract_tags(content: str, context: str = "", max_tags: int = 5) -> list[str]:
    combined = f"{content} {context}".strip()
    tags: list[str] = []

    def add(tag: str) -> None:
        cleaned = tag.strip(" ,.;:()[]{}")
        if not cleaned:
            return
        lowered = cleaned.lower()
        if lowered in _TAG_STOPWORDS:
            return
        if cleaned not in tags:
            tags.append(cleaned)

    for tag in re.findall(r"คุณ[\wก-๙-]+", combined):
        add(tag)
    for tag in re.findall(r"\b[A-Z][A-Z0-9-]{2,}\b", combined):
        add(tag)
    for tag in re.findall(r"\b[A-Z][a-zA-Z0-9-]{2,}\b", combined):
        add(tag)
    for tag in re.findall(r"\b[A-Za-z][A-Za-z0-9-]*[A-Z][A-Za-z0-9-]*\b", combined):
        add(tag)
    for tag in re.findall(r"\b[a-z]+(?:-[a-z0-9]+)+\b", combined):
        add(tag)

    return tags[:max_tags]


def _format_entry(content_type: str, content: str, context: str, tags: list[str] | None = None) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    ctx = f" — {context}" if context else ""
    tag_line = f"Tags: [{', '.join(tags or [])}]\n" if tags else ""
    if content_type == "daily-log":
        if tag_line:
            return f"\n- {content}{ctx}\n  {tag_line}"
        return f"\n- {content}{ctx}\n"
    return f"\n## [{today}] {content}{ctx}\n{tag_line}"


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
    return f"""# User Model — User

## Communication Preferences
- Concise, accurate, direct
- Wants advanced frameworks, not basic advice
- Thai + English mix in conversation
- Prefers actionable output over explanations

## Technical Preferences
- Databases, automation tools, and knowledge systems
- Prisma v6 (avoid v7)
- Python for scripts, Node.js for apps
- WSL2 development environment

## Work Patterns
- Technical lead, operator, or founder
- Multiple concurrent projects
- Prefers reactive support over proactive micromanagement on stable projects
- Values critique-by-default

## Recurring Topics
- Workflow automation
- Client project delivery
- Ghost Brain system improvement
- Campaign or operations automation

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
    p_recall.add_argument("--json", action="store_true", help="Return structured JSON")

    p_summary = sub.add_parser("summary", help="Formatted recall summary")
    p_summary.add_argument("query", help="Search query")
    p_summary.add_argument("--limit", type=int, default=5)

    p_report = sub.add_parser("report", help="Structured recall report")
    p_report.add_argument("query", help="Search query")
    p_report.add_argument("--limit", type=int, default=10)
    p_report.add_argument("--sources", default="all")
    p_report.add_argument("--json", action="store_true", help="Return JSON report")

    p_related = sub.add_parser("related", help="Show linked memory around a query")
    p_related.add_argument("query", help="Search query")
    p_related.add_argument("--limit", type=int, default=8)
    p_related.add_argument("--sources", default="all")
    p_related.add_argument("--json", action="store_true", help="Return JSON report")

    p_capture = sub.add_parser("capture", help="Smart capture content")
    p_capture.add_argument("content", help="Content to capture")
    p_capture.add_argument("--context", default="")
    p_capture.add_argument("--json", action="store_true", help="Return JSON result")

    p_um = sub.add_parser("user-model", help="View or update user model")
    p_um.add_argument("--show", action="store_true", help="Show parsed model")
    p_um.add_argument("--json", action="store_true", help="Return parsed JSON")
    p_um.add_argument("--update", nargs=2, metavar=("TYPE", "DATA"),
                       help="Update model: --update correction 'data'")

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    runtime = _runtime()

    if args.command == "recall":
        src_list = [s.strip() for s in args.sources.split(",")]
        if args.json:
            report = runtime.recall.recall(RecallQuery(query=args.query, limit=args.limit, sources=src_list))
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return

        results = unified_recall(args.query, limit=args.limit, sources=src_list)
        if not results:
            print("No results found.")
            return
        for r in results:
            score = r.get("score", 0)
            print(
                f"[{score:.2f} | {r.get('confidence', 'low'):6s}] "
                f"{r.get('item_type', '?'):12s} {r.get('citation', r.get('file', '?')):50s} "
                f"{r.get('snippet', '')[:80]}"
            )

    elif args.command == "summary":
        print(recall_summary(args.query, limit=args.limit))

    elif args.command == "report":
        src_list = [s.strip() for s in args.sources.split(",")]
        report = runtime.recall.recall(RecallQuery(query=args.query, limit=args.limit, sources=src_list)).to_dict()
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(recall_summary(args.query, limit=args.limit))

    elif args.command == "related":
        src_list = [s.strip() for s in args.sources.split(",")]
        report = build_related_recall(args.query, limit=args.limit, sources=src_list)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(related_recall_summary(args.query, limit=args.limit))

    elif args.command == "capture":
        capture = runtime.recall.capture(CaptureRequest(content=args.content, context=args.context))
        result = capture.to_dict()
        result["file"] = result["path"]
        result["duplicate_warning"] = result["message"] if result["duplicate"] or not result["added"] else ""
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return
        print(f"Type:    {result['type']}")
        print(f"File:    {result['file']}")
        if result.get("tags"):
            print(f"Tags:    {', '.join(result['tags'])}")
        if result.get("duplicate_warning"):
            print(f"Warning: {result['duplicate_warning']}")
        else:
            print("Status:  captured")

    elif args.command == "user-model":
        if args.update:
            signal_type, signal_data = args.update
            runtime.recall.update_user_model(UserModelSignal(signal_type=signal_type, data=signal_data))
            print(f"Updated user model ({signal_type}): {signal_data}")
        else:
            model = runtime.recall.get_user_model()
            if args.json or args.show:
                print(json.dumps(model, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(model, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
