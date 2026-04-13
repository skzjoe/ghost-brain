#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ghost_conversation_memory import collect_session_summaries
from ghost_core.contracts import SCHEMA_GUARDRAILS
from ghost_core.workspace import get_workspace_paths

BANGKOK = ZoneInfo("Asia/Bangkok")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _daily_note_path(workspace: Path, timestamp: datetime) -> Path:
    day = timestamp.astimezone(BANGKOK).strftime("%Y-%m-%d")
    return workspace / "memory" / f"{day}.md"


def _note_status(note_path: Path) -> dict[str, Any]:
    if not note_path.exists():
        return {"exists": False, "updated_at": "", "updated_dt": None}
    updated_dt = datetime.fromtimestamp(note_path.stat().st_mtime, timezone.utc)
    return {
        "exists": True,
        "updated_at": updated_dt.isoformat().replace("+00:00", "Z"),
        "updated_dt": updated_dt,
    }


def _session_is_significant(summary: dict[str, Any], min_messages: int, min_user_messages: int) -> bool:
    return (
        summary.get("message_count", 0) >= min_messages
        or summary.get("user_messages", 0) >= min_user_messages
    )


def _capture_risk(uncaptured: list[dict[str, Any]]) -> tuple[str, str]:
    if not uncaptured:
        return "clear", "low"
    if len(uncaptured) >= 2:
        return "block", "high"
    session = uncaptured[0]
    if session.get("message_count", 0) >= 8 or session.get("user_messages", 0) >= 3:
        return "block", "high"
    return "nudge", "medium"


def build_guardrail_report(
    workspace: str | Path | None = None,
    *,
    session_root: str | Path | None = None,
    days: int = 3,
    max_sessions: int = 12,
    grace_minutes: int = 20,
    min_messages: int = 6,
    min_user_messages: int = 2,
) -> dict[str, Any]:
    paths = get_workspace_paths(workspace or os.environ.get("OPENCLAW_WORKSPACE"))
    uncaptured: list[dict[str, Any]] = []
    warnings: list[str] = []
    summaries = collect_session_summaries(
        days=days,
        max_sessions=max_sessions,
        session_root=session_root,
        include_automated=False,
    )
    grace_delta = timedelta(minutes=max(grace_minutes, 0))

    for summary in summaries:
        if not _session_is_significant(summary, min_messages=min_messages, min_user_messages=min_user_messages):
            continue
        last_message_dt = _parse_timestamp(summary.get("last_message_at"))
        if not last_message_dt:
            continue
        if _now_utc() - last_message_dt < grace_delta:
            continue
        note_path = _daily_note_path(paths.workspace, last_message_dt)
        note_status = _note_status(note_path)
        updated_dt = note_status.get("updated_dt")
        if updated_dt and updated_dt >= last_message_dt:
            continue
        uncaptured.append(
            {
                **summary,
                "note_path": str(note_path.relative_to(paths.workspace)),
                "note_exists": note_status["exists"],
                "note_updated_at": note_status["updated_at"],
                "minutes_since_activity": int((_now_utc() - last_message_dt).total_seconds() // 60),
            }
        )

    status, capture_risk = _capture_risk(uncaptured)
    if uncaptured and any(not item.get("note_exists") for item in uncaptured):
        warnings.append("A session appears uncaptured and its matching daily note is missing.")
    if status == "block":
        next_action = "Run /logs or update the relevant daily note before /new."
    elif status == "nudge":
        next_action = "Capture the latest session before resetting so context is not lost."
    else:
        next_action = "No uncaptured-session risk detected."

    return {
        "schema_version": SCHEMA_GUARDRAILS,
        "generated_at": _now_iso(),
        "status": status,
        "capture_risk": capture_risk,
        "sessions_considered": len(summaries),
        "uncaptured_count": len(uncaptured),
        "uncaptured_sessions": uncaptured,
        "next_action": next_action,
        "warnings": warnings,
    }


def print_guardrail_report(payload: dict[str, Any]) -> None:
    print("🛡️ Ghost Guardrails")
    print(f"   Status: {payload.get('status', 'unknown')} ({payload.get('capture_risk', 'unknown')})")
    print(f"   Sessions considered: {payload.get('sessions_considered', 0)}")
    if payload.get("warnings"):
        for warning in payload["warnings"][:3]:
            print(f"   Warning: {warning}")
    uncaptured = payload.get("uncaptured_sessions", [])
    if not uncaptured:
        print("   No uncaptured-session risk detected.")
        return
    for item in uncaptured[:5]:
        print(f"   - {item.get('agent', 'unknown')} · {item.get('last_message_at', '-')}")
        print(f"     note={item.get('note_path', '-')} updated={item.get('note_updated_at', 'missing') or 'missing'} msgs={item.get('message_count', 0)}")
        if item.get("preview"):
            print(f"     {item['preview']}")
    print(f"   Next: {payload.get('next_action', '-')}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost_guardrails", description="Ghost uncaptured-work guardrails")
    sub = parser.add_subparsers(dest="command")

    check_p = sub.add_parser("check", help="Inspect uncaptured-session risk")
    check_p.add_argument("--days", type=int, default=3)
    check_p.add_argument("--json", action="store_true")

    pre_new_p = sub.add_parser("pre-new", help="Block /new when uncaptured work risk is present")
    pre_new_p.add_argument("--days", type=int, default=3)
    pre_new_p.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    payload = build_guardrail_report(days=args.days)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_guardrail_report(payload)

    if args.command == "pre-new" and payload.get("status") != "clear":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
