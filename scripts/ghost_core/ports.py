from __future__ import annotations

from typing import Any, Protocol

from .contracts import (
    CaptureRequest,
    CaptureResult,
    LearningDigest,
    LearningReflectionRequest,
    LearningReflectionResult,
    LearningStatusSnapshot,
    RecallQuery,
    RecallReport,
    SessionContextSnapshot,
    UserModelSignal,
)


class MemoryStore(Protocol):
    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]: ...
    def stats(self) -> dict[str, Any]: ...


class RecallService(Protocol):
    def recall(self, request: RecallQuery) -> RecallReport: ...


class CaptureRouter(Protocol):
    def capture(self, request: CaptureRequest) -> CaptureResult: ...


class LearningService(Protocol):
    def reflect(self, request: LearningReflectionRequest) -> LearningReflectionResult: ...
    def status(self) -> LearningStatusSnapshot: ...
    def digest(self, days: int = 30) -> LearningDigest: ...


class SafetyScanner(Protocol):
    def is_safe(self, text: str) -> bool: ...
    def is_duplicate(self, path: str, content: str) -> bool: ...


class UserModelStore(Protocol):
    def get_user_model(self) -> dict[str, Any]: ...
    def update_user_model(self, signal: UserModelSignal) -> None: ...


class SessionContextStore(Protocol):
    def snapshot(self) -> SessionContextSnapshot: ...
