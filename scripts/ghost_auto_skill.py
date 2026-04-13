#!/usr/bin/env python3
"""
ghost_auto_skill.py — Auto Skill Creation + Self-Validation Pipeline

Immune system for Ghost Brain: create skills from experience,
validate through real usage, self-improve on failure, retire what doesn't work.

Zero review burden — the user sees a dashboard, not an approval queue.

Lifecycle:
  detect  → is this task skill-worthy?
  create  → generate skill draft in skills/.auto/
  match   → find matching auto-skill for incoming task
  record  → track success/failure from real usage
  improve → revise skill based on failure context
  promote → graduate to skills/ (manual or auto at threshold)
  retire  → deactivate underperforming skills
  status  → dashboard view
  list    → list all auto-skills with stats

State: .local/auto_skills.json
Skills: skills/.auto/<name>/SKILL.md

Auto-promote: 3+ successes, 0 failures, success_rate >= 90%
Auto-retire: 3+ uses, success_rate < 50%
"""

import json
import os
import sys
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from ghost_core.workspace import get_workspace_paths

# Paths
_workspace_hint = os.environ.get("GHOST_WORKSPACE") or os.environ.get("OPENCLAW_WORKSPACE")
_paths = get_workspace_paths(_workspace_hint)
WORKSPACE = _paths.workspace
STATE_FILE = _paths.local_dir / "auto_skills.json"
SKILLS_AUTO_DIR = _paths.skills_dir / ".auto"
SKILLS_DIR = _paths.skills_dir

# Thresholds
PROMOTE_MIN_SUCCESSES = 3
PROMOTE_MIN_RATE = 0.9
RETIRE_MIN_USES = 3
RETIRE_MAX_RATE = 0.5
MATCH_THRESHOLD = 0.45
WEAK_MATCH_THRESHOLD = 0.25


def _load_state():
    """Load auto-skills state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"skills": {}, "version": 1}


def _save_state(state):
    """Save auto-skills state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _skill_id(name):
    """Generate a stable skill ID from name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60]


def _extract_keywords(text):
    """Extract meaningful keywords from text for fingerprinting."""
    # Remove common stop words, keep technical terms
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
        "ที่", "ของ", "ใน", "และ", "ไม่", "ได้", "จะ", "ให้", "มี", "เป็น",
        "แล้ว", "ก็", "กับ", "ว่า", "ไป", "มา", "อยู่", "จาก", "ด้วย",
    }
    words = re.findall(r"[a-z0-9_\-\.]+", text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in stop]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:30]  # Cap at 30 keywords


def _keyword_similarity(kw1, kw2):
    """Calculate Jaccard similarity between two keyword lists."""
    if not kw1 or not kw2:
        return 0.0
    s1, s2 = set(kw1), set(kw2)
    intersection = s1 & s2
    union = s1 | s2
    return len(intersection) / len(union) if union else 0.0


def _coverage_score(source_keywords, target_keywords):
    if not source_keywords or not target_keywords:
        return 0.0
    source_set = set(source_keywords)
    target_set = set(target_keywords)
    return len(source_set & target_set) / len(source_set)


def _phrase_bonus(task_description, skill_name, overlap):
    lowered_task = task_description.lower()
    lowered_name = skill_name.lower()
    if lowered_name and lowered_name in lowered_task:
        return 0.15
    if len(overlap) >= 3:
        return 0.1
    if len(overlap) == 2:
        return 0.05
    return 0.0


def _usage_bonus(skill):
    rate = _success_rate(skill)
    if rate is None or skill["usage"]["count"] < 2:
        return 0.0
    return min(0.08, rate * 0.08)


def _match_score(task_description, task_kw, skill):
    skill_kw = skill["fingerprint"].get("keywords", [])
    overlap = sorted(set(task_kw) & set(skill_kw))
    keyword_similarity = _keyword_similarity(task_kw, skill_kw)
    task_coverage = _coverage_score(task_kw, skill_kw)
    skill_coverage = _coverage_score(skill_kw, task_kw)
    phrase_bonus = _phrase_bonus(task_description, skill["name"], overlap)
    usage_bonus = _usage_bonus(skill)
    score = (
        (task_coverage * 0.5)
        + (skill_coverage * 0.2)
        + (keyword_similarity * 0.2)
        + phrase_bonus
        + usage_bonus
    )
    reasons = []
    if overlap:
        reasons.append(f"shared keywords: {', '.join(overlap[:5])}")
    if phrase_bonus >= 0.1:
        reasons.append("strong phrase/name match")
    if usage_bonus > 0:
        reasons.append("boosted by prior successful usage")
    return {
        "score": round(min(score, 0.99), 3),
        "keyword_similarity": round(keyword_similarity, 3),
        "task_coverage": round(task_coverage, 3),
        "skill_coverage": round(skill_coverage, 3),
        "overlap": overlap,
        "reasons": reasons,
    }


def _match_confidence(score):
    if score >= 0.7:
        return "high"
    if score >= MATCH_THRESHOLD:
        return "medium"
    if score >= WEAK_MATCH_THRESHOLD:
        return "low"
    return "none"


def _now_iso():
    """Current time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Commands ────────────────────────────────────────────────────────


def cmd_detect(task_log):
    """
    Analyze a task log to determine if it's skill-worthy.
    Returns a fingerprint + recommendation.

    Criteria for skill-worthiness:
    - Multi-step (3+ distinct actions/tools)
    - Repeatable pattern (not one-off data)
    - Has clear input → output structure
    """
    keywords = _extract_keywords(task_log)
    lines = task_log.strip().split("\n")

    # Heuristics for skill-worthiness
    signals = {
        "multi_step": len(lines) >= 3 or len(keywords) >= 5,
        "has_tools": any(
            t in task_log.lower()
            for t in [
                "exec", "write", "read", "browser", "fetch", "search",
                "python", "script", "api", "curl", "git", "npm",
                "gog", "mcporter", "claude", "spawn",
            ]
        ),
        "has_structure": any(
            s in task_log.lower()
            for s in [
                "step", "then", "next", "first", "finally", "→", "->",
                "ขั้นตอน", "แล้ว", "จากนั้น", "สุดท้าย",
            ]
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
    """
    Create an auto-skill from a task log.
    Generates SKILL.md in skills/.auto/<name>/
    """
    state = _load_state()
    sid = _skill_id(name)

    if sid in state["skills"] and state["skills"][sid]["status"] != "retired":
        print(f"⚠️  Skill '{sid}' already exists (status: {state['skills'][sid]['status']})")
        return None

    keywords = _extract_keywords(task_log)
    desc = description or f"Auto-generated skill from task: {name}"

    # Create skill directory and SKILL.md
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

    # Register in state
    state["skills"][sid] = {
        "name": name,
        "description": desc,
        "created": _now_iso(),
        "source_task_hash": hashlib.sha256(task_log.encode()).hexdigest()[:16],
        "fingerprint": {
            "keywords": keywords,
        },
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
    """
    Find the best matching auto-skill for a task description.
    Returns strong matches first, with a weak-candidate fallback band.
    """
    state = _load_state()
    task_kw = _extract_keywords(task_description)

    matches = []
    weak_matches = []
    for sid, skill in state["skills"].items():
        if skill["status"] in ("retired",):
            continue
        metrics = _match_score(task_description, task_kw, skill)
        score = metrics["score"]
        candidate = {
            "skill_id": sid,
            "name": skill["name"],
            "similarity": score,
            "keyword_similarity": metrics["keyword_similarity"],
            "task_coverage": metrics["task_coverage"],
            "skill_coverage": metrics["skill_coverage"],
            "confidence": _match_confidence(score),
            "reasons": metrics["reasons"],
            "status": skill["status"],
            "success_rate": _success_rate(skill),
            "usage_count": skill["usage"]["count"],
            "path": skill["skill_path"],
        }
        if score >= MATCH_THRESHOLD:
            matches.append(candidate)
        elif score >= WEAK_MATCH_THRESHOLD:
            weak_matches.append(candidate)

    matches.sort(key=lambda m: m["similarity"], reverse=True)
    weak_matches.sort(key=lambda m: m["similarity"], reverse=True)
    output = matches or weak_matches[:3]

    if output:
        heading = "🎯 Found matching skill(s):" if matches else "🤔 No strong match, but these weak candidates are closest:"
        print(heading)
        for m in output[:5]:
            rate = f"{m['success_rate']:.0%}" if m['success_rate'] is not None else "n/a"
            print(
                f"   [{m['similarity']:.0%}] {m['name']} "
                f"(confidence: {m['confidence']}, status: {m['status']}, used: {m['usage_count']}x, success: {rate})"
            )
            if m["reasons"]:
                print(f"         because {m['reasons'][0]}")
            print(f"         → {m['path']}")
    else:
        print("❌ No matching auto-skill found.")

    return output


def cmd_record(skill_id, outcome):
    """
    Record a usage outcome (success/failure).
    Triggers auto-promote or auto-retire if thresholds met.
    """
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

    # Auto-promote check
    if (
        skill["status"] == "draft"
        and skill["usage"]["successes"] >= PROMOTE_MIN_SUCCESSES
        and rate is not None
        and rate >= PROMOTE_MIN_RATE
    ):
        skill["status"] = "active"
        action = "promoted"
        print(f"🎉 Auto-promoted '{skill_id}' → active (success rate: {rate:.0%})")

    # Auto-retire check
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
    """
    Mark a skill for improvement with failure context.
    Appends failure notes to SKILL.md for LLM to revise.
    """
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return

    skill = state["skills"][skill_id]
    skill_path = Path(skill["skill_path"])

    if not skill_path.exists():
        print(f"❌ Skill file not found: {skill_path}")
        return

    # Append failure context
    improvement_note = f"""

## Improvement Note #{skill['improvements'] + 1} ({_now_iso()})
**Failure context:** {failure_context}
**Action needed:** Revise the procedure above to handle this case.
"""

    with open(skill_path, "a") as f:
        f.write(improvement_note)

    skill["improvements"] += 1
    # Update keywords with failure context
    new_kw = _extract_keywords(failure_context)
    existing = set(skill["fingerprint"]["keywords"])
    for kw in new_kw:
        if kw not in existing:
            skill["fingerprint"]["keywords"].append(kw)
            existing.add(kw)

    _save_state(state)
    print(
        f"🔧 Added improvement note #{skill['improvements']} to '{skill_id}'"
    )
    print(f"   LLM should revise: {skill_path}")
    return True


def cmd_promote(skill_id):
    """Manually promote a skill to active status."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return

    skill = state["skills"][skill_id]
    old_status = skill["status"]
    skill["status"] = "active"
    _save_state(state)
    print(f"✅ Promoted '{skill_id}': {old_status} → active")


def cmd_retire(skill_id):
    """Manually retire a skill."""
    state = _load_state()
    if skill_id not in state["skills"]:
        print(f"❌ Skill '{skill_id}' not found")
        return

    skill = state["skills"][skill_id]
    old_status = skill["status"]
    skill["status"] = "retired"
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

    # Count by status
    counts = {}
    for s in skills.values():
        counts[s["status"]] = counts.get(s["status"], 0) + 1

    total_uses = sum(s["usage"]["count"] for s in skills.values())
    total_successes = sum(s["usage"]["successes"] for s in skills.values())
    overall_rate = (
        total_successes / total_uses if total_uses > 0 else None
    )

    print("📊 Auto Skill Pipeline — Dashboard")
    print(f"   Total skills: {len(skills)}")
    for status, count in sorted(counts.items()):
        emoji = {"draft": "📝", "active": "✅", "retired": "💀"}.get(status, "❓")
        print(f"   {emoji} {status}: {count}")
    print(f"   Total uses: {total_uses}")
    if overall_rate is not None:
        print(f"   Overall success rate: {overall_rate:.0%}")
    print()

    # List skills
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
    """List all auto-skills with basic info."""
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


# ─── Helpers ─────────────────────────────────────────────────────────


def _success_rate(skill):
    """Calculate success rate, None if no uses."""
    total = skill["usage"]["count"]
    if total == 0:
        return None
    return skill["usage"]["successes"] / total


# ─── CLI ─────────────────────────────────────────────────────────────


USAGE = """
Usage: ghost_auto_skill.py <command> [args]

Commands:
  detect  <task_log>                  Check if task is skill-worthy
  create  <name> <task_log> [desc]    Create auto-skill from task
  match   <task_description>          Find matching skill for task
  record  <skill_id> <success|failure> Record usage outcome
  improve <skill_id> <failure_context> Add improvement note
  promote <skill_id>                  Manual promote to active
  retire  <skill_id>                  Manual retire
  status                              Dashboard
  list                                List all with JSON
  cleanup                             Remove retired skills

Lifecycle: detect → create → [match → use → record] → auto-promote/retire
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
