#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_cli import _build_parser


CLI = Path(__file__).parent.parent / "scripts" / "ghost_cli.py"


def test_parser_recall_search_json():
    parser = _build_parser()
    args = parser.parse_args(["recall", "search", "erpnext", "--json"])
    related = parser.parse_args(["recall", "related", "erpnext", "--json"])
    assert args.command == "recall"
    assert args.recall_command == "search"
    assert args.json is True
    assert related.recall_command == "related"


def test_parser_learning_status_json():
    parser = _build_parser()
    args = parser.parse_args(["learning", "status", "--json"])
    assert args.command == "learning"
    assert args.learning_command == "status"
    assert args.json is True


def test_parser_context_show_json():
    parser = _build_parser()
    args = parser.parse_args(["context", "show", "--json"])
    assert args.command == "context"
    assert args.context_command == "show"
    assert args.json is True


def test_parser_capture_json():
    parser = _build_parser()
    args = parser.parse_args(["capture", "test note", "--json"])
    brief = parser.parse_args(["brief", "--json"])
    followups = parser.parse_args(["followups", "due", "--json"])
    assert args.command == "capture"
    assert args.json is True
    assert brief.command == "brief"
    assert followups.command == "followups"
    assert followups.followups_command == "due"


def test_parser_research_run_and_list_json():
    parser = _build_parser()
    run_args = parser.parse_args(["research", "run", "ghostlite", "--case", "capture_decision", "--json"])
    list_args = parser.parse_args(["research", "list", "--json"])
    assert run_args.command == "research"
    assert run_args.research_command == "run"
    assert run_args.case == "capture_decision"
    assert run_args.json is True
    assert list_args.research_command == "list"
    assert list_args.json is True


def test_parser_research_experiments_json():
    parser = _build_parser()
    args = parser.parse_args(["research", "experiments", "phase2-context-bridge", "baseline", "--json"])
    focus = parser.parse_args(["research", "focus", "--json"])
    assert args.command == "research"
    assert args.research_command == "experiments"
    assert args.name == "phase2-context-bridge"
    assert args.against == "baseline"
    assert focus.research_command == "focus"


def test_cli_learning_status_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "learning", "status", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-learning-loop/v1"
    assert payload["command"] == "status"


def test_cli_context_show_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "context", "show", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-session-context/v1"
    assert "focus" in payload
    assert "second_brain_focus" in payload


def test_cli_capture_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "capture", "We decided to use PostgreSQL", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["type"] == "decision"
    assert "path" in payload
    assert "PostgreSQL" in payload.get("tags", [])


def test_cli_recall_report_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "recall", "report", "ghost", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-recall/v1"
    assert "results" in payload


def test_cli_recall_related_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "recall", "related", "ghost", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-recall/v1"
    assert payload["mode"] == "related"
    assert "related" in payload


def test_cli_research_dashboard_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "research", "dashboard", "--json"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-dashboard/v1"
    assert "suite_summary" in payload


def test_cli_research_focus_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "research", "focus", "--json"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-dashboard/v1"
    assert "recommendations" in payload



def test_cli_research_list_json():
    result = subprocess.run(
        [sys.executable, str(CLI), "research", "list", "--json"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-eval/v1"
    assert any(item["suite"] == "ghostlite" for item in payload["suites"])



def test_cli_research_invalid_metadata_json_error():
    result = subprocess.run(
        [sys.executable, str(CLI), "research", "track-outcome", "manual", "proposal-review", "success", "--metadata-json", "{bad", "--json"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr
