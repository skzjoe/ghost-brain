#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ghost_core.defaults import build_default_runtime
from ghost_core.workspace import get_workspace_paths
from ghost_guardrails import build_guardrail_report
from ghost_memory_sync import build_memory_sync_report

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace

BRIEF_SCHEMA = "ghost-brief/v1"
FOLLOWUPS_SCHEMA = "ghost-followups/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _runtime(workspace: str | Path | None = None):
    return build_default_runtime(str(workspace or WORKSPACE))


def _paths_for(workspace: str | Path | None = None):
    return get_workspace_paths(workspace or WORKSPACE)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _parse_iso_date(value: str) -> datetime | None:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"—", "-", "n/a", "N/A"}:
        return None
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        return None


def _extract_section_lines(text: str, section_title: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section and stripped != section_title:
                break
            in_section = stripped == section_title
            continue
        if in_section:
            collected.append(line)
    return collected


def _parse_markdown_table(lines: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None
    for raw in lines:
        stripped = raw.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if headers is None:
            headers = cells
            continue
        if all(cell.startswith("---") or cell == "" for cell in cells):
            continue
        if headers and len(cells) == len(headers):
            rows.append({headers[i].lower().replace(" ", "_"): cells[i] for i in range(len(headers))})
    return rows


def recent_decisions(workspace: str | Path | None = None, limit: int = 3) -> list[dict[str, Any]]:
    paths = _paths_for(workspace)
    text = _read_text(paths.memory_dir / "decisions.md")
    decisions: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("["):
            continue
        if "] **" not in stripped:
            continue
        date_part = stripped.split("]", 1)[0].lstrip("[")
        title_part = stripped.split("**", 2)
        title = title_part[1].strip() if len(title_part) > 2 else stripped
        rationale = stripped.split("—", 1)[1].strip() if "—" in stripped else ""
        decisions.append({"date": date_part, "title": title, "rationale": rationale, "raw": stripped})
    return decisions[:limit]


def followups_due(workspace: str | Path | None = None, limit: int = 10, stale_after_days: int = 7) -> dict[str, Any]:
    paths = _paths_for(workspace)
    text = _read_text(paths.memory_dir / "follow-ups.md")
    active_rows = _parse_markdown_table(_extract_section_lines(text, "## Active"))
    today = datetime.now()
    items: list[dict[str, Any]] = []

    for row in active_rows:
        since_date = _parse_iso_date(row.get("since", ""))
        deadline_date = _parse_iso_date(row.get("deadline", ""))
        age_days = (today - since_date).days if since_date else None
        days_to_deadline = (deadline_date - today).days if deadline_date else None
        state = (row.get("state", "") or "").strip().lower()
        bucket = "active"
        priority = 4
        if days_to_deadline is not None and days_to_deadline < 0:
            bucket = "overdue"
            priority = 0
        elif days_to_deadline is not None and days_to_deadline <= 7:
            bucket = "due_this_week"
            priority = 1
        elif age_days is not None and age_days >= stale_after_days:
            bucket = "stale"
            priority = 2
        elif state == "blocked":
            bucket = "blocked"
            priority = 3

        items.append(
            {
                "item": row.get("item", ""),
                "owner": row.get("owner", ""),
                "since": row.get("since", ""),
                "deadline": row.get("deadline", ""),
                "state": row.get("state", ""),
                "status": row.get("status", ""),
                "age_days": age_days,
                "days_to_deadline": days_to_deadline,
                "bucket": bucket,
                "priority": priority,
            }
        )

    items.sort(key=lambda item: (item["priority"], item["days_to_deadline"] if item["days_to_deadline"] is not None else 9999, -(item["age_days"] or 0)))
    counts: dict[str, int] = {}
    for item in items:
        counts[item["bucket"]] = counts.get(item["bucket"], 0) + 1
    return {
        "schema_version": FOLLOWUPS_SCHEMA,
        "generated_at": now_iso(),
        "stale_after_days": stale_after_days,
        "total_active": len(items),
        "counts": counts,
        "items": items[:limit],
    }


def build_brief(workspace: str | Path | None = None, decision_limit: int = 3, followup_limit: int = 5) -> dict[str, Any]:
    runtime = _runtime(workspace)
    snapshot = runtime.session_context.snapshot().to_dict()
    followups = followups_due(workspace=workspace, limit=followup_limit)
    decisions = recent_decisions(workspace=workspace, limit=decision_limit)
    second_brain = snapshot.get("second_brain_focus") or {}
    guardrails = snapshot.get("guardrails") or build_guardrail_report(workspace=workspace)
    memory_sync = snapshot.get("memory_sync") or build_memory_sync_report(workspace=workspace)
    return {
        "schema_version": BRIEF_SCHEMA,
        "generated_at": now_iso(),
        "focus": snapshot.get("focus", ""),
        "blockers": snapshot.get("blockers", [])[:5],
        "next_actions": snapshot.get("next_actions", [])[:5],
        "commitments_due": snapshot.get("commitments_due", [])[:5],
        "followups_due": followups,
        "recent_decisions": decisions,
        "second_brain_focus": second_brain,
        "guardrails": guardrails,
        "memory_sync": memory_sync,
        "summary": {
            "repetition_risk": second_brain.get("repetition_risk", "unknown"),
            "continuity_health": second_brain.get("continuity_health", "unknown"),
            "capture_risk": guardrails.get("capture_risk", "unknown"),
            "memory_sync_status": memory_sync.get("status", "unknown"),
            "due_followups": followups.get("counts", {}).get("overdue", 0) + followups.get("counts", {}).get("due_this_week", 0),
            "stale_followups": followups.get("counts", {}).get("stale", 0),
        },
    }


def print_followups(payload: dict[str, Any]) -> None:
    print("📌 Ghost Follow-ups Due")
    counts = payload.get("counts", {})
    if counts:
        print("   Counts: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    items = payload.get("items", [])
    if not items:
        print("   No active follow-ups.")
        return
    for item in items:
        age = f"{item['age_days']}d" if item.get("age_days") is not None else "-"
        deadline = item.get("deadline") or "-"
        print(f"   - [{item.get('bucket', 'active')}] {item['item']}")
        print(f"     owner={item.get('owner', '-')} deadline={deadline} age={age} state={item.get('state', '-')}")


def print_brief(payload: dict[str, Any]) -> None:
    print("👻 Ghost Brief")
    print(f"   Focus: {payload.get('focus') or '-'}")
    second_brain = payload.get("second_brain_focus") or {}
    if second_brain:
        print(f"   Repetition risk: {second_brain.get('repetition_risk', '-')}")
        if second_brain.get("next_best_action"):
            print(f"   Next best action: {second_brain['next_best_action']}")
    guardrails = payload.get("guardrails") or {}
    if guardrails:
        print(f"   Capture risk: {guardrails.get('capture_risk', '-')}")
    memory_sync = payload.get("memory_sync") or {}
    if memory_sync:
        print(f"   Memory sync: {memory_sync.get('status', '-')}")
    if payload.get("blockers"):
        print("   Blockers:")
        for item in payload["blockers"][:3]:
            print(f"     - {item}")
    if payload.get("commitments_due"):
        print("   Commitments due:")
        for item in payload["commitments_due"][:3]:
            print(f"     - {item}")
    followups = (payload.get("followups_due") or {}).get("items", [])
    if followups:
        print("   Follow-ups due:")
        for item in followups[:3]:
            deadline = item.get("deadline") or "-"
            print(f"     - [{item.get('bucket', 'active')}] {item['item']} (deadline: {deadline})")
    decisions = payload.get("recent_decisions", [])
    if decisions:
        print("   Recent decisions:")
        for item in decisions[:3]:
            print(f"     - [{item.get('date', '-')}] {item['title']}")


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))
