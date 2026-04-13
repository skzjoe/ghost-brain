from __future__ import annotations

from typing import Any, Callable

from ..contracts import CaptureRequest, CaptureResult, RecallQuery, RecallReport, UserModelSignal


class UnifiedRecallAdapter:
    def __init__(
        self,
        recall_report_fn: Callable[..., dict[str, Any]] | None = None,
        capture_fn: Callable[..., dict[str, Any]] | None = None,
        get_user_model_fn: Callable[[], dict[str, Any]] | None = None,
        update_user_model_fn: Callable[[str, str], None] | None = None,
    ):
        self._recall_report_fn = recall_report_fn
        self._capture_fn = capture_fn
        self._get_user_model_fn = get_user_model_fn
        self._update_user_model_fn = update_user_model_fn

    def _module(self):
        import ghost_unified_recall

        return ghost_unified_recall

    def recall(self, request: RecallQuery) -> RecallReport:
        fn = self._recall_report_fn or self._module().build_recall_report
        report = fn(request.query, limit=request.limit, sources=request.sources)
        return RecallReport(**report)

    def capture(self, request: CaptureRequest) -> CaptureResult:
        fn = self._capture_fn or self._module().smart_capture
        payload = fn(request.content, context=request.context)
        return CaptureResult(
            type=payload.get("type", "note"),
            path=payload.get("path", payload.get("file", "")),
            added=bool(payload.get("added", not payload.get("duplicate_warning"))),
            duplicate=bool(payload.get("duplicate", bool(payload.get("duplicate_warning")))),
            message=payload.get("message", payload.get("duplicate_warning", "")),
            tags=list(payload.get("tags", [])),
        )

    def get_user_model(self) -> dict[str, Any]:
        fn = self._get_user_model_fn or self._module().get_user_model
        return fn()

    def update_user_model(self, signal: UserModelSignal) -> None:
        fn = self._update_user_model_fn or self._module().update_user_model
        fn(signal.signal_type, signal.data)
