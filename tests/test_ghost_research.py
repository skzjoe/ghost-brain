#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_research import build_dashboard, build_focus_report, log_manual_outcome, regression_report, run_suite, save_baseline, show_run
from ghost_research_lib import add_experiment, compare_runs, continuity_report, run_experiment, safety_report, trajectory_summary


SCRIPT = Path(__file__).parent.parent / "scripts" / "ghost_research.py"


def test_run_ghostlite_suite():
    report = run_suite("ghostlite")
    assert report["schema_version"] == "ghost-eval/v1"
    assert report["suite"] == "ghostlite"
    assert report["task_count"] >= 5
    assert "results" in report


def test_run_case_filter_and_show_run():
    report = run_suite("continuity", case="continuity_duplicate_guard")
    saved = show_run(report["run_id"])
    assert report["task_count"] == 1
    assert saved["run_id"] == report["run_id"]
    assert saved["results"][0]["task_id"] == "continuity_duplicate_guard"


def test_run_continuity_suite_and_compare_runs():
    baseline = run_suite("continuity")
    current = run_suite("continuity")
    comparison = compare_runs(baseline["run_id"], current["run_id"])
    assert comparison["suite"] == "continuity"
    assert comparison["schema_version"] == "ghost-regression/v1"
    assert comparison["status"] in {"pass", "improved", "regression"}


def test_baseline_and_regression_cycle():
    report = run_suite("safety")
    baseline = save_baseline("safety", run_id=report["run_id"])
    assert baseline["suite"] == "safety"
    regression = regression_report("safety")
    assert regression["suite"] == "safety"
    assert regression["schema_version"] == "ghost-regression/v1"
    assert regression["status"] in {"pass", "improved", "regression"}


def test_dashboard_includes_manual_outcomes_experiments_and_reports():
    log_manual_outcome(
        suite="manual",
        task="proposal-review",
        status="success",
        score=1.0,
        notes="client-ready",
        model="gpt-5.4",
        metadata={"phase": "phase2"},
    )
    log_manual_outcome(
        suite="continuity",
        task="missed-deadline-context",
        status="failure",
        score=0.0,
        notes="forgot deadline",
        model="gpt-5.4",
        metadata={"phase": "phase2"},
    )
    experiment_name = "phase2-context-bridge"
    try:
        add_experiment(experiment_name, "Context bridge should reduce recall misses", tags=["phase2"])
    except ValueError:
        pass
    run_experiment(experiment_name, {"score_pct": 92.5, "misses": 1}, notes="baseline capture")
    dashboard = build_dashboard(days=30)
    focus = build_focus_report(days=30)
    continuity = continuity_report(days=30)
    safety = safety_report(days=30)
    assert dashboard["schema_version"] == "ghost-dashboard/v1"
    assert dashboard["manual_outcomes"] >= 2
    assert dashboard["models_seen"].get("gpt-5.4", 0) >= 1
    assert "experiments" in dashboard and "experiments" in dashboard["experiments"]
    assert "recommendations" in dashboard
    assert "second_brain" in dashboard
    assert "memory_signals" in dashboard
    assert dashboard["second_brain"]["capture_candidates"]
    assert focus["schema_version"] == "ghost-dashboard/v1"
    assert "recommendations" in focus
    assert "memory_signals" in focus
    assert continuity["schema_version"] == "ghost-eval/v1"
    assert safety["schema_version"] == "ghost-safety-benchmark/v1"


def test_trajectory_summary_after_run():
    report = run_suite("ghostlite", case="model_router_simple")
    summary = trajectory_summary(report["run_id"])
    assert summary["schema_version"] == "ghost-trajectory/v1"
    assert summary["event_count"] >= 1
    assert summary["task_ids"]["model_router_simple"] >= 1


def test_cli_run_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "run", "ghostlite", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["suite"] == "ghostlite"
    assert payload["schema_version"] == "ghost-eval/v1"


def test_cli_dashboard_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "dashboard", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "ghost-dashboard/v1"
    assert "suite_summary" in payload


def test_cli_focus_and_invalid_metadata_json():
    focus = subprocess.run(
        [sys.executable, str(SCRIPT), "focus", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert focus.returncode == 0
    focus_payload = json.loads(focus.stdout)
    assert focus_payload["schema_version"] == "ghost-dashboard/v1"
    assert "recommendations" in focus_payload

    invalid = subprocess.run(
        [sys.executable, str(SCRIPT), "track", "outcome", "manual", "proposal-review", "success", "--metadata-json", "{bad", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert invalid.returncode != 0
    assert "Error:" in invalid.stderr


def test_regression_invalid_baseline_path_returns_clean_error(tmp_path):
    run_suite("ghostlite")
    bad = tmp_path / "bad-baseline.json"
    bad.write_text("{not json", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "regression", "ghostlite", "--baseline-path", str(bad), "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "Error:" in result.stderr
