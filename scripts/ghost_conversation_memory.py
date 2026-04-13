#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ghost_core.contracts import SCHEMA_CONVERSATION, SOURCE_LABELS, build_citation, confidence_from_score

QUERY_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "what", "when", "where", "were", "have",
    "has", "had", "did", "say", "said", "you", "your", "our", "we", "i", "about", "into", "just", "then", "than", "them", "they",
    "last", "week", "time", "earlier", "previously", "mentioned", "discussed", "chat", "conversation", "session",
    "เรา", "คือ", "และ", "ของ", "ได้", "ไม่", "ให้", "กับ", "แล้ว", "ครับ", "ค่ะ",
}
TOPIC_STOPWORDS = QUERY_STOPWORDS | {
    "ghost", "brain", "assistant", "tool", "tools", "message", "messages", "session", "sessions",
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat().replace("+00:00", "Z")


def _session_root(session_root: str | Path | None = None) -> Path:
    configured = session_root or os.environ.get("OPENCLAW_SESSIONS_ROOT") or os.environ.get("GHOST_SESSION_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".openclaw" / "agents"


def _normalize_query_terms(query: str) -> list[str]:
    return [
        term for term in re.findall(r"[\w-]+", (query or "").lower())
        if len(term) > 1 and term not in QUERY_STOPWORDS
    ]


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def _display_path(path: Path) -> str:
    rel = _relative_path(path)
    if rel == str(path):
        return rel
    return f"~/{rel}"


def _parse_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 1_000_000_000_000 else value
        try:
            return datetime.fromtimestamp(timestamp, timezone.utc)
        except (OSError, ValueError):
            return None
    cleaned = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _extract_text_parts(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if isinstance(content, dict):
        text = content.get("text") or content.get("input") or content.get("output")
        return [str(text)] if text else []
    parts: list[str] = []
    if not isinstance(content, list):
        return parts
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in {"text", "input_text", "output_text"}:
            text = item.get("text") or item.get("input") or item.get("output")
            if text:
                parts.append(str(text))
    return parts


def _strip_envelope_noise(text: str) -> str:
    cleaned = text or ""
    block_patterns = [
        r"Conversation info \(untrusted metadata\):\s*```json.*?```",
        r"Sender \(untrusted metadata\):\s*```json.*?```",
        r"Replied message \(untrusted.*?\):\s*```json.*?```",
        r"<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>.*?<<<END_OPENCLAW_INTERNAL_CONTEXT>>>",
        r"<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>.*?<<<END_UNTRUSTED_CHILD_RESULT>>>",
    ]
    for pattern in block_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE | re.DOTALL)

    line_patterns = [
        r"^System \(untrusted\):.*$",
        r"^Sender \(untrusted metadata\):.*$",
        r"^Conversation info \(untrusted metadata\):.*$",
    ]
    for pattern in line_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    cleaned = re.sub(r"\[\[\s*reply_to[^\]]*\]\]", " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def _message_text(record: dict[str, Any]) -> str:
    message = record.get("message") or {}
    content = message.get("content")
    text = " ".join(_extract_text_parts(content)).strip()
    return _strip_envelope_noise(text)


def _message_timestamp(record: dict[str, Any]) -> datetime | None:
    message = record.get("message") or {}
    return _parse_timestamp(message.get("timestamp") or record.get("timestamp"))


def _message_role(record: dict[str, Any]) -> str:
    message = record.get("message") or {}
    return str(message.get("role") or "")


def _is_automated_prompt(text: str) -> bool:
    lowered = (text or "").lower()
    return (
        lowered.startswith("[cron:")
        or "read and follow the prompt at:" in lowered
        or lowered.startswith("a new session was started via /new or /reset")
        or "[subagent context]" in lowered
    )


def _iter_session_files(
    session_root: str | Path | None = None,
    *,
    agent: str | None = None,
    days: int = 30,
    max_sessions: int = 40,
) -> list[Path]:
    root = _session_root(session_root)
    if not root.exists():
        return []
    cutoff = _now_utc() - timedelta(days=max(days, 1))
    patterns = [f"{agent}/sessions/*.jsonl"] if agent else ["*/sessions/*.jsonl"]
    files: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if ".checkpoint." in path.name:
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            except OSError:
                continue
            if mtime < cutoff:
                continue
            files.append(path)
    files.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    return files[:max_sessions]


def _topic_keywords(texts: list[str], limit: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        for token in re.findall(r"[\w-]+", text.lower()):
            if len(token) < 3 or token in TOPIC_STOPWORDS:
                continue
            counter[token] += 1
    return [token for token, _ in counter.most_common(limit)]


def _normalized_match_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())[:220]


def _phrase_bonus(text: str, query_terms: list[str]) -> float:
    if len(query_terms) < 2:
        return 0.0
    lowered = (text or "").lower()
    bigrams = [f"{query_terms[i]} {query_terms[i + 1]}" for i in range(len(query_terms) - 1)]
    return 0.05 if any(phrase in lowered for phrase in bigrams) else 0.0


def _postprocess_hits(hits: list[dict[str, Any]], *, limit: int, per_session_limit: int = 2) -> list[dict[str, Any]]:
    hits.sort(
        key=lambda item: (
            item.get("score", 0),
            item.get("timestamp", ""),
            item.get("line", 0),
        ),
        reverse=True,
    )

    filtered: list[dict[str, Any]] = []
    seen_snippets: set[str] = set()
    session_counts: Counter[str] = Counter()
    for item in hits:
        snippet_key = _normalized_match_text(item.get("snippet", ""))
        if snippet_key and snippet_key in seen_snippets:
            continue
        session_id = str(item.get("session_id") or "")
        if session_id and session_counts[session_id] >= per_session_limit:
            continue
        if snippet_key:
            seen_snippets.add(snippet_key)
        if session_id:
            session_counts[session_id] += 1
        filtered.append(item)
        if len(filtered) >= limit:
            break
    return filtered


def collect_session_summaries(
    *,
    days: int = 30,
    max_sessions: int = 40,
    session_root: str | Path | None = None,
    agent: str | None = None,
    include_automated: bool = False,
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in _iter_session_files(session_root, agent=agent, days=days, max_sessions=max_sessions):
        session_id = path.stem
        agent_name = path.parent.parent.name if path.parent.parent else "unknown"
        started_at: datetime | None = None
        last_message_at: datetime | None = None
        previews: list[str] = []
        topic_texts: list[str] = []
        user_messages = 0
        assistant_messages = 0
        automated = False
        message_count = 0

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for raw in lines:
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            record_type = record.get("type")
            if record_type == "session" and not started_at:
                started_at = _parse_timestamp(record.get("timestamp"))
                continue
            if record_type != "message":
                continue
            role = _message_role(record)
            if role not in {"user", "assistant"}:
                continue
            text = _message_text(record)
            if not text:
                continue
            if _is_automated_prompt(text):
                automated = True
                continue
            timestamp = _message_timestamp(record)
            last_message_at = timestamp or last_message_at
            message_count += 1
            if role == "user":
                user_messages += 1
            if role == "assistant":
                assistant_messages += 1
            if len(previews) < 3:
                previews.append(text[:140])
            topic_texts.append(text)

        if automated and not include_automated and message_count == 0:
            continue
        if automated and not include_automated and message_count <= 1 and not topic_texts:
            continue
        if not started_at:
            try:
                started_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            except OSError:
                started_at = None
        if not last_message_at:
            last_message_at = started_at

        summaries.append(
            {
                "session_id": session_id,
                "agent": agent_name,
                "file": _display_path(path),
                "citation": _display_path(path),
                "started_at": started_at.isoformat().replace("+00:00", "Z") if started_at else "",
                "last_message_at": last_message_at.isoformat().replace("+00:00", "Z") if last_message_at else "",
                "message_count": message_count,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "preview": " | ".join(previews)[:280],
                "keywords": _topic_keywords(topic_texts),
                "automated": automated,
            }
        )

    summaries.sort(key=lambda item: item.get("last_message_at", ""), reverse=True)
    return summaries


def search_conversation_hits(
    query: str,
    *,
    limit: int = 10,
    days: int = 30,
    max_sessions: int = 40,
    session_root: str | Path | None = None,
    agent: str | None = None,
    roles: set[str] | None = None,
    per_session_limit: int = 2,
) -> list[dict[str, Any]]:
    query_terms = _normalize_query_terms(query)
    if not query_terms:
        return []
    min_matches = 2 if len(query_terms) >= 3 else 1
    allowed_roles = roles or {"user", "assistant"}
    hits: list[dict[str, Any]] = []
    for path in _iter_session_files(session_root, agent=agent, days=days, max_sessions=max_sessions):
        session_id = path.stem
        agent_name = path.parent.parent.name if path.parent.parent else "unknown"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for line_no, raw in enumerate(lines, 1):
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "message":
                continue
            role = _message_role(record)
            if role not in allowed_roles:
                continue
            text = _message_text(record)
            if not text or _is_automated_prompt(text):
                continue
            lowered = text.lower()
            matched_terms = [term for term in query_terms if term in lowered]
            if len(matched_terms) < min_matches:
                continue
            timestamp = _message_timestamp(record)
            coverage = len(matched_terms) / max(len(query_terms), 1)
            recency_bonus = 0.0
            if timestamp:
                age_days = (_now_utc() - timestamp.astimezone(timezone.utc)).days
                if age_days <= 3:
                    recency_bonus = 0.12
                elif age_days <= 14:
                    recency_bonus = 0.06
            specificity_bonus = min(0.1, max(0, len(set(matched_terms)) - 1) * 0.03)
            score = min(
                0.98,
                0.35
                + (coverage * 0.45)
                + recency_bonus
                + (0.04 if role == "user" else 0.0)
                + specificity_bonus
                + _phrase_bonus(text, query_terms),
            )
            file_ref = _display_path(path)
            hits.append(
                {
                    "query": query,
                    "source": "conversation",
                    "source_bucket": "conversation",
                    "source_label": SOURCE_LABELS["conversation"],
                    "file": file_ref,
                    "line": line_no,
                    "citation": build_citation(file_ref, line_no),
                    "snippet": text[:280],
                    "score": round(score, 3),
                    "confidence": confidence_from_score(score),
                    "item_type": "conversation",
                    "date": timestamp.date().isoformat() if timestamp else "",
                    "timestamp": timestamp.isoformat().replace("+00:00", "Z") if timestamp else "",
                    "role": role,
                    "session_id": session_id,
                    "agent": agent_name,
                    "matched_terms": matched_terms,
                    "source_labels": [SOURCE_LABELS["conversation"]],
                    "evidence": [
                        {
                            "kind": "conversation",
                            "label": f"{role} message match",
                            "matched_terms": matched_terms,
                            "file": file_ref,
                            "line": line_no,
                        }
                    ],
                }
            )

    return _postprocess_hits(hits, limit=limit, per_session_limit=per_session_limit)


def search_conversations(
    query: str,
    *,
    limit: int = 10,
    days: int = 30,
    max_sessions: int = 40,
    session_root: str | Path | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    results = search_conversation_hits(
        query,
        limit=limit,
        days=days,
        max_sessions=max_sessions,
        session_root=session_root,
        agent=agent,
    )
    scanned = len(_iter_session_files(session_root, agent=agent, days=days, max_sessions=max_sessions))
    recommendations: list[str] = []
    if results:
        recommendations.append("Raw conversation hits found, promote any durable decision or follow-up into structured memory if it will matter again.")
        if any(item.get("role") == "user" for item in results[:3]):
            recommendations.append("Top hits include user phrasing, reuse the original language when reconstructing intent.")
    else:
        recommendations.append("No raw conversation hits found, broaden the query or try a project/person name.")

    return {
        "schema_version": SCHEMA_CONVERSATION,
        "mode": "search",
        "generated_at": _now_iso(),
        "query": query,
        "days": days,
        "sessions_scanned": scanned,
        "total_results": len(results),
        "unique_sessions": len({item.get("session_id") for item in results if item.get("session_id")}),
        "results": results,
        "recommendations": recommendations,
    }


def recent_conversations(
    *,
    days: int = 7,
    limit: int = 8,
    max_sessions: int = 20,
    session_root: str | Path | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    sessions = collect_session_summaries(
        days=days,
        max_sessions=max_sessions,
        session_root=session_root,
        agent=agent,
        include_automated=False,
    )
    sessions = [session for session in sessions if session.get("message_count", 0) > 0][:limit]
    return {
        "schema_version": SCHEMA_CONVERSATION,
        "mode": "recent",
        "generated_at": _now_iso(),
        "days": days,
        "session_count": len(sessions),
        "sessions": sessions,
        "recommendations": [
            "Use recent sessions to recover working context quickly before asking the user to restate anything.",
        ] if sessions else ["No recent non-automated sessions found in the selected window."],
    }


def print_search_report(payload: dict[str, Any]) -> None:
    print("💬 Ghost Conversation Recall")
    print(f"   Query: {payload.get('query')}")
    print(f"   Sessions scanned: {payload.get('sessions_scanned', 0)}")
    results = payload.get("results", [])
    if not results:
        print("   No matching conversation snippets.")
        return
    for item in results[:10]:
        print(f"   - [{item.get('score', 0):.2f}] {item.get('snippet', '')}")
        print(f"     {item.get('agent', 'unknown')} · {item.get('role', 'message')} · {item.get('citation', item.get('file', '-'))}")


def print_recent_report(payload: dict[str, Any]) -> None:
    print("🧵 Recent Ghost Conversations")
    sessions = payload.get("sessions", [])
    if not sessions:
        print("   No recent sessions found.")
        return
    for item in sessions[:10]:
        print(f"   - {item.get('agent', 'unknown')} · {item.get('last_message_at', '-')}")
        print(f"     msgs={item.get('message_count', 0)} user={item.get('user_messages', 0)} assistant={item.get('assistant_messages', 0)}")
        if item.get("keywords"):
            print(f"     topics={', '.join(item['keywords'])}")
        if item.get("preview"):
            print(f"     {item['preview']}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost_conversation_memory", description="Ghost conversation-memory surfaces")
    sub = parser.add_subparsers(dest="command")

    search_p = sub.add_parser("search", help="Search raw session transcripts")
    search_p.add_argument("query")
    search_p.add_argument("--limit", type=int, default=10)
    search_p.add_argument("--days", type=int, default=30)
    search_p.add_argument("--json", action="store_true")

    recent_p = sub.add_parser("recent", help="Summarize recent non-automated sessions")
    recent_p.add_argument("--days", type=int, default=7)
    recent_p.add_argument("--limit", type=int, default=8)
    recent_p.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == "search":
        payload = search_conversations(args.query, limit=args.limit, days=args.days)
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_search_report(payload)
        return
    if args.command == "recent":
        payload = recent_conversations(days=args.days, limit=args.limit)
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_recent_report(payload)


if __name__ == "__main__":
    main()
