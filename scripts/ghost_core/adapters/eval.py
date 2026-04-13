from __future__ import annotations

from typing import Any, Callable


class EvalAdapter:
    def __init__(self, run_fn: Callable[..., dict[str, Any]] | None = None, list_fn: Callable[[], list[dict[str, Any]]] | None = None, show_fn: Callable[[str], dict[str, Any]] | None = None):
        self._run_fn = run_fn
        self._list_fn = list_fn
        self._show_fn = show_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def run(self, suite: str, case: str | None = None) -> dict[str, Any]:
        fn = self._run_fn or self._module().run_suite
        return fn(suite, case=case)

    def list(self) -> list[dict[str, Any]]:
        fn = self._list_fn or self._module().list_suites
        return fn()

    def show_run(self, run_id: str) -> dict[str, Any]:
        fn = self._show_fn or self._module().show_run
        return fn(run_id)
