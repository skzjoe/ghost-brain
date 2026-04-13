from __future__ import annotations

from typing import Any, Callable

from ..contracts import (
    LearningDigest,
    LearningReflectionRequest,
    LearningReflectionResult,
    LearningStatusSnapshot,
)


class LearningLoopAdapter:
    def __init__(
        self,
        reflect_fn: Callable[..., dict[str, Any]] | None = None,
        status_fn: Callable[[], dict[str, Any]] | None = None,
        digest_fn: Callable[..., dict[str, Any]] | None = None,
        promote_fn: Callable[[], list[dict[str, Any]]] | None = None,
        detect_skill_candidate_fn: Callable[[str], dict[str, Any] | None] | None = None,
        check_skill_fn: Callable[[str, str, bool], dict[str, Any] | None] | None = None,
    ):
        self._reflect_fn = reflect_fn
        self._status_fn = status_fn
        self._digest_fn = digest_fn
        self._promote_fn = promote_fn
        self._detect_skill_candidate_fn = detect_skill_candidate_fn
        self._check_skill_fn = check_skill_fn

    def _module(self):
        import ghost_learning_loop

        return ghost_learning_loop

    @staticmethod
    def _pick(payload: dict[str, Any], keys: list[str]) -> dict[str, Any]:
        return {key: payload[key] for key in keys if key in payload}

    def reflect(self, request: LearningReflectionRequest) -> LearningReflectionResult:
        fn = self._reflect_fn or self._module().post_task_reflection
        payload = fn(request.task_summary, request.outcome, request.errors or None)
        return LearningReflectionResult(**payload)

    def status(self) -> LearningStatusSnapshot:
        fn = self._status_fn or self._module().learning_status
        payload = fn()
        return LearningStatusSnapshot(**self._pick(payload, [
            "total_learnings",
            "by_state",
            "due_for_review",
            "last_captured",
            "skill_candidates_pending",
            "skill_improvements_pending",
            "validated_total",
            "promoted_total",
            "recent_captures_7d",
            "recent_validations_30d",
            "recent_promotions_30d",
            "impact",
            "backlog",
            "recommended_actions",
        ]))

    def digest(self, days: int = 30) -> LearningDigest:
        fn = self._digest_fn or self._module().learning_digest
        payload = fn(days=days)
        return LearningDigest(**self._pick(payload, [
            "generated_at",
            "window_days",
            "total_learnings",
            "due_for_review",
            "validated_total",
            "promoted_total",
            "recent_captures",
            "recent_validations",
            "recent_promotions",
            "skill_candidates_pending",
            "skill_improvements_pending",
            "recommended_actions",
            "schema_version",
        ]))

    def promote(self) -> list[dict[str, Any]]:
        fn = self._promote_fn or self._module().auto_promote_learnings
        return fn()

    def detect_skill_candidate(self, task_log: str) -> dict[str, Any] | None:
        fn = self._detect_skill_candidate_fn or self._module().detect_skill_candidate
        return fn(task_log)

    def check_skill(self, skill_name: str, execution_log: str, success: bool = True) -> dict[str, Any] | None:
        fn = self._check_skill_fn or self._module().check_skill_improvement
        return fn(skill_name, execution_log, success)
