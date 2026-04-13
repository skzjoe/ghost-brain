from __future__ import annotations

import re
from pathlib import Path

from ..contracts import SessionContextSnapshot
from ..workspace import GhostWorkspacePaths, get_workspace_paths


class SessionContextAdapter:
    def __init__(
        self,
        workspace: str | Path | None = None,
        active_work_path: str | Path | None = None,
        commitments_path: str | Path | None = None,
    ):
        self._paths: GhostWorkspacePaths = get_workspace_paths(workspace)
        self.active_work_path = Path(active_work_path) if active_work_path else self._paths.workspace / "ACTIVE_WORK.md"
        self.commitments_path = Path(commitments_path) if commitments_path else self._paths.memory_dir / "commitments.md"

    def snapshot(self) -> SessionContextSnapshot:
        active_text = self._read_text(self.active_work_path)
        commitments_text = self._read_text(self.commitments_path)
        return SessionContextSnapshot(
            focus=self._extract_focus(active_text),
            blockers=self._extract_blockers(active_text),
            next_actions=self._extract_if_idle_actions(active_text),
            commitments_due=self._extract_commitments_due(active_text, commitments_text),
            second_brain_focus=self._extract_second_brain_focus(),
            guardrails=self._extract_guardrails(),
            memory_sync=self._extract_memory_sync(),
        )

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    @staticmethod
    def _extract_focus(text: str) -> str:
        if not text:
            return ""
        lines = text.splitlines()
        entries: list[str] = []
        current_heading = ""
        status = ""
        focus = ""
        in_current_workstreams = False
        for line in lines + ["## END"]:
            stripped = line.strip()
            if stripped.startswith("## "):
                if current_heading and ("active" in status.lower() or "on-demand" in status.lower()):
                    entries.append(SessionContextAdapter._format_focus(current_heading, focus or status))
                in_current_workstreams = stripped == "## Current Workstreams"
                current_heading = ""
                status = ""
                focus = ""
                continue
            if not in_current_workstreams:
                continue
            if stripped.startswith("### "):
                if current_heading and ("active" in status.lower() or "on-demand" in status.lower()):
                    entries.append(SessionContextAdapter._format_focus(current_heading, focus or status))
                current_heading = stripped[4:].strip()
                status = ""
                focus = ""
                continue
            if stripped.startswith("- **Status:**"):
                status = stripped.split("**Status:**", 1)[1].strip()
            elif stripped.startswith("- **Focus:**"):
                focus = stripped.split("**Focus:**", 1)[1].strip()
        return "; ".join(entries[:3])

    @staticmethod
    def _format_focus(heading: str, focus: str) -> str:
        return f"{heading}: {focus}" if focus else heading

    @staticmethod
    def _extract_if_idle_actions(text: str) -> list[str]:
        return SessionContextAdapter._extract_bullets_from_section(text, "## If Idle, Pull Next")[:5]

    @staticmethod
    def _extract_bullets_from_section(text: str, section_header: str) -> list[str]:
        lines = text.splitlines()
        in_section = False
        bullets: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if in_section and stripped != section_header:
                    break
                in_section = stripped == section_header
                continue
            if in_section and stripped.startswith("- "):
                bullets.append(stripped[2:].strip())
        return bullets

    @staticmethod
    def _extract_blockers(text: str) -> list[str]:
        if not text:
            return []
        blockers: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if not stripped:
                continue
            if stripped.startswith("|") and any(token in lower for token in ["blocked", "deadline risk", "waiting on"]):
                blockers.append(re.sub(r"\s*\|\s*", " | ", stripped).strip(" |"))
            elif stripped.startswith("- ") and any(token in lower for token in ["blocked", "deadline", "waiting on", "urgent"]):
                blockers.append(stripped[2:].strip())
        return blockers[:5]

    @staticmethod
    def _extract_commitments_due(active_text: str, commitments_text: str) -> list[str]:
        due: list[str] = []
        for line in active_text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if "deadline" in lower or "days to deadline" in lower:
                due.append(stripped)
        for line in commitments_text.splitlines():
            stripped = line.strip()
            if "Deadline:" in stripped:
                due.append(stripped)
        seen: list[str] = []
        for item in due:
            if item not in seen:
                seen.append(item)
        return seen[:5]

    @staticmethod
    def _extract_second_brain_focus() -> dict:
        try:
            from ghost_research_lib import build_focus_report

            focus = build_focus_report(days=30)
            return {
                "repetition_risk": (focus.get("second_brain") or {}).get("repetition_risk", "unknown"),
                "continuity_health": (focus.get("second_brain") or {}).get("continuity_health", "unknown"),
                "next_best_action": (focus.get("second_brain") or {}).get("next_best_action", ""),
                "recommendations": focus.get("recommendations", [])[:3],
                "memory_signals": focus.get("memory_signals", [])[:3],
                "warnings": focus.get("warnings", [])[:3],
            }
        except Exception as exc:
            return {"status": "degraded", "warnings": [f"focus_unavailable:{exc}"]}

    @staticmethod
    def _extract_guardrails() -> dict:
        try:
            from ghost_guardrails import build_guardrail_report

            report = build_guardrail_report(days=3)
            return {
                "status": report.get("status", "unknown"),
                "capture_risk": report.get("capture_risk", "unknown"),
                "uncaptured_count": report.get("uncaptured_count", 0),
                "next_action": report.get("next_action", ""),
                "warnings": report.get("warnings", [])[:3],
            }
        except Exception as exc:
            return {"status": "degraded", "warnings": [f"guardrails_unavailable:{exc}"]}

    @staticmethod
    def _extract_memory_sync() -> dict:
        try:
            from ghost_memory_sync import build_memory_sync_report

            report = build_memory_sync_report()
            return {
                "status": report.get("status", "unknown"),
                "drifted_count": report.get("drifted_count", 0),
                "missing_from_db_count": report.get("missing_from_db_count", 0),
                "recommendation": report.get("recommendation", ""),
                "warnings": report.get("warnings", [])[:3],
            }
        except Exception as exc:
            return {"status": "degraded", "warnings": [f"memory_sync_unavailable:{exc}"]}
