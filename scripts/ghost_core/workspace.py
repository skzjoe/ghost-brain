from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GhostWorkspacePaths:
    workspace: Path
    memory_dir: Path
    learnings_dir: Path
    local_dir: Path
    skills_dir: Path
    user_model_path: Path


def get_workspace_paths(workspace: str | Path | None = None) -> GhostWorkspacePaths:
    root = Path(
        workspace or os.environ.get("OPENCLAW_WORKSPACE") or os.path.expanduser("~/.openclaw/workspace")
    ).expanduser()
    return GhostWorkspacePaths(
        workspace=root,
        memory_dir=root / "memory",
        learnings_dir=root / ".learnings",
        local_dir=root / ".local",
        skills_dir=root / "skills",
        user_model_path=root / "memory" / "user-model.md",
    )
