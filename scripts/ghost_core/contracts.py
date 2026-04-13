from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SOURCE_LABELS = {
    "memory": "Structured Memory",
    "daily": "Daily Notes",
    "learnings": "Learnings",
    "conversation": "Conversations",
}


SCHEMA_RECALL = "ghost-recall/v1"
SCHEMA_LEARNING = "ghost-learning-loop/v1"
SCHEMA_CAPTURE = "ghost-capture/v1"
SCHEMA_SESSION = "ghost-session-context/v1"
SCHEMA_CONVERSATION = "ghost-conversations/v1"
SCHEMA_GUARDRAILS = "ghost-guardrails/v1"
SCHEMA_MEMORY_SYNC = "ghost-memory-sync/v1"
SCHEMA_EVAL = "ghost-eval/v1"
SCHEMA_TRAJECTORY = "ghost-trajectory/v1"
SCHEMA_REGRESSION = "ghost-regression/v1"
SCHEMA_SAFETY = "ghost-safety-benchmark/v1"
SCHEMA_DASHBOARD = "ghost-dashboard/v1"
SCHEMA_EXPERIMENT = "ghost-experiment/v1"


def confidence_from_score(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def build_citation(file_path: str, line: int | None = None) -> str:
    if line and line > 0:
        return f"{file_path}#L{line}"
    return file_path


@dataclass
class RecallQuery:
    query: str
    limit: int = 10
    sources: list[str] = field(default_factory=lambda: ["all"])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecallEvidence:
    query: str
    item_type: str
    source_bucket: str
    source_label: str
    source_detail: str
    file: str
    line: int
    citation: str
    score: float
    confidence: str
    snippet: str
    date: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    source_labels: list[str] = field(default_factory=list)
    id: str = ""
    title: str = ""
    status: str = ""
    match: str = ""
    distance: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RecallHit = RecallEvidence


@dataclass
class RecallReport:
    query: str
    generated_at: str
    total_results: int
    grouped_counts: dict[str, int]
    strongest_signal: str
    recommendations: list[str]
    results: list[dict[str, Any]]
    schema_version: str = SCHEMA_RECALL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaptureRequest:
    content: str
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaptureResult:
    type: str
    path: str
    added: bool
    duplicate: bool = False
    message: str = ""
    tags: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_CAPTURE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserModelSignal:
    signal_type: str
    data: str
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningReflectionRequest:
    task_summary: str
    outcome: str
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningReflectionResult:
    captured: bool
    entries: list[dict[str, Any]] = field(default_factory=list)
    proposed_skill: str | None = None
    schema_version: str = SCHEMA_LEARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningStatusSnapshot:
    total_learnings: int
    by_state: dict[str, int]
    due_for_review: int
    last_captured: str | None
    skill_candidates_pending: int
    skill_improvements_pending: int
    validated_total: int
    promoted_total: int
    recent_captures_7d: int
    recent_validations_30d: int
    recent_promotions_30d: int
    impact: dict[str, Any] = field(default_factory=dict)
    backlog: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_LEARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningDigest:
    generated_at: str
    window_days: int
    total_learnings: int
    due_for_review: int
    validated_total: int
    promoted_total: int
    recent_captures: int
    recent_validations: int
    recent_promotions: int
    skill_candidates_pending: int
    skill_improvements_pending: int
    recommended_actions: list[str]
    schema_version: str = SCHEMA_LEARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionContextSnapshot:
    focus: str = ""
    blockers: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    commitments_due: list[str] = field(default_factory=list)
    second_brain_focus: dict[str, Any] = field(default_factory=dict)
    guardrails: dict[str, Any] = field(default_factory=dict)
    memory_sync: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_SESSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalCase:
    id: str
    suite: str
    category: str
    phase: str
    description: str
    tags: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalRunRequest:
    suite: str
    case: str | None = None
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalCaseResult:
    suite: str
    task_id: str
    category: str
    phase: str
    description: str
    passed: bool
    score: float
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalRunReport:
    suite: str
    phase: str
    run_id: str
    generated_at: str
    task_count: int
    passed_tasks: int
    failed_tasks: int
    score_pct: float
    pass_rate_pct: float
    failed_task_ids: list[str]
    results: list[dict[str, Any]]
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrajectoryEvent:
    run_id: str
    event_type: str
    generated_at: str
    suite: str = ""
    task_id: str = ""
    status: str = ""
    score: float | None = None
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_TRAJECTORY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrajectorySummary:
    run_id: str
    generated_at: str
    event_count: int
    event_types: dict[str, int]
    suites: dict[str, int]
    task_ids: dict[str, int]
    status_counts: dict[str, int]
    schema_version: str = SCHEMA_TRAJECTORY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RegressionDiff:
    task_id: str
    baseline_score: float
    current_score: float
    delta_score: float
    status: str
    schema_version: str = SCHEMA_REGRESSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RegressionReport:
    suite: str
    baseline_id: str
    current_run_id: str
    baseline_score_pct: float
    current_score_pct: float
    delta_score_pct: float
    baseline_pass_rate_pct: float
    current_pass_rate_pct: float
    delta_pass_rate_pct: float
    regressed_tasks: list[str]
    improved_tasks: list[str]
    status: str
    generated_at: str
    diffs: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = SCHEMA_REGRESSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyBenchmarkReport:
    suite: str
    generated_at: str
    task_count: int
    passed_tasks: int
    failed_tasks: int
    score_pct: float
    failed_task_ids: list[str]
    results: list[dict[str, Any]]
    schema_version: str = SCHEMA_SAFETY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContinuityCase:
    id: str
    description: str
    expected_signals: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContinuityResult:
    run_id: str
    task_id: str
    passed: bool
    signals_found: list[str] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContinuityReport:
    suite: str
    generated_at: str
    run_count: int
    avg_score_pct: float
    latest_run_id: str = ""
    results: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = SCHEMA_EVAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentRun:
    name: str
    run_id: str
    generated_at: str
    status: str
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    schema_version: str = SCHEMA_EXPERIMENT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardSnapshot:
    generated_at: str
    window_days: int
    suite_runs: int
    manual_outcomes: int
    suite_summary: dict[str, Any] = field(default_factory=dict)
    phase_breakdown: dict[str, int] = field(default_factory=dict)
    top_failing_tasks: list[dict[str, Any]] = field(default_factory=list)
    manual_status_counts: dict[str, int] = field(default_factory=dict)
    models_seen: dict[str, int] = field(default_factory=dict)
    tracked_suites: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    experiments: dict[str, Any] = field(default_factory=dict)
    memory_signals: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    second_brain: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_DASHBOARD

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
