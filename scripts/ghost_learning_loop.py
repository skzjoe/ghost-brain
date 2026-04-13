#!/usr/bin/env python3
"""
Ghost Brain — Unified Learning Loop Engine

Closed-loop self-improvement system: captures learnings from task outcomes,
detects skill candidates, proposes improvements, and auto-promotes validated learnings.

Usage:
  python3 scripts/ghost_learning_loop.py reflect 'task summary' 'outcome' [--errors 'e1,e2']
  python3 scripts/ghost_learning_loop.py detect-skill 'task log text'
  python3 scripts/ghost_learning_loop.py check-skill skill_name 'execution log' [--success/--failure]
  python3 scripts/ghost_learning_loop.py promote
  python3 scripts/ghost_learning_loop.py status [--json]
  python3 scripts/ghost_learning_loop.py digest [--days 30] [--json]
"""

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ghost_core.contracts import LearningReflectionRequest
from ghost_core.defaults import build_default_runtime
from ghost_core_contracts import LearningDigest
from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths()
WORKSPACE = _paths.workspace
LEARNINGS_DIR = _paths.learnings_dir
SKILLS_DIR = _paths.skills_dir
PROPOSED_SKILLS_DIR = _paths.local_dir / "proposed-skills"
SKILL_IMPROVEMENTS_DIR = _paths.local_dir / "skill-improvements"
STATE_FILE = LEARNINGS_DIR / "learning-review-state.json"


def _runtime():
    return build_default_runtime(str(WORKSPACE))

CORRECTION_KEYWORDS = re.compile(
    r"correct(ed|ion)|fix(ed)?|wrong|mistake|should have|instead of|actually",
    re.IGNORECASE,
)
ERROR_KEYWORDS = re.compile(
    r"error|fail(ed|ure)?|exception|crash|broke|timeout|404|500|traceback",
    re.IGNORECASE,
)
PATTERN_KEYWORDS = re.compile(
    r"pattern|workflow|always do|every time|repeat(ed)?|reusable|template|recipe",
    re.IGNORECASE,
)

MULTI_STEP_PATTERN = re.compile(
    r"(step \d|then |after that|next,? |finally )",
    re.IGNORECASE,
)


def _default_state() -> dict:
    return {"items": {}, "last_scan": None, "version": 3}


def _normalize_state(state: dict | None) -> dict:
    normalized = dict(state or {})
    normalized.setdefault("items", {})
    normalized.setdefault("last_scan", None)
    normalized["version"] = max(int(normalized.get("version", 3) or 3), 3)

    for item_id, item in normalized["items"].items():
        item.setdefault("level", 0)
        item.setdefault("next_review", datetime.now().strftime("%Y-%m-%d"))
        item.setdefault("last_reviewed", None)
        item.setdefault("times_surfaced", 0)
        item.setdefault("times_reinforced", 0)
        item.setdefault("graduated", False)
        item.setdefault("learning_state", "observed")
        item.setdefault("logged", item.get("captured_at") or item.get("created_at"))
        item.setdefault("captured_at", item.get("logged") or item.get("created_at"))
        item.setdefault("validated_at", item.get("validated_at"))
        item.setdefault("promoted_at", item.get("promoted_at"))
        item.setdefault("source_scope", item.get("scope", ""))
        item.setdefault("category", item.get("category", "observation"))
    return normalized


def _load_state(state_file: Path | None = None) -> dict:
    path = state_file or STATE_FILE
    if path.exists():
        return _normalize_state(json.loads(path.read_text(encoding="utf-8")))
    return _default_state()


def _save_state(state: dict, state_file: Path | None = None) -> None:
    path = state_file or STATE_FILE
    state = _normalize_state(state)
    state["version"] = 3
    state["last_updated"] = datetime.now().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp:
        json.dump(state, tmp, indent=2, ensure_ascii=False, sort_keys=True)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _record_learning_capture(
    state: dict, entry_id: str, category: str, scope: str, logged_at: str,
) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    item = state.setdefault("items", {}).setdefault(entry_id, {})
    item.update({
        "level": item.get("level", 0),
        "next_review": item.get("next_review", today),
        "last_reviewed": item.get("last_reviewed"),
        "times_surfaced": item.get("times_surfaced", 0),
        "times_reinforced": item.get("times_reinforced", 0),
        "graduated": item.get("graduated", False),
        "learning_state": item.get("learning_state", "proposed"),
        "logged": item.get("logged", logged_at),
        "captured_at": logged_at,
        "validated_at": item.get("validated_at"),
        "promoted_at": item.get("promoted_at"),
        "source_scope": scope,
        "category": category,
    })
    return state


def _make_json_response(command: str, data: dict, ok: bool = True,
                        errors: list | None = None, warnings: list | None = None) -> dict:
    return {
        "schema_version": "ghost-learning-loop/v1",
        "command": command,
        "ok": ok,
        "generated_at": datetime.now().isoformat(),
        "data": data,
        "errors": errors or [],
        "warnings": warnings or [],
    }


def _emit_result(command: str, data: dict, json_mode: bool,
                 errors: list | None = None, warnings: list | None = None) -> None:
    if json_mode:
        print(json.dumps(
            _make_json_response(command, data, ok=not errors, errors=errors, warnings=warnings),
            indent=2,
            ensure_ascii=False,
        ))


def _next_learning_id(scope_file: Path) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"LRN-{today}-"
    count = 1
    matches: list[int] = []
    if LEARNINGS_DIR.exists():
        for md in LEARNINGS_DIR.rglob("*.md"):
            try:
                found = re.findall(rf"\[{re.escape(prefix)}(\d+)\]", md.read_text(encoding="utf-8"))
            except OSError:
                continue
            matches.extend(int(m) for m in found)
    if matches:
        count = max(matches) + 1
    return f"{prefix}{count:03d}"


def _content_is_safe(text: str) -> bool:
    """Check content safety via memory_content_scanner if available."""
    try:
        from memory_content_scanner import is_safe
        return is_safe(text)
    except ImportError:
        return True


def _check_duplicate(filepath: str, new_entry: str) -> bool:
    """Return True if duplicate detected (i.e. NOT safe to write)."""
    try:
        from memory_content_scanner import check_duplicate
        result = check_duplicate(filepath, new_entry)
        return not result.safe
    except ImportError:
        return False


def _determine_scope(task_summary: str, outcome: str) -> Path:
    """Pick the narrowest valid scope file for a learning entry."""
    combined = f"{task_summary} {outcome}".lower()

    projects_dir = LEARNINGS_DIR / "projects"
    if projects_dir.exists():
        for project_file in projects_dir.glob("*.md"):
            if project_file.stem.lower() != "readme":
                project_name = project_file.stem.replace("-", " ").replace("_", " ")
                if project_name in combined:
                    return project_file

    domains_dir = LEARNINGS_DIR / "domains"
    if domains_dir.exists():
        for domain_file in domains_dir.glob("*.md"):
            domain_name = domain_file.stem.lower()
            if domain_name in combined:
                return domain_file

    return LEARNINGS_DIR / "LEARNINGS.md"


def _classify_learning(task_summary: str, outcome: str, errors: list | None) -> str:
    combined = f"{task_summary} {outcome}"
    if errors:
        return "error_recovery"
    if CORRECTION_KEYWORDS.search(combined):
        return "correction"
    if PATTERN_KEYWORDS.search(combined):
        return "best_practice"
    return "observation"


def _format_learning_entry(
    entry_id: str, category: str, task_summary: str, outcome: str,
    errors: list | None, area: str = "ops",
) -> str:
    now = datetime.now().isoformat()
    priority = "high" if errors else "medium"

    lines = [
        f"\n## [{entry_id}] {category}\n",
        f"**Logged**: {now}",
        f"**Priority**: {priority}",
        "**Status**: pending",
        "**State**: proposed",
        f"**Area**: {area}\n",
        "### Summary",
        f"{task_summary}\n",
        "### Details",
        f"Outcome: {outcome}",
    ]
    if errors:
        lines.append(f"Errors encountered: {'; '.join(errors)}")
    lines.extend([
        "\n### Metadata",
        "- Source: auto_reflection",
        f"- Tags: learning-loop, {category}",
        "\n---\n",
    ])
    return "\n".join(lines)


def _task_has_signal(task_summary: str, outcome: str, errors: list | None) -> bool:
    if errors:
        return True
    combined = f"{task_summary} {outcome}"
    return bool(
        CORRECTION_KEYWORDS.search(combined)
        or ERROR_KEYWORDS.search(combined)
        or PATTERN_KEYWORDS.search(combined)
    )


def post_task_reflection(
    task_summary: str, outcome: str, errors: list | None = None,
) -> dict:
    """Analyze a completed task and capture learnings if warranted."""
    result: dict = {"captured": False, "entries": [], "proposed_skill": None}

    if not _task_has_signal(task_summary, outcome, errors):
        return result

    scope_file = _determine_scope(task_summary, outcome)
    category = _classify_learning(task_summary, outcome, errors)
    entry_id = _next_learning_id(scope_file)
    entry_text = _format_learning_entry(entry_id, category, task_summary, outcome, errors)

    if not _content_is_safe(entry_text):
        return result

    if _check_duplicate(str(scope_file), entry_text):
        return result

    scope_file.parent.mkdir(parents=True, exist_ok=True)
    logged_at = datetime.now().isoformat()
    with open(scope_file, "a", encoding="utf-8") as f:
        f.write(entry_text)

    state = _load_state()
    state = _record_learning_capture(
        state,
        entry_id=entry_id,
        category=category,
        scope=str(scope_file.relative_to(WORKSPACE)),
        logged_at=logged_at,
    )
    _save_state(state)

    result["captured"] = True
    result["entries"].append({
        "id": entry_id,
        "category": category,
        "scope": str(scope_file.relative_to(WORKSPACE)),
        "captured_at": logged_at,
    })

    if PATTERN_KEYWORDS.search(f"{task_summary} {outcome}"):
        result["proposed_skill"] = f"skill-from-{entry_id.lower()}"

    return result


def _list_existing_skills(workspace_path: Path | None = None) -> list[str]:
    skills_dir = (workspace_path or WORKSPACE) / "skills"
    if not skills_dir.exists():
        return []
    return [d.name for d in skills_dir.iterdir() if d.is_dir()]


def detect_skill_candidate(
    task_log: str, workspace_path: str | None = None,
) -> dict | None:
    """Analyze task_log for repeated multi-step patterns worth extracting as a skill."""
    ws = Path(workspace_path) if workspace_path else WORKSPACE

    steps = MULTI_STEP_PATTERN.findall(task_log)
    if len(steps) < 2:
        return None

    step_lines = []
    for line in task_log.split("\n"):
        if MULTI_STEP_PATTERN.search(line):
            step_lines.append(line.strip())

    name_words = []
    for word in task_log.lower().split()[:10]:
        cleaned = re.sub(r"[^a-z0-9]", "", word)
        if cleaned and len(cleaned) > 2 and cleaned not in ("the", "and", "then", "step", "next", "after", "that", "finally"):
            name_words.append(cleaned)
    candidate_name = "-".join(name_words[:3]) or "unnamed-skill"

    existing = _list_existing_skills(ws)
    for skill_name in existing:
        normalized_existing = skill_name.lower().replace("-", " ")
        normalized_candidate = candidate_name.replace("-", " ")
        overlap = set(normalized_existing.split()) & set(normalized_candidate.split())
        if len(overlap) >= 2:
            return None

    description_source = task_log[:200].replace("\n", " ").strip()

    return {
        "name": candidate_name,
        "description": description_source,
        "steps": step_lines or [s.strip() for s in task_log.split("\n") if s.strip()][:5],
        "source_task": task_log[:500],
    }


def propose_skill_creation(
    candidate: dict, workspace_path: str | None = None,
) -> str:
    """Generate a SKILL.md draft and save to .local/proposed-skills/."""
    ws = Path(workspace_path) if workspace_path else WORKSPACE
    output_dir = ws / ".local" / "proposed-skills" / candidate["name"]
    output_dir.mkdir(parents=True, exist_ok=True)

    steps_md = "\n".join(f"   {i+1}. {s}" for i, s in enumerate(candidate.get("steps", [])))

    skill_md = (
        "---\n"
        f"name: {candidate['name']}\n"
        f"description: \"{candidate.get('description', 'Auto-detected skill candidate')}\"\n"
        "status: proposed\n"
        "---\n\n"
        f"# {candidate['name']}\n\n"
        f"{candidate.get('description', '')}\n\n"
        "## Steps\n\n"
        f"{steps_md}\n\n"
        "## Source\n\n"
        f"Detected from task log on {datetime.now().strftime('%Y-%m-%d')}.\n\n"
        "---\n"
        "**Status:** proposed — requires user approval before installing to skills/\n"
    )

    skill_path = output_dir / "SKILL.md"
    skill_path.write_text(skill_md, encoding="utf-8")
    return str(skill_path)


def check_skill_improvement(
    skill_name: str, execution_log: str, success: bool,
) -> dict | None:
    """After a skill is used, check if it needs improvement."""
    if success and not ERROR_KEYWORDS.search(execution_log):
        return None

    issues = []
    if not success:
        issues.append("Skill execution failed")
    if ERROR_KEYWORDS.search(execution_log):
        error_matches = ERROR_KEYWORDS.findall(execution_log)
        issues.append(f"Errors detected: {', '.join(set(m if isinstance(m, str) else m[0] for m in error_matches[:3]))}")
    if CORRECTION_KEYWORDS.search(execution_log):
        issues.append("Manual corrections were needed")

    if not issues:
        return None

    issue_summary = "; ".join(issues)
    proposed_fix = f"Review {skill_name} for: {issue_summary}. Check execution log for details."

    SKILL_IMPROVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    improvement_path = SKILL_IMPROVEMENTS_DIR / f"{skill_name}.md"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n## Improvement proposal — {now}\n\n"
        f"**Skill:** {skill_name}\n"
        f"**Success:** {'yes' if success else 'no'}\n"
        f"**Issues:** {issue_summary}\n"
        f"**Proposed fix:** {proposed_fix}\n\n"
        "### Execution log excerpt\n\n"
        f"```\n{execution_log[:1000]}\n```\n\n---\n"
    )

    with open(improvement_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return {
        "skill_name": skill_name,
        "issue": issue_summary,
        "proposed_fix": proposed_fix,
    }


def auto_promote_learnings(state_file: str | None = None) -> list:
    """Scan state and auto-promote learnings that meet promotion criteria."""
    sf = Path(state_file) if state_file else STATE_FILE
    state = _load_state(sf)
    promoted = []
    now = datetime.now()

    for item_id, sr in state["items"].items():
        current_state = sr.get("learning_state", "observed")

        if current_state == "observed" and sr.get("times_reinforced", 0) >= 3:
            sr["learning_state"] = "validated"
            sr["validated_at"] = now.strftime("%Y-%m-%d")
            promoted.append({
                "id": item_id,
                "action": "validated",
                "reason": f"times_reinforced={sr['times_reinforced']} >= 3",
            })

        if current_state == "validated":
            reinforced = sr.get("times_reinforced", 0)
            logged_str = sr.get("logged", "")
            age_qualifies = False
            if logged_str:
                try:
                    logged_date = datetime.fromisoformat(logged_str.replace("Z", "+00:00"))
                    age_qualifies = (now - logged_date.replace(tzinfo=None)) > timedelta(days=30)
                except (ValueError, TypeError):
                    pass

            if reinforced >= 5 or age_qualifies:
                sr["learning_state"] = "promoted"
                sr["promoted_at"] = now.strftime("%Y-%m-%d")
                sr["graduated"] = True
                sr["next_review"] = "9999-12-31"
                promoted.append({
                    "id": item_id,
                    "action": "promoted",
                    "reason": f"times_reinforced={reinforced}, age_qualifies={age_qualifies}",
                })

    if promoted:
        _save_state(state, sf)

    return promoted


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def _count_recent_items(items: dict, field_names: list[str], days: int) -> int:
    cutoff = datetime.now() - timedelta(days=days)
    count = 0
    for sr in items.values():
        seen = False
        for field in field_names:
            dt = _parse_dt(sr.get(field))
            if dt and dt >= cutoff:
                seen = True
                break
        if seen:
            count += 1
    return count


def _latest_item_timestamp(items: dict, field_names: list[str]) -> str | None:
    latest: datetime | None = None
    for sr in items.values():
        for field in field_names:
            dt = _parse_dt(sr.get(field))
            if dt and (latest is None or dt > latest):
                latest = dt
    return latest.isoformat() if latest else None


def _build_impact_metrics(state: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    items = state.get("items", {})
    total = len(items)
    captured_7d = _count_recent_items(items, ["captured_at", "logged", "created_at"], 7)
    captured_30d = _count_recent_items(items, ["captured_at", "logged", "created_at"], 30)
    validated_30d = _count_recent_items(items, ["validated_at"], 30)
    promoted_30d = _count_recent_items(items, ["promoted_at"], 30)
    avg_reinforcements = (
        sum(item.get("times_reinforced", 0) for item in items.values()) / total
        if total else 0.0
    )
    today = now.strftime("%Y-%m-%d")
    due = sum(1 for item in items.values() if not item.get("graduated") and item.get("next_review", "9999-12-31") <= today)
    overdue = sum(1 for item in items.values() if not item.get("graduated") and item.get("next_review", "9999-12-31") < today)

    capture_to_validate_rate = round(validated_30d / captured_30d, 3) if captured_30d else 0.0
    validate_to_promote_rate = round(promoted_30d / validated_30d, 3) if validated_30d else 0.0
    overdue_rate = round(overdue / due, 3) if due else 0.0

    return {
        "captured_7d": captured_7d,
        "captured_30d": captured_30d,
        "validated_30d": validated_30d,
        "promoted_30d": promoted_30d,
        "capture_to_validate_rate": capture_to_validate_rate,
        "validate_to_promote_rate": validate_to_promote_rate,
        "avg_reinforcements_per_learning": round(avg_reinforcements, 2),
        "overdue_count": overdue,
        "overdue_rate": overdue_rate,
    }


def _recommended_actions(stats: dict) -> list[str]:
    actions = []
    if stats.get("due_for_review", 0) > 0:
        actions.append(f"Review {stats['due_for_review']} due learning(s) to prevent drift.")
    if stats.get("skill_improvements_pending", 0) > 0:
        actions.append("Apply pending skill improvements before the next repeated workflow.")
    if stats.get("skill_candidates_pending", 0) > 0:
        actions.append("Convert pending skill candidates into reusable skills or archive them.")
    if stats.get("recent_promotions_30d", 0) == 0 and stats.get("total_learnings", 0) > 0:
        actions.append("No recent promotions, review whether validated learnings should graduate into stable guidance.")
    if not actions:
        actions.append("Learning loop looks healthy, keep capturing non-trivial corrections and patterns.")
    return actions


def learning_status(state_file: str | None = None) -> dict:
    """Return stats about the learning system."""
    sf = Path(state_file) if state_file else STATE_FILE
    state = _load_state(sf)

    by_state: dict[str, int] = {}
    for sr in state["items"].values():
        ls = sr.get("learning_state", "observed")
        by_state[ls] = by_state.get(ls, 0) + 1

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    due_count = sum(
        1 for sr in state["items"].values()
        if not sr.get("graduated") and sr.get("next_review", "9999-12-31") <= today
    )
    overdue_count = sum(
        1 for sr in state["items"].values()
        if not sr.get("graduated") and sr.get("next_review", "9999-12-31") < today
    )

    last_captured = _latest_item_timestamp(state["items"], ["captured_at", "logged", "created_at"])

    pending_skills = 0
    if PROPOSED_SKILLS_DIR.exists():
        pending_skills = sum(1 for d in PROPOSED_SKILLS_DIR.iterdir() if d.is_dir())

    pending_improvements = 0
    if SKILL_IMPROVEMENTS_DIR.exists():
        pending_improvements = sum(1 for f in SKILL_IMPROVEMENTS_DIR.glob("*.md"))

    validated_total = by_state.get("validated", 0)
    promoted_total = by_state.get("promoted", 0)
    recent_captures = _count_recent_items(state["items"], ["captured_at", "logged", "created_at"], 7)
    recent_validations = _count_recent_items(state["items"], ["validated_at"], 30)
    recent_promotions = _count_recent_items(state["items"], ["promoted_at"], 30)
    impact = _build_impact_metrics(state, now=now)
    backlog = {
        "due": due_count,
        "overdue": overdue_count,
        "graduated": sum(1 for sr in state["items"].values() if sr.get("graduated")),
    }

    stats = {
        "total_learnings": len(state["items"]),
        "by_state": by_state,
        "due_for_review": due_count,
        "last_captured": last_captured,
        "skill_candidates_pending": pending_skills,
        "skill_improvements_pending": pending_improvements,
        "validated_total": validated_total,
        "promoted_total": promoted_total,
        "recent_captures_7d": recent_captures,
        "recent_validations_30d": recent_validations,
        "recent_promotions_30d": recent_promotions,
        "impact": impact,
        "backlog": backlog,
    }
    stats["recommended_actions"] = _recommended_actions(stats)
    return stats


def learning_digest(state_file: str | None = None, days: int = 30) -> dict:
    """Return an automation-friendly digest of learning impact and backlog."""
    stats = learning_status(state_file)
    sf = Path(state_file) if state_file else STATE_FILE
    state = _load_state(sf)

    digest = LearningDigest(
        generated_at=datetime.now().isoformat(),
        window_days=days,
        total_learnings=stats["total_learnings"],
        due_for_review=stats["due_for_review"],
        validated_total=stats["validated_total"],
        promoted_total=stats["promoted_total"],
        recent_captures=_count_recent_items(state["items"], ["captured_at", "logged", "created_at"], days),
        recent_validations=_count_recent_items(state["items"], ["validated_at"], days),
        recent_promotions=_count_recent_items(state["items"], ["promoted_at"], days),
        skill_candidates_pending=stats["skill_candidates_pending"],
        skill_improvements_pending=stats["skill_improvements_pending"],
        recommended_actions=stats["recommended_actions"],
    )
    payload = digest.to_dict()
    payload["headline"] = (
        f"{payload['recent_captures']} captured, {payload['recent_validations']} validated, "
        f"{payload['recent_promotions']} promoted in the last {days} days"
    )
    payload["highlights"] = [
        f"Validated total: {payload['validated_total']}",
        f"Promoted total: {payload['promoted_total']}",
    ]
    payload["needs_attention"] = [
        f"{payload['due_for_review']} learning(s) due for review",
        f"{payload['skill_candidates_pending']} pending skill candidate(s)",
        f"{payload['skill_improvements_pending']} pending skill improvement file(s)",
    ]
    payload["pending_skill_candidates"] = payload["skill_candidates_pending"]
    payload["pending_skill_improvements"] = payload["skill_improvements_pending"]
    return payload


def _print_status(stats: dict) -> None:
    print(f"📊 Learning Loop Status")
    print(f"   Total learnings: {stats['total_learnings']}")
    print(f"   Due for review: {stats['due_for_review']}")
    print(f"   Validated: {stats['validated_total']}")
    print(f"   Promoted: {stats['promoted_total']}")
    print(f"   Last captured: {stats['last_captured'] or 'never'}")
    print(f"   Recent captures (7d): {stats['recent_captures_7d']}")
    print(f"   Recent validations (30d): {stats['recent_validations_30d']}")
    print(f"   Recent promotions (30d): {stats['recent_promotions_30d']}")
    print(f"   Skill candidates pending: {stats['skill_candidates_pending']}")
    print(f"   Skill improvements pending: {stats['skill_improvements_pending']}")
    print(
        f"   Impact: captured7d={stats['impact']['captured_7d']} | "
        f"validated30d={stats['impact']['validated_30d']} | "
        f"promoted30d={stats['impact']['promoted_30d']}"
    )
    print(
        f"   Backlog: due={stats['backlog']['due']} | overdue={stats['backlog']['overdue']} | "
        f"graduated={stats['backlog']['graduated']}"
    )
    print(f"   By state:")
    for state_name in ["proposed", "observed", "validated", "promoted", "archived"]:
        count = stats["by_state"].get(state_name, 0)
        if count:
            print(f"     {state_name}: {count}")
    if stats.get("recommended_actions"):
        print(f"   Recommended actions:")
        for action in stats["recommended_actions"][:3]:
            print(f"     - {action}")


def _print_digest(digest: dict) -> None:
    print("📈 Learning Impact Digest")
    print(f"   Window: {digest['window_days']} days")
    print(f"   Headline: {digest['headline']}")
    print(f"   Total learnings: {digest['total_learnings']}")
    print(f"   Due for review: {digest['due_for_review']}")
    print(f"   Recent captures: {digest['recent_captures']}")
    print(f"   Recent validations: {digest['recent_validations']}")
    print(f"   Recent promotions: {digest['recent_promotions']}")
    print(f"   Validated total: {digest['validated_total']}")
    print(f"   Promoted total: {digest['promoted_total']}")
    print(f"   Skill candidates pending: {digest['skill_candidates_pending']}")
    print(f"   Skill improvements pending: {digest['skill_improvements_pending']}")
    if digest.get("highlights"):
        print("   Highlights:")
        for line in digest["highlights"][:3]:
            print(f"     - {line}")
    if digest.get("needs_attention"):
        print("   Needs attention:")
        for line in digest["needs_attention"][:3]:
            print(f"     - {line}")
    print("   Recommended actions:")
    for action in digest["recommended_actions"][:3]:
        print(f"     - {action}")


def main():
    parser = argparse.ArgumentParser(description="Ghost Brain — Unified Learning Loop")
    sub = parser.add_subparsers(dest="command")

    reflect_p = sub.add_parser("reflect", help="Post-task reflection")
    reflect_p.add_argument("task_summary", help="Summary of the task")
    reflect_p.add_argument("outcome", help="Outcome of the task")
    reflect_p.add_argument("--errors", default="", help="Comma-separated error list")
    reflect_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    detect_p = sub.add_parser("detect-skill", help="Detect skill candidate from task log")
    detect_p.add_argument("task_log", help="Task log text")
    detect_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    check_p = sub.add_parser("check-skill", help="Check skill for improvement needs")
    check_p.add_argument("skill_name", help="Name of the skill")
    check_p.add_argument("execution_log", help="Execution log text")
    check_p.add_argument("--success", dest="success", action="store_true", default=True)
    check_p.add_argument("--failure", dest="success", action="store_false")
    check_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    promote_p = sub.add_parser("promote", help="Auto-promote qualified learnings")
    promote_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    status_p = sub.add_parser("status", help="Show learning loop status")
    status_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    digest_p = sub.add_parser("digest", help="Show learning impact digest")
    digest_p.add_argument("--days", type=int, default=30, help="Rolling window in days")
    digest_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")

    args = parser.parse_args()
    runtime = _runtime()

    if not args.command:
        parser.print_help()
        return

    if args.command == "reflect":
        errors = [e.strip() for e in args.errors.split(",") if e.strip()] or None
        result = runtime.learning.reflect(
            LearningReflectionRequest(
                task_summary=args.task_summary,
                outcome=args.outcome,
                errors=errors or [],
            )
        ).to_dict()
        if getattr(args, "json", False):
            _emit_result("reflect", result, True)
            return
        if result["captured"]:
            for entry in result["entries"]:
                print(f"✅ Captured [{entry['id']}] ({entry['category']}) → {entry['scope']}")
            if result["proposed_skill"]:
                print(f"💡 Skill candidate detected: {result['proposed_skill']}")
        else:
            print("ℹ️  No learning signal detected — nothing captured.")

    elif args.command == "detect-skill":
        candidate = runtime.learning.detect_skill_candidate(args.task_log)
        if getattr(args, "json", False):
            _emit_result("detect-skill", candidate or {}, True)
            return
        if candidate:
            print(f"💡 Skill candidate: {candidate['name']}")
            print(f"   Steps: {len(candidate['steps'])}")
            print(f"   Description: {candidate['description'][:100]}")
            print(json.dumps(candidate, indent=2, ensure_ascii=False))
        else:
            print("ℹ️  No skill candidate detected.")

    elif args.command == "check-skill":
        result = runtime.learning.check_skill(args.skill_name, args.execution_log, args.success)
        if getattr(args, "json", False):
            _emit_result("check-skill", result or {"skill_name": args.skill_name, "clean": True}, True)
            return
        if result:
            print(f"⚠️  Improvement needed for {result['skill_name']}")
            print(f"   Issue: {result['issue']}")
            print(f"   Fix: {result['proposed_fix']}")
        else:
            print(f"✅ {args.skill_name} executed cleanly.")

    elif args.command == "promote":
        promoted = runtime.learning.promote()
        if getattr(args, "json", False):
            _emit_result("promote", {"actions": promoted}, True)
            return
        if promoted:
            for item in promoted:
                print(f"⬆️  [{item['id']}] → {item['action']} ({item['reason']})")
        else:
            print("ℹ️  No learnings qualify for promotion right now.")

    elif args.command == "status":
        stats = runtime.learning.status().to_dict()
        if args.json:
            _emit_result("status", stats, True)
        else:
            _print_status(stats)

    elif args.command == "digest":
        digest = runtime.learning.digest(days=args.days).to_dict()
        if args.json:
            _emit_result("digest", digest, True)
        else:
            _print_digest(digest)


if __name__ == "__main__":
    main()
