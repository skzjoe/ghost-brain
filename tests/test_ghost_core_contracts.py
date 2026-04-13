#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_core.contracts import (
    DashboardSnapshot,
    EvalCaseResult,
    ExperimentRun,
    LearningStatusSnapshot,
    RecallEvidence,
    RecallQuery,
    RegressionDiff,
    TrajectoryEvent,
    build_citation,
    confidence_from_score,
)
from ghost_core.workspace import get_workspace_paths


def test_confidence_from_score_bands():
    assert confidence_from_score(0.9) == "high"
    assert confidence_from_score(0.6) == "medium"
    assert confidence_from_score(0.1) == "low"


def test_build_citation_with_line():
    assert build_citation("memory/decisions.md", 12) == "memory/decisions.md#L12"


def test_recall_evidence_serializes():
    item = RecallEvidence(
        query="erpnext",
        item_type="decision",
        source_bucket="memory",
        source_label="Structured Memory",
        source_detail="db:fts",
        file="memory/decisions.md",
        line=0,
        citation="memory/decisions.md",
        score=0.8,
        confidence="medium",
        snippet="Decided ERPNext",
    )
    payload = item.to_dict()
    assert payload["query"] == "erpnext"
    assert payload["source_label"] == "Structured Memory"


def test_workspace_paths_resolution(tmp_path):
    paths = get_workspace_paths(tmp_path)
    assert paths.workspace == tmp_path
    assert paths.memory_dir == tmp_path / "memory"
    assert paths.user_model_path == tmp_path / "memory" / "user-model.md"


def test_workspace_paths_resolution_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCLAW_WORKSPACE", str(tmp_path))
    paths = get_workspace_paths()
    assert paths.workspace == tmp_path


def test_recall_query_defaults():
    query = RecallQuery(query="erpnext")
    assert query.limit == 10
    assert query.sources == ["all"]


def test_learning_status_snapshot_serializes():
    snapshot = LearningStatusSnapshot(
        total_learnings=1,
        by_state={"observed": 1},
        due_for_review=1,
        last_captured="2026-04-12T11:00:00",
        skill_candidates_pending=0,
        skill_improvements_pending=0,
        validated_total=0,
        promoted_total=0,
        recent_captures_7d=1,
        recent_validations_30d=0,
        recent_promotions_30d=0,
    )
    payload = snapshot.to_dict()
    assert payload["schema_version"] == "ghost-learning-loop/v1"


def test_research_contracts_serialize():
    case_result = EvalCaseResult(
        suite="ghostlite",
        task_id="capture_decision",
        category="capture",
        phase="phase1",
        description="Decision capture routes correctly",
        passed=True,
        score=1.0,
        summary="ok",
    )
    event = TrajectoryEvent(run_id="run-123", event_type="task_result", generated_at="2026-04-13T00:00:00Z")
    diff = RegressionDiff(task_id="capture_decision", baseline_score=1.0, current_score=0.0, delta_score=-1.0, status="regressed")
    experiment = ExperimentRun(name="phase2-context-bridge", run_id="exp-1", generated_at="2026-04-13T00:00:00Z", status="success", metrics={"score_pct": 90})
    dashboard = DashboardSnapshot(generated_at="2026-04-13T00:00:00Z", window_days=14, suite_runs=1, manual_outcomes=0)

    assert case_result.to_dict()["schema_version"] == "ghost-eval/v1"
    assert event.to_dict()["schema_version"] == "ghost-trajectory/v1"
    assert diff.to_dict()["schema_version"] == "ghost-regression/v1"
    assert experiment.to_dict()["schema_version"] == "ghost-experiment/v1"
    assert dashboard.to_dict()["schema_version"] == "ghost-dashboard/v1"
