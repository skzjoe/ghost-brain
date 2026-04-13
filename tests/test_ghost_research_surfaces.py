#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "scripts"


def _run(script: str, *args: str, timeout: int = 30):
    return subprocess.run([sys.executable, str(ROOT / script), *args], capture_output=True, text=True, timeout=timeout)


def test_ghost_eval_list_and_run_json():
    listed = _run("ghost_eval.py", "list", "ghostlite", "--json")
    assert listed.returncode == 0
    list_payload = json.loads(listed.stdout)
    assert list_payload["suite"] == "ghostlite"
    assert any(item["id"] == "capture_decision" for item in list_payload["cases"])

    run = _run("ghost_eval.py", "run", "ghostlite", "--case", "capture_decision", "--json")
    assert run.returncode == 0
    run_payload = json.loads(run.stdout)
    assert run_payload["suite"] == "ghostlite"
    assert run_payload["task_count"] == 1


def test_ghost_safety_benchmark_and_dashboard_json():
    safety = _run("ghost_safety_benchmark.py", "run", "--json")
    assert safety.returncode == 0
    safety_payload = json.loads(safety.stdout)
    assert safety_payload["suite"] == "safety"

    dashboard = _run("ghost_dashboard.py", "summary", "--json")
    assert dashboard.returncode == 0
    dashboard_payload = json.loads(dashboard.stdout)
    assert dashboard_payload["schema_version"] == "ghost-dashboard/v1"

    focus = _run("ghost_dashboard.py", "focus", "--json")
    assert focus.returncode == 0
    focus_payload = json.loads(focus.stdout)
    assert "recommendations" in focus_payload


def test_ghost_regression_and_continuity_json():
    baseline = _run("ghost_regression.py", "baseline", "ghostlite", "--json")
    assert baseline.returncode == 0
    baseline_payload = json.loads(baseline.stdout)
    assert baseline_payload["suite"] == "ghostlite"

    compare = _run("ghost_regression.py", "compare", "ghostlite", "--run-now", "--json", timeout=60)
    assert compare.returncode == 0
    compare_payload = json.loads(compare.stdout)
    assert compare_payload["schema_version"] == "ghost-regression/v1"

    continuity = _run("ghost_continuity_benchmark.py", "report", "--json")
    assert continuity.returncode == 0
    continuity_payload = json.loads(continuity.stdout)
    assert continuity_payload["suite"] == "continuity"

    invalid = _run("ghost_regression.py", "compare", "ghostlite", "--baseline-path", "does-not-exist.json", "--json")
    assert invalid.returncode != 0
    assert "Error:" in invalid.stderr


def test_ghost_trajectory_and_experiments_json():
    appended = _run(
        "ghost_trajectory_log.py",
        "append",
        "run-test-trajectory",
        "--event",
        "manual_outcome",
        "--suite",
        "manual",
        "--task",
        "proposal-review",
        "--status",
        "success",
        "--score",
        "1.0",
        "--json",
    )
    assert appended.returncode == 0
    append_payload = json.loads(appended.stdout)
    assert append_payload["run_id"] == "run-test-trajectory"

    summary = _run("ghost_trajectory_log.py", "summary", "run-test-trajectory", "--json")
    assert summary.returncode == 0
    summary_payload = json.loads(summary.stdout)
    assert summary_payload["event_count"] >= 1

    invalid_append = _run("ghost_trajectory_log.py", "append", "run-test-trajectory", "--event", "manual_outcome", "--data", "{bad", "--json")
    assert invalid_append.returncode != 0
    assert "Error:" in invalid_append.stderr

    add = _run("ghost_experiments.py", "add", "phase2-registry-test", "--hypothesis", "Registry tracks experiment runs", "--json")
    if add.returncode != 0:
        assert "already exists" in add.stderr
    run = _run("ghost_experiments.py", "run", "phase2-registry-test", "--metric", "score_pct=95", "--json")
    assert run.returncode == 0
    run_payload = json.loads(run.stdout)
    assert run_payload["name"] == "phase2-registry-test"

    show = _run("ghost_experiments.py", "show", "--json")
    assert show.returncode == 0
    show_payload = json.loads(show.stdout)
    assert any(item["name"] == "phase2-registry-test" for item in show_payload["experiments"])
