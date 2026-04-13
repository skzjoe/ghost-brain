from __future__ import annotations

from typing import Any, Callable


class UsageDashboardAdapter:
    def __init__(self, dashboard_fn: Callable[..., dict[str, Any]] | None = None):
        self._dashboard_fn = dashboard_fn

    def _module(self):
        import ghost_research_lib
        return ghost_research_lib

    def snapshot(self, days: int = 30) -> dict[str, Any]:
        fn = self._dashboard_fn or self._module().build_dashboard
        return fn(days=days)
