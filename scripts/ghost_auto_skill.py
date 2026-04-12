#!/usr/bin/env python3
"""
Ghost Brain — Auto Skill Pipeline

Immune-system approach to skill management: create skills from experience,
validate through real usage, self-improve on failure, retire what doesn't work.

Zero review burden — user sees a dashboard, not an approval queue.

Lifecycle:
  detect  → is this task skill-worthy?
  create  → generate skill draft in skills/.auto/
  match   → find matching auto-skill for incoming task
  record  → track success/failure from real usage
  improve → revise skill based on failure context
  promote → graduate to active (manual or auto at threshold)
  retire  → deactivate underperforming skills
  status  → dashboard view
  list    → list all auto-skills with stats
  cleanup → remove retired skills

State: .local/auto_skills.json
Skills: skills/.auto/<name>/SKILL.md

Auto-promote: 3+ successes, 0 failures, success_rate >= 90%
Auto-retire: 3+ uses, success_rate < 50%

Usage:
  python3 scripts/ghost_auto_skill.py detect '<task_log>'
  python3 scripts/ghost_auto_skill.py create '<name>' '<task_log>' [description]
  python3 scripts/ghost_auto_skill.py match '<task_description>'
  python3 scripts/ghost_auto_skill.py record <skill_id> success|failure
  python3 scripts/ghost_auto_skill.py improve <skill_id> '<failure_context>'
  python3 scripts/ghost_auto_skill.py promote <skill_id>
  python3 scripts/ghost_auto_skill.py retire <skill_id>
  python3 scripts/ghost_auto_skill.py status
  python3 scripts/ghost_auto_skill.py list
  python3 scripts/ghost_auto_skill.py cleanup
"""

import json
import os
import sys
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
STATE_FILE = WORKSPACE / ".local" / "auto_skills.json"
SKILLS_AUTO_DIR = WORKSPACE / "skills" / ".auto"
SKILLS_DIR = WORKSPACE / "skills"

PROMOTE_MIN_SUCCESSES = 3
PROMOTE_MIN_RATE = 0.9
RETIRE_MIN_USES = 3
RETIRE_MAX_RATE = 0.5
SIMILARITY_THRESHOLD = 0.3


def _load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"skills": {}, "version": 1}


def _save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _skill_id(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60]


def _extract_keywords(text):
    stop = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "just", "and", "but", "or", "if", "this",
        "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
        "he", "she", "it", "they", "them", "what", "which", "who", "whom",
    }
    words = re.findall(r"[a-z0-9_\-\.]+", text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in stop]
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:30]


def _keyword_similarity(kw1, kw2):
    if not kw1 or not kw2:
        return 0.0
    s1, s2 = set(kw1), set(kw2)
    intersection = s1 & s2
    union = s1 | s2
    return len(intersection) / len(union) if union else 0.0


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _success_rate(skill):
    total = skill["usage"]["count"]
    if total == 0:
        return None
    return skill["usage"]["successes"] / total


# ─── Commands ────────────────────────────────────────────────────────


def cmd_detect(task_log):
    """
    Analyze a task log to determine if it's skill-worthy.

    Criteria:
    - Multi-step (3+ distinct actions or 5+ keywords)
    - Uses tools or structured workflow
    - Has sequential structure
    - Non-trivial length (>100 chars)
    """
    keywords = _extract_keywords(task_log)
    lines = task_log.strip().split("\n")

    signals = {
        "multi_step": len(lines) >= 3 or len(keywords) >= 5,
        "has_tools": any(
            t in task_log.lower()
            for t in [
                "exec", "write", "read", "browser", "fetch", "search",
                "python", "script", "api", "curl", "git", "npm",
                "spawn", "deploy", "build", "install", "configure",
            ]
        ),
        "has_structure": any(
            s in task_log.lower()
            for s in ["step", "then", "next", "first", "finally", "→", "->"]
        ),
        "not_trivial": len(task_log) > 100,
    }

    score = sum(signals.values()) / len(signals)
    worthy = score >= 0.5

    result = {
        "worthy": worthy,
        "score": round(score, 2),
        "signals": signals,
        "keywords": keywords[:15],
        "suggestion": (
            f"Skill-worthy (score: {score:.0%}). Create with: "
            f"ghost_auto_skill.py create '<name>' '<task_log>'"
            if worthy
            else f"Not skill-worthy (score: {score:.0%}). Too simple or one-off."
        ),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_create(name, task_log, description=None):
    """Create an auto-skill from a task log."""
    state = _load_state()
    sid = _skill_id(name)

    if sid in state["skills"] and state["skills"][sid]["status"] != "retired":
        print(f"⚠️  Skill '{sid}' already exists (status: {state['skills'][sid]['status']})")
        return None

    keywords = _extract_keywords(task_log)
    desc = description or f"Auto-generated skill from task: {name}"

    skill_dir = SKILLS_AUTO_DIR / sid
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = f"""# {name}

> Auto-generated by Ghost Auto Skill Pipeline
> Created: {_now_iso()}
> Status: draft — will auto-promote after {PROMOTE_MIN_SUCCESSES} successful uses

## Description
{desc}

## When to Use
This skill applies when the task matches these patterns:
- Keywords: {', '.join(keywords[:10])}

## Procedure
The following procedure was extracted from a successful task execution:

{task_log}

## Validation
- Created from real task execution
- Tracked via `.local/auto_skills.json`
- Will auto-promote after {PROMOTE_MIN_SUCCESSES}+ successes with ≥{PROMOTE_MIN_RATE:.0%} success rate
- Will auto-retire if success rate drops below {RETIRE_MAX_RATE:.0%} after {RETIRE_MIN_USES}+ uses
"""

    with open(skill_dir / "SKILL.md", "w") as f:
        f.write(skill_md)

    state["skills"][sid] = {
        "name": name,
        "description": desc,
        "created": _now_iso(),
        "source_task_hash": hashlib.sha256(task_log.encode()).hexdigest()[:16],
        "fingerprint": {"keywords": keywords},
        "status": "draft",
        "skill_path": str(skill_dir / "SKILL.md"),
        "usage": {
            "count": 0,
            "successes": 0,
            "failures": 0,
            "last_used": None,
        },
        "improvements": 0,
        "version": 1,
    }

    _save_state(state)
    print(f"✅ Created auto-skill: {sid}")
    print(f"   Path: {skill_dir / 'SKILL.md'}")
    print(f"   Keywords: {', '.join(keywords[:10])}")
    print(f"   Status: draft → auto-promotes at {PROMOTE_MIN_SUCCESSES} successes")
    return sid


def cmd_match(task_description):
    """Find the best matching auto-skill for a task description."""
    state = _load_state()
    task_kw = _extract_keywords(task_description)

    matches = []
    for sid, skill in state["skills"].items():
        if skill["status"] in ("retired",):
            continue
        skill_kw = skill["fingerprint"].get("keywords", [])
        sim = _keyword_similarity(task_kw, skill_kw)
        if sim >= SIMILARITY_THRESHOLD:
            matches.append({
                "skill_id": sid,
                "name": skill["name"],
                "similarity": round(sim, 3),
                "status": skill["status"],
                "success_rate": _success_rate(skill),
                "usage_count": skill["usage"]["count"],
                "path": skill["skill_path"],
            })

    matches.sort(key=lambda m: m["similarity"], reverse=True)

    if matches:
        print(f"🎯 Found {len(matches)} matching skill(s):")
        for m in matches[:5]:
            rate = f"{m['success_rate']:.0%}" if m['success_rate'] is not None else "n/a"
            print(
                f"   [{m['similarity']:.0%}] {m['name']} "
                f"(status: {m['status']}, used: {m['usage_count']}x, "
                f"success: {rate})"
            )
            print(f"         → {m['path']}")
    else:
        print("❌ No matching auto-skill found.")

    return matches


def cmd_record(skill_id, outcome):
    """Record a usage outcome. Triggers auto-promote or auto-retire."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return

    skill = state["skills"][skill_id]
    skill["usage"]["count"] += 1
    skill["usage"]["last_used"] = _now_iso()

    if outcome == "success":
        skill["usage"]["successes"] += 1
    elif outcome == "failure":
        skill["usage"]["failures"] += 1
    else:
        print(f"❌ Unknown outcome '{outcome}'. Use 'success' or 'failure'.")
        return

    rate = _success_rate(skill)
    action = None

    if (
        skill["status"] == "draft"
        and skill["usage"]["successes"] >= PROMOTE_MIN_SUCCESSES
        and rate is not None
        and rate >= PROMOTE_MIN_RATE
    ):
        skill["status"] = "active"
        action = "promoted"
        print(f"🎉 Auto-promoted '{skill_id}' → active (success rate: {rate:.0%})")

    if (
        skill["usage"]["count"] >= RETIRE_MIN_USES
        and rate is not None
        and rate < RETIRE_MAX_RATE
    ):
        skill["status"] = "retired"
        action = "retired"
        print(f"💀 Auto-retired '{skill_id}' (success rate: {rate:.0%})")

    _save_state(state)

    if not action:
        rate_str = f"{rate:.0%}" if rate is not None else "n/a"
        print(
            f"📝 Recorded {outcome} for '{skill_id}' "
            f"(total: {skill['usage']['count']}, "
            f"success rate: {rate_str})"
        )

    return action


def cmd_improve(skill_id, failure_context):
    """Add improvement notes from failure context to the skill."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return

    skill = state["skills"][skill_id]
    skill_path = Path(skill["skill_path"])

    if not skill_path.exists():
        print(f"❌ Skill file not found: {skill_path}")
        return

    improvement_note = f"""

## Improvement Note #{skill['improvements'] + 1} ({_now_iso()})
**Failure context:** {failure_context}
**Action needed:** Revise the procedure above to handle this case.
"""

    with open(skill_path, "a") as f:
        f.write(improvement_note)

    skill["improvements"] += 1
    new_kw = _extract_keywords(failure_context)
    existing = set(skill["fingerprint"]["keywords"])
    for kw in new_kw:
        if kw not in existing:
            skill["fingerprint"]["keywords"].append(kw)
            existing.add(kw)

    _save_state(state)
    print(f"🔧 Added improvement note #{skill['improvements']} to '{skill_id}'")
    print(f"   Revise: {skill_path}")
    return True


def cmd_promote(skill_id):
    """Manually promote a skill to active status."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return
    old_status = state["skills"][skill_id]["status"]
    state["skills"][skill_id]["status"] = "active"
    _save_state(state)
    print(f"✅ Promoted '{skill_id}': {old_status} → active")


def cmd_retire(skill_id):
    """Manually retire a skill."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return
    old_status = state["skills"][skill_id]["status"]
    state["skills"][skill_id]["status"] = "retired"
    _save_state(state)
    print(f"💀 Retired '{skill_id}': {old_status} → retired")


def cmd_status():
    """Dashboard view of all auto-skills."""
    state = _load_state()
    skills = state.get("skills", {})

    if not skills:
        print("📊 Auto Skill Pipeline — Empty")
        print("   No auto-skills created yet.")
        print("   Use: ghost_auto_skill.py create '<name>' '<task_log>'")
        return

    counts = {}
    for s in skills.values():
        counts[s["status"]] = counts.get(s["status"], 0) + 1

    total_uses = sum(s["usage"]["count"] for s in skills.values())
    total_successes = sum(s["usage"]["successes"] for s in skills.values())
    overall_rate = total_successes / total_uses if total_uses > 0 else None

    print("📊 Auto Skill Pipeline — Dashboard")
    print(f"   Total skills: {len(skills)}")
    for status, count in sorted(counts.items()):
        emoji = {"draft": "📝", "active": "✅", "retired": "💀"}.get(status, "❓")
        print(f"   {emoji} {status}: {count}")
    print(f"   Total uses: {total_uses}")
    if overall_rate is not None:
        print(f"   Overall success rate: {overall_rate:.0%}")
    print()

    for sid, skill in sorted(
        skills.items(), key=lambda x: x[1]["usage"]["count"], reverse=True
    ):
        rate = _success_rate(skill)
        rate_str = f"{rate:.0%}" if rate is not None else "n/a"
        emoji = {"draft": "📝", "active": "✅", "retired": "💀"}.get(
            skill["status"], "❓"
        )
        print(
            f"   {emoji} {skill['name']} [{sid}] — "
            f"used {skill['usage']['count']}x, "
            f"success {rate_str}, "
            f"v{skill['version']}"
        )


def cmd_list():
    """List all auto-skills as JSON."""
    state = _load_state()
    skills = state.get("skills", {})

    if not skills:
        print("No auto-skills found.")
        return []

    result = []
    for sid, skill in skills.items():
        rate = _success_rate(skill)
        entry = {
            "id": sid,
            "name": skill["name"],
            "status": skill["status"],
            "uses": skill["usage"]["count"],
            "success_rate": rate,
            "path": skill["skill_path"],
        }
        result.append(entry)
        print(json.dumps(entry, ensure_ascii=False))

    return result


def cmd_cleanup():
    """Remove retired skills' files and clean state."""
    state = _load_state()
    removed = 0
    for sid, skill in list(state["skills"].items()):
        if skill["status"] == "retired":
            skill_path = Path(skill["skill_path"])
            skill_dir = skill_path.parent
            if skill_dir.exists():
                import shutil
                shutil.rmtree(skill_dir)
                print(f"🗑️  Removed {skill_dir}")
            del state["skills"][sid]
            removed += 1

    _save_state(state)
    print(f"Cleaned up {removed} retired skill(s).")


# ─── CLI ─────────────────────────────────────────────────────────────


USAGE = """
Usage: ghost_auto_skill.py <command> [args]

Commands:
  detect  <task_log>                   Check if task is skill-worthy
  create  <name> <task_log> [desc]     Create auto-skill from task
  match   <task_description>           Find matching skill for task
  record  <skill_id> <success|failure> Record usage outcome
  improve <skill_id> <failure_context> Add improvement note
  promote <skill_id>                   Manual promote to active
  retire  <skill_id>                   Manual retire
  status                               Dashboard
  list                                 List all with JSON
  cleanup                              Remove retired skills

Lifecycle: detect → create → [match → use → record] → auto-promote/retire
Thresholds: promote at 3 successes ≥90% | retire at <50% after 3 uses
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "detect":
        if len(sys.argv) < 3:
            print("Usage: ghost_auto_skill.py detect '<task_log>'")
            sys.exit(1)
        cmd_detect(sys.argv[2])

    elif cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: ghost_auto_skill.py create '<name>' '<task_log>' [description]")
            sys.exit(1)
        desc = sys.argv[4] if len(sys.argv) > 4 else None
        cmd_create(sys.argv[2], sys.argv[3], desc)

    elif cmd == "match":
        if len(sys.argv) < 3:
            print("Usage: ghost_auto_skill.py match '<task_description>'")
            sys.exit(1)
        cmd_match(sys.argv[2])

    elif cmd == "record":
        if len(sys.argv) < 4:
            print("Usage: ghost_auto_skill.py record <skill_id> <success|failure>")
            sys.exit(1)
        cmd_record(sys.argv[2], sys.argv[3])

    elif cmd == "improve":
        if len(sys.argv) < 4:
            print("Usage: ghost_auto_skill.py improve <skill_id> '<failure_context>'")
            sys.exit(1)
        cmd_improve(sys.argv[2], sys.argv[3])

    elif cmd == "promote":
        if len(sys.argv) < 3:
            print("Usage: ghost_auto_skill.py promote <skill_id>")
            sys.exit(1)
        cmd_promote(sys.argv[2])

    elif cmd == "retire":
        if len(sys.argv) < 3:
            print("Usage: ghost_auto_skill.py retire <skill_id>")
            sys.exit(1)
        cmd_retire(sys.argv[2])

    elif cmd == "status":
        cmd_status()

    elif cmd == "list":
        cmd_list()

    elif cmd == "cleanup":
        cmd_cleanup()

    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
