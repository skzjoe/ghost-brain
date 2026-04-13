from __future__ import annotations

from typing import Any, Callable


class ContinuityBenchmarkAdapter:
    def __init__(self, run_fn: Callable[..., dict[str, Any]] | None = None, report_fn: Callable[..., dict[str, Any]] | None = None):
        self._run_fn = run_fn
        self._report_fn = report_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def run(self, case: str | None = None) -> dict[str, Any]:
        fn = self._run_fn or self._module().run_suite
        return fn("continuity", case=case)

    def report(self, days: int = 30) -> dict[str, Any]:
        fn = self._report_fn or self._module().continuity_report
        return fn(days=days)
