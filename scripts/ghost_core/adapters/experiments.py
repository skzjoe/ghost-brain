from __future__ import annotations

from typing import Any, Callable


class ExperimentsAdapter:
    def __init__(self, add_fn: Callable[..., dict[str, Any]] | None = None, run_fn: Callable[..., dict[str, Any]] | None = None, list_fn: Callable[[], dict[str, Any]] | None = None, compare_fn: Callable[..., dict[str, Any]] | None = None):
        self._add_fn = add_fn
        self._run_fn = run_fn
        self._list_fn = list_fn
        self._compare_fn = compare_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def add(self, name: str, hypothesis: str, tags: list[str] | None = None) -> dict[str, Any]:
        fn = self._add_fn or self._module().add_experiment
        return fn(name, hypothesis, tags=tags)

    def run(self, name: str, metrics: dict[str, Any], notes: str = "", status: str = "success") -> dict[str, Any]:
        fn = self._run_fn or self._module().run_experiment
        return fn(name, metrics, notes=notes, status=status)

    def list(self) -> dict[str, Any]:
        fn = self._list_fn or self._module().list_experiments
        return fn()

    def compare(self, name: str, against: str = "baseline") -> dict[str, Any]:
        fn = self._compare_fn or self._module().compare_experiment
        return fn(name, against)
