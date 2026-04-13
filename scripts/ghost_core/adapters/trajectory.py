from __future__ import annotations

from typing import Any, Callable


class TrajectoryAdapter:
    def __init__(self, append_fn: Callable[..., dict[str, Any]] | None = None, summary_fn: Callable[[str], dict[str, Any]] | None = None):
        self._append_fn = append_fn
        self._summary_fn = summary_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def append(self, **payload: Any) -> dict[str, Any]:
        fn = self._append_fn or self._module().append_trajectory_event
        return fn(**payload)

    def summary(self, run_id: str) -> dict[str, Any]:
        fn = self._summary_fn or self._module().trajectory_summary
        return fn(run_id)
