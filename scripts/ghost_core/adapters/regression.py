from __future__ import annotations

from typing import Any, Callable


class RegressionAdapter:
    def __init__(self, baseline_fn: Callable[..., dict[str, Any]] | None = None, report_fn: Callable[..., dict[str, Any]] | None = None, compare_runs_fn: Callable[[str, str], dict[str, Any]] | None = None):
        self._baseline_fn = baseline_fn
        self._report_fn = report_fn
        self._compare_runs_fn = compare_runs_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def save_baseline(self, suite: str, run_id: str | None = None) -> dict[str, Any]:
        fn = self._baseline_fn or self._module().save_baseline
        return fn(suite, run_id=run_id)

    def report(self, suite: str, run_now: bool = False, baseline_path: str | None = None) -> dict[str, Any]:
        fn = self._report_fn or self._module().regression_report
        return fn(suite, run_now=run_now, baseline_path=baseline_path)

    def compare_runs(self, run_a: str, run_b: str) -> dict[str, Any]:
        fn = self._compare_runs_fn or self._module().compare_runs
        return fn(run_a, run_b)
