from __future__ import annotations

from typing import Any, Callable


class SafetyBenchmarkAdapter:
    def __init__(self, run_fn: Callable[[], dict[str, Any]] | None = None, report_fn: Callable[..., dict[str, Any]] | None = None):
        self._run_fn = run_fn
        self._report_fn = report_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def run(self) -> dict[str, Any]:
        if self._run_fn:
            return self._run_fn()
        return self._module().run_suite("safety")

    def report(self, days: int = 30) -> dict[str, Any]:
        fn = self._report_fn or self._module().safety_report
        return fn(days=days)
