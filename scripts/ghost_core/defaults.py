from __future__ import annotations

from dataclasses import dataclass

from .adapters import LearningLoopAdapter, MemoryDbAdapter, SessionContextAdapter, UnifiedRecallAdapter
from .workspace import GhostWorkspacePaths, get_workspace_paths


@dataclass(frozen=True)
class GhostCoreRuntime:
    paths: GhostWorkspacePaths
    memory_db: MemoryDbAdapter
    recall: UnifiedRecallAdapter
    learning: LearningLoopAdapter
    session_context: SessionContextAdapter


def build_default_runtime(workspace: str | None = None) -> GhostCoreRuntime:
    paths = get_workspace_paths(workspace)
    return GhostCoreRuntime(
        paths=paths,
        memory_db=MemoryDbAdapter(),
        recall=UnifiedRecallAdapter(),
        learning=LearningLoopAdapter(),
        session_context=SessionContextAdapter(workspace=paths.workspace),
    )
