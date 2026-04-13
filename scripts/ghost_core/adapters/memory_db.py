from __future__ import annotations

from typing import Any, Callable

from ..errors import BackendUnavailable


class MemoryDbAdapter:
    def __init__(self, backend_factory: Callable[[], Any] | None = None):
        self._backend_factory = backend_factory

    def _make_backend(self):
        if self._backend_factory is not None:
            return self._backend_factory()
        try:
            from ghost_memory_db import GhostMemory
        except Exception as exc:  # pragma: no cover
            raise BackendUnavailable("GhostMemory backend is unavailable") from exc
        return GhostMemory()

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        backend = self._make_backend()
        try:
            if hasattr(backend, "search_hybrid"):
                return backend.search_hybrid(query, limit)
            return backend.search_fts(query, limit)
        finally:
            close = getattr(backend, "close", None)
            if callable(close):
                close()

    def stats(self) -> dict[str, Any]:
        backend = self._make_backend()
        try:
            stats = getattr(backend, "stats", None)
            if callable(stats):
                return stats()
            return {}
        finally:
            close = getattr(backend, "close", None)
            if callable(close):
                close()
