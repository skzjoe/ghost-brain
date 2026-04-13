#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_session_context import _build_parser
from ghost_core.adapters.session_context import SessionContextAdapter


def test_parser_show_json():
    parser = _build_parser()
    args = parser.parse_args(["show", "--json"])
    assert args.command == "show"
    assert args.json is True


def test_session_context_snapshot_extracts_fields(tmp_path):
    active_work = tmp_path / "ACTIVE_WORK.md"
    active_work.write_text(
        "## Current Workstreams\n\n"
        "### Ghost Brain\n"
        "- **Status:** Active productization stream\n"
        "- **Focus:** harden core interfaces\n\n"
        "## If Idle, Pull Next\n"
        "- Review learnings\n"
        "- Improve proactive signals\n\n"
        "## Current Blockers / Watchlist\n"
        "- Project Atlas blocked / deadline risk\n",
        encoding="utf-8",
    )
    commitments = tmp_path / "memory" / "commitments.md"
    commitments.parent.mkdir(parents=True, exist_ok=True)
    commitments.write_text("| 2026-03-23 | Example Contact | Project Atlas | Deadline: 16 Apr 2569 |\n", encoding="utf-8")

    snapshot = SessionContextAdapter(
        workspace=tmp_path,
        active_work_path=active_work,
        commitments_path=commitments,
    ).snapshot().to_dict()

    assert snapshot["focus"] == "Ghost Brain: harden core interfaces"
    assert snapshot["next_actions"][:2] == ["Review learnings", "Improve proactive signals"]
    assert any("blocked" in item.lower() for item in snapshot["blockers"])
    assert any("Deadline:" in item for item in snapshot["commitments_due"])
    assert "second_brain_focus" in snapshot


def test_cli_show_json(tmp_path, monkeypatch):
    active_work = tmp_path / "ACTIVE_WORK.md"
    active_work.write_text(
        "## Current Workstreams\n\n"
        "### Ghost Brain\n"
        "- **Status:** Active productization stream\n"
        "- **Focus:** harden core interfaces\n",
        encoding="utf-8",
    )
    commitments = tmp_path / "memory" / "commitments.md"
    commitments.parent.mkdir(parents=True, exist_ok=True)
    commitments.write_text("# Commitments\n", encoding="utf-8")

    monkeypatch.setenv("OPENCLAW_WORKSPACE", str(tmp_path))
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "scripts" / "ghost_session_context.py"), "show", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-session-context/v1"
    assert payload["focus"] == "Ghost Brain: harden core interfaces"
    assert "second_brain_focus" in payload
