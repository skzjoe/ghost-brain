#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_core.adapters.continuity_benchmark import ContinuityBenchmarkAdapter
from ghost_core.adapters.eval import EvalAdapter
from ghost_core.adapters.experiments import ExperimentsAdapter
from ghost_core.adapters.learning_loop import LearningLoopAdapter
from ghost_core.adapters.memory_db import MemoryDbAdapter
from ghost_core.adapters.regression import RegressionAdapter
from ghost_core.adapters.safety import SafetyBenchmarkAdapter
from ghost_core.adapters.session_context import SessionContextAdapter
from ghost_core.adapters.trajectory import TrajectoryAdapter
from ghost_core.adapters.unified_recall import UnifiedRecallAdapter
from ghost_core.adapters.usage_dashboard import UsageDashboardAdapter
from ghost_core.contracts import CaptureRequest, LearningReflectionRequest, RecallQuery, UserModelSignal
from ghost_core.defaults import build_default_runtime


class FakeMemoryBackend:
    def __init__(self):
        self.closed = False

    def search_hybrid(self, query, limit):
        return [{"query": query, "limit": limit, "match": "both"}]

    def stats(self):
        return {"items": 12}

    def close(self):
        self.closed = True


def test_memory_db_adapter_search_and_stats():
    backend = FakeMemoryBackend()
    adapter = MemoryDbAdapter(backend_factory=lambda: backend)
    results = adapter.search("erp", limit=3)
    assert results[0]["query"] == "erp"
    assert adapter.stats()["items"] == 12
    assert backend.closed is True


def test_unified_recall_adapter_returns_contracts():
    adapter = UnifiedRecallAdapter(
        recall_report_fn=lambda query, limit, sources: {
            "query": query,
            "generated_at": "2026-04-12T10:00:00",
            "total_results": 1,
            "grouped_counts": {"memory": 1},
            "strongest_signal": "Structured Memory",
            "recommendations": ["Use the decision log"],
            "results": [{"query": query, "snippet": "Decided ERPNext"}],
            "schema_version": "ghost-recall/v1",
        },
        capture_fn=lambda content, context="": {
            "type": "decision",
            "path": "memory/decisions.md",
            "added": True,
            "duplicate": False,
            "message": f"captured:{context}",
        },
        get_user_model_fn=lambda: {"preferences": ["concise"]},
        update_user_model_fn=lambda signal_type, data: None,
    )

    report = adapter.recall(RecallQuery(query="ERPNext", limit=5, sources=["memory"]))
    assert report.query == "ERPNext"
    assert report.total_results == 1

    capture = adapter.capture(CaptureRequest(content="We decided", context="meeting"))
    assert capture.type == "decision"
    assert capture.added is True

    model = adapter.get_user_model()
    assert model["preferences"] == ["concise"]

    adapter.update_user_model(UserModelSignal(signal_type="preference", data="concise"))


def test_learning_loop_adapter_filters_extended_digest_fields():
    adapter = LearningLoopAdapter(
        reflect_fn=lambda task_summary, outcome, errors=None: {
            "captured": True,
            "entries": [{"id": "LRN-1"}],
            "proposed_skill": None,
        },
        status_fn=lambda: {
            "total_learnings": 2,
            "by_state": {"observed": 1, "validated": 1},
            "due_for_review": 1,
            "last_captured": "2026-04-12T11:00:00",
            "skill_candidates_pending": 0,
            "skill_improvements_pending": 1,
            "validated_total": 1,
            "promoted_total": 0,
            "recent_captures_7d": 1,
            "recent_validations_30d": 1,
            "recent_promotions_30d": 0,
            "impact": {"captured_7d": 1},
            "backlog": {"due": 1},
            "recommended_actions": ["Review due learnings"],
        },
        digest_fn=lambda days=30: {
            "generated_at": "2026-04-12T11:00:00",
            "window_days": days,
            "total_learnings": 2,
            "due_for_review": 1,
            "validated_total": 1,
            "promoted_total": 0,
            "recent_captures": 1,
            "recent_validations": 1,
            "recent_promotions": 0,
            "skill_candidates_pending": 0,
            "skill_improvements_pending": 1,
            "recommended_actions": ["Review due learnings"],
            "headline": "extra field should be ignored",
        },
        promote_fn=lambda: [{"id": "LRN-1", "action": "validated"}],
        detect_skill_candidate_fn=lambda task_log: {"name": "deploy-skill"},
        check_skill_fn=lambda skill_name, execution_log, success: {"skill_name": skill_name, "issue": "timeout", "proposed_fix": "retry"},
    )

    reflection = adapter.reflect(LearningReflectionRequest(task_summary="Fix", outcome="Done", errors=[]))
    assert reflection.captured is True

    status = adapter.status()
    assert status.total_learnings == 2
    assert status.skill_improvements_pending == 1

    digest = adapter.digest(days=14)
    assert digest.window_days == 14
    assert digest.recent_validations == 1

    promoted = adapter.promote()
    assert promoted[0]["action"] == "validated"
    assert adapter.detect_skill_candidate("Step 1: Build") == {"name": "deploy-skill"}
    assert adapter.check_skill("deploy-skill", "timeout", False)["issue"] == "timeout"


def test_build_default_runtime(tmp_path):
    runtime = build_default_runtime(str(tmp_path))
    assert runtime.paths.workspace == tmp_path
    assert runtime.paths.memory_dir == tmp_path / "memory"
    assert runtime.recall is not None
    assert runtime.learning is not None
    assert runtime.memory_db is not None
    assert runtime.session_context is not None


def test_session_context_adapter_extracts_focus_and_actions(tmp_path):
    active_work = tmp_path / "ACTIVE_WORK.md"
    active_work.write_text(
        "## Current Workstreams\n\n"
        "### Northstar\n"
        "- **Status:** Active / support phase\n"
        "- **Focus:** reactive bug support only\n\n"
        "### Ghost Brain\n"
        "- **Status:** Active productization stream\n"
        "- **Focus:** production-grade Ghost layer\n\n"
        "## If Idle, Pull Next\n"
        "- Review learnings\n"
        "- Improve recall UX\n\n"
        "## Watchlist\n"
        "- Project Atlas blocked by client input\n",
        encoding="utf-8",
    )
    commitments = tmp_path / "memory" / "commitments.md"
    commitments.parent.mkdir(parents=True, exist_ok=True)
    commitments.write_text("| 2026-03-23 | Contact Lead | Project Atlas | Deadline: 2026-04-16 |\n", encoding="utf-8")

    snapshot = SessionContextAdapter(
        workspace=tmp_path,
        active_work_path=active_work,
        commitments_path=commitments,
    ).snapshot()

    assert "Northstar: reactive bug support only" in snapshot.focus
    assert "Ghost Brain: production-grade Ghost layer" in snapshot.focus
    assert snapshot.next_actions[:2] == ["Review learnings", "Improve recall UX"]
    assert any("blocked" in item.lower() for item in snapshot.blockers)
    assert any("Deadline:" in item for item in snapshot.commitments_due)
    assert isinstance(snapshot.second_brain_focus, dict)


def test_research_adapters_route_calls():
    eval_adapter = EvalAdapter(
        run_fn=lambda suite, case=None: {"suite": suite, "case": case},
        list_fn=lambda: [{"suite": "ghostlite"}],
        show_fn=lambda run_id: {"run_id": run_id},
    )
    regression_adapter = RegressionAdapter(
        baseline_fn=lambda suite, run_id=None: {"suite": suite, "run_id": run_id},
        report_fn=lambda suite, run_now=False, baseline_path=None: {"suite": suite, "run_now": run_now, "baseline_path": baseline_path},
        compare_runs_fn=lambda run_a, run_b: {"run_a": run_a, "run_b": run_b},
    )
    safety_adapter = SafetyBenchmarkAdapter(run_fn=lambda: {"suite": "safety"}, report_fn=lambda days=30: {"days": days})
    continuity_adapter = ContinuityBenchmarkAdapter(run_fn=lambda suite, case=None: {"suite": suite, "case": case}, report_fn=lambda days=30: {"days": days})
    trajectory_adapter = TrajectoryAdapter(append_fn=lambda **payload: payload, summary_fn=lambda run_id: {"run_id": run_id})
    dashboard_adapter = UsageDashboardAdapter(dashboard_fn=lambda days=30: {"days": days, "schema_version": "ghost-dashboard/v1"})
    experiments_adapter = ExperimentsAdapter(
        add_fn=lambda name, hypothesis, tags=None: {"name": name, "hypothesis": hypothesis, "tags": tags or []},
        run_fn=lambda name, metrics, notes="", status="success": {"name": name, "metrics": metrics, "notes": notes, "status": status},
        list_fn=lambda: {"experiments": []},
        compare_fn=lambda name, against="baseline": {"name": name, "against": against},
    )

    assert eval_adapter.run("ghostlite", case="capture_decision") == {"suite": "ghostlite", "case": "capture_decision"}
    assert eval_adapter.list()[0]["suite"] == "ghostlite"
    assert eval_adapter.show_run("run-1")["run_id"] == "run-1"
    assert regression_adapter.save_baseline("ghostlite", run_id="run-1")["run_id"] == "run-1"
    assert regression_adapter.report("ghostlite", run_now=True)["run_now"] is True
    assert regression_adapter.compare_runs("a", "b") == {"run_a": "a", "run_b": "b"}
    assert safety_adapter.run()["suite"] == "safety"
    assert safety_adapter.report(days=7)["days"] == 7
    assert continuity_adapter.run(case="continuity_duplicate_guard")["case"] == "continuity_duplicate_guard"
    assert trajectory_adapter.append(run_id="run-2", event_type="task_result")["run_id"] == "run-2"
    assert trajectory_adapter.summary("run-2")["run_id"] == "run-2"
    assert dashboard_adapter.snapshot(days=14)["days"] == 14
    assert experiments_adapter.add("exp", "hyp") == {"name": "exp", "hypothesis": "hyp", "tags": []}
    assert experiments_adapter.run("exp", {"score": 1})["metrics"]["score"] == 1
    assert experiments_adapter.list() == {"experiments": []}
    assert experiments_adapter.compare("exp", "baseline") == {"name": "exp", "against": "baseline"}
