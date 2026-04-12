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
  python3 scripts/ghost_learning_loop.py status
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent
LEARNINGS_DIR = WORKSPACE / ".learnings"
SKILLS_DIR = WORKSPACE / "skills"
PROPOSED_SKILLS_DIR = WORKSPACE / ".local" / "proposed-skills"
SKILL_IMPROVEMENTS_DIR = WORKSPACE / ".local" / "skill-improvements"
STATE_FILE = LEARNINGS_DIR / "learning-review-state.json"

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


def _load_state(state_file: Path | None = None) -> dict:
    path = state_file or STATE_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"items": {}, "last_scan": None, "version": 2}


def _save_state(state: dict, state_file: Path | None = None) -> None:
    path = state_file or STATE_FILE
    state["last_updated"] = datetime.now().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _next_learning_id(scope_file: Path) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"LRN-{today}-"
    count = 1
    if scope_file.exists():
        matches = re.findall(rf"\[{re.escape(prefix)}(\d+)\]", scope_file.read_text(encoding="utf-8"))
        if matches:
            count = max(int(m) for m in matches) + 1
    return f"{prefix}{count:03d}"


def _content_is_safe(text: str) -> bool:
    """Check content safety via memory_content_scanner if available."""
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from memory_content_scanner import is_safe
        return is_safe(text)
    except ImportError:
        return True


def _check_duplicate(filepath: str, new_entry: str) -> bool:
    """Return True if duplicate detected (i.e. NOT safe to write)."""
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
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
    with open(scope_file, "a", encoding="utf-8") as f:
        f.write(entry_text)

    result["captured"] = True
    result["entries"].append({
        "id": entry_id,
        "category": category,
        "scope": str(scope_file.relative_to(WORKSPACE)),
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


def learning_status(state_file: str | None = None) -> dict:
    """Return stats about the learning system."""
    sf = Path(state_file) if state_file else STATE_FILE
    state = _load_state(sf)

    by_state: dict[str, int] = {}
    for sr in state["items"].values():
        ls = sr.get("learning_state", "observed")
        by_state[ls] = by_state.get(ls, 0) + 1

    today = datetime.now().strftime("%Y-%m-%d")
    due_count = sum(
        1 for sr in state["items"].values()
        if not sr.get("graduated") and sr.get("next_review", "9999-12-31") <= today
    )

    last_captured = state.get("last_updated")

    pending_skills = 0
    if PROPOSED_SKILLS_DIR.exists():
        pending_skills = sum(1 for d in PROPOSED_SKILLS_DIR.iterdir() if d.is_dir())

    pending_improvements = 0
    if SKILL_IMPROVEMENTS_DIR.exists():
        pending_improvements = sum(1 for f in SKILL_IMPROVEMENTS_DIR.glob("*.md"))

    return {
        "total_learnings": len(state["items"]),
        "by_state": by_state,
        "due_for_review": due_count,
        "last_captured": last_captured,
        "skill_candidates_pending": pending_skills,
        "skill_improvements_pending": pending_improvements,
    }


def _print_status(stats: dict) -> None:
    print(f"📊 Learning Loop Status")
    print(f"   Total learnings: {stats['total_learnings']}")
    print(f"   Due for review: {stats['due_for_review']}")
    print(f"   Last captured: {stats['last_captured'] or 'never'}")
    print(f"   Skill candidates pending: {stats['skill_candidates_pending']}")
    print(f"   Skill improvements pending: {stats['skill_improvements_pending']}")
    print(f"   By state:")
    for state_name in ["proposed", "observed", "validated", "promoted", "archived"]:
        count = stats["by_state"].get(state_name, 0)
        if count:
            print(f"     {state_name}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Ghost Brain — Unified Learning Loop")
    sub = parser.add_subparsers(dest="command")

    reflect_p = sub.add_parser("reflect", help="Post-task reflection")
    reflect_p.add_argument("task_summary", help="Summary of the task")
    reflect_p.add_argument("outcome", help="Outcome of the task")
    reflect_p.add_argument("--errors", default="", help="Comma-separated error list")

    detect_p = sub.add_parser("detect-skill", help="Detect skill candidate from task log")
    detect_p.add_argument("task_log", help="Task log text")

    check_p = sub.add_parser("check-skill", help="Check skill for improvement needs")
    check_p.add_argument("skill_name", help="Name of the skill")
    check_p.add_argument("execution_log", help="Execution log text")
    check_p.add_argument("--success", dest="success", action="store_true", default=True)
    check_p.add_argument("--failure", dest="success", action="store_false")

    sub.add_parser("promote", help="Auto-promote qualified learnings")
    sub.add_parser("status", help="Show learning loop status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "reflect":
        errors = [e.strip() for e in args.errors.split(",") if e.strip()] or None
        result = post_task_reflection(args.task_summary, args.outcome, errors)
        if result["captured"]:
            for entry in result["entries"]:
                print(f"✅ Captured [{entry['id']}] ({entry['category']}) → {entry['scope']}")
            if result["proposed_skill"]:
                print(f"💡 Skill candidate detected: {result['proposed_skill']}")
        else:
            print("ℹ️  No learning signal detected — nothing captured.")

    elif args.command == "detect-skill":
        candidate = detect_skill_candidate(args.task_log)
        if candidate:
            print(f"💡 Skill candidate: {candidate['name']}")
            print(f"   Steps: {len(candidate['steps'])}")
            print(f"   Description: {candidate['description'][:100]}")
            print(json.dumps(candidate, indent=2, ensure_ascii=False))
        else:
            print("ℹ️  No skill candidate detected.")

    elif args.command == "check-skill":
        result = check_skill_improvement(args.skill_name, args.execution_log, args.success)
        if result:
            print(f"⚠️  Improvement needed for {result['skill_name']}")
            print(f"   Issue: {result['issue']}")
            print(f"   Fix: {result['proposed_fix']}")
        else:
            print(f"✅ {args.skill_name} executed cleanly.")

    elif args.command == "promote":
        promoted = auto_promote_learnings()
        if promoted:
            for item in promoted:
                print(f"⬆️  [{item['id']}] → {item['action']} ({item['reason']})")
        else:
            print("ℹ️  No learnings qualify for promotion right now.")

    elif args.command == "status":
        stats = learning_status()
        _print_status(stats)


if __name__ == "__main__":
    main()
