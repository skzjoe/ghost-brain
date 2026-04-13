#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_working_memory import build_brief, followups_due, recent_decisions

CLI = Path(__file__).parent.parent / "scripts" / "ghost_cli.py"


def _seed_workspace(root: Path) -> None:
    (root / "memory").mkdir(parents=True, exist_ok=True)
    (root / "ACTIVE_WORK.md").write_text(
        "## Current Workstreams\n\n"
        "### Ghost Brain\n"
        "- **Status:** Active productization stream\n"
        "- **Focus:** ship second-brain daily surfaces\n\n"
        "## If Idle, Pull Next\n"
        "- Review stale follow-ups\n"
        "- Improve recall UX\n\n"
        "## Current Blockers / Watchlist\n"
        "- Project Atlas blocked / deadline risk\n",
        encoding="utf-8",
    )
    (root / "memory" / "commitments.md").write_text(
        "| 2026-04-10 | User | Project Atlas | Deadline: 2026-04-16 |\n",
        encoding="utf-8",
    )
    (root / "memory" / "decisions.md").write_text(
        "# Decision Journal\n\n"
        "[2026-04-13] **Build ghost brief first** — fastest path to working-memory value.\n"
        "[2026-04-12] **Keep research compatibility umbrella** — preserve existing surfaces.\n",
        encoding="utf-8",
    )
    (root / "memory" / "follow-ups.md").write_text(
        "# Follow-up Tracker\n\n"
        "## Active\n"
        "| Item | Owner | Since | Deadline | State | Status |\n"
        "|---|---|---|---|---|---|\n"
        "| Project Atlas — receive client inputs | User | 2026-04-01 | 2026-04-16 | waiting | waiting on client |\n"
        "| LifeOps — set first budget | User | 2026-04-02 | — | waiting | waiting on setup |\n"
        "| Internal cleanup | User | 2026-04-12 | — | active | optional |\n",
        encoding="utf-8",
    )


def test_followups_due_categorizes_and_sorts(tmp_path):
    _seed_workspace(tmp_path)
    payload = followups_due(workspace=tmp_path, limit=10, stale_after_days=7)
    assert payload["schema_version"] == "ghost-followups/v1"
    assert payload["total_active"] == 3
    assert payload["counts"]["due_this_week"] >= 1
    assert payload["counts"]["stale"] >= 1
    assert payload["items"][0]["bucket"] in {"due_this_week", "overdue"}


def test_build_brief_includes_decisions_followups_and_focus(tmp_path):
    _seed_workspace(tmp_path)
    payload = build_brief(workspace=tmp_path, decision_limit=2, followup_limit=2)
    assert payload["schema_version"] == "ghost-brief/v1"
    assert "Ghost Brain: ship second-brain daily surfaces" in payload["focus"]
    assert len(payload["recent_decisions"]) == 2
    assert payload["followups_due"]["items"]
    assert "second_brain_focus" in payload
    assert "guardrails" in payload
    assert "memory_sync" in payload



def test_recent_decisions_reads_latest_entries(tmp_path):
    _seed_workspace(tmp_path)
    decisions = recent_decisions(workspace=tmp_path, limit=1)
    assert len(decisions) == 1
    assert decisions[0]["title"] == "Build ghost brief first"



def test_cli_brief_and_followups_json(tmp_path, monkeypatch):
    _seed_workspace(tmp_path)
    monkeypatch.setenv("OPENCLAW_WORKSPACE", str(tmp_path))

    brief = subprocess.run(
        [sys.executable, str(CLI), "brief", "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert brief.returncode == 0
    brief_payload = json.loads(brief.stdout)
    assert brief_payload["schema_version"] == "ghost-brief/v1"
    assert brief_payload["followups_due"]["items"]
    assert "guardrails" in brief_payload

    followups = subprocess.run(
        [sys.executable, str(CLI), "followups", "due", "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert followups.returncode == 0
    followups_payload = json.loads(followups.stdout)
    assert followups_payload["schema_version"] == "ghost-followups/v1"
    assert followups_payload["items"]
