"""Stable Ghost core package surface."""

from .contracts import (
    CaptureRequest,
    CaptureResult,
    LearningDigest,
    LearningReflectionRequest,
    LearningReflectionResult,
    LearningStatusSnapshot,
    RecallEvidence,
    RecallHit,
    RecallQuery,
    RecallReport,
    SessionContextSnapshot,
    UserModelSignal,
)
from .adapters import SessionContextAdapter
from .defaults import GhostCoreRuntime, build_default_runtime
from .workspace import GhostWorkspacePaths, get_workspace_paths

__all__ = [
    "CaptureRequest",
    "CaptureResult",
    "GhostCoreRuntime",
    "GhostWorkspacePaths",
    "LearningDigest",
    "LearningReflectionRequest",
    "LearningReflectionResult",
    "LearningStatusSnapshot",
    "RecallEvidence",
    "RecallHit",
    "RecallQuery",
    "RecallReport",
    "SessionContextAdapter",
    "SessionContextSnapshot",
    "UserModelSignal",
    "build_default_runtime",
    "get_workspace_paths",
]
