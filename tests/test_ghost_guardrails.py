#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_guardrails import build_guardrail_report


def _write_session(path: Path, messages: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [{"type": "session", "id": path.stem, "timestamp": messages[0][2]}]
    for index, (role, text, timestamp) in enumerate(messages, start=1):
        records.append(
            {
                "type": "message",
                "id": f"m{index}",
                "timestamp": timestamp,
                "message": {
                    "role": role,
                    "content": [{"type": "text", "text": text}],
                    "timestamp": timestamp,
                },
            }
        )
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def test_guardrails_blocks_when_significant_session_is_newer_than_daily_note(tmp_path):
    (tmp_path / "memory").mkdir(parents=True, exist_ok=True)
    note = tmp_path / "memory" / "2026-04-12.md"
    note.write_text("# Daily note\n", encoding="utf-8")
    os.utime(note, (1, 1))

    session_root = tmp_path / "agents"
    _write_session(
        session_root / "main" / "sessions" / "uncaptured.jsonl",
        [
            ("user", "We changed the release plan", "2026-04-12T09:00:00Z"),
            ("assistant", "Need to update docs and cut a clean patch release", "2026-04-12T09:01:00Z"),
            ("user", "Also add the missing guardrails", "2026-04-12T09:02:00Z"),
            ("assistant", "Okay, I will implement them", "2026-04-12T09:03:00Z"),
            ("user", "Don't forget transcript recall", "2026-04-12T09:04:00Z"),
            ("assistant", "Got it", "2026-04-12T09:05:00Z"),
        ],
    )

    payload = build_guardrail_report(
        workspace=tmp_path,
        session_root=session_root,
        days=30,
        grace_minutes=0,
    )
    assert payload["schema_version"] == "ghost-guardrails/v1"
    assert payload["status"] == "block"
    assert payload["uncaptured_count"] == 1


def test_guardrails_clear_when_daily_note_is_newer_than_session(tmp_path):
    (tmp_path / "memory").mkdir(parents=True, exist_ok=True)
    note = tmp_path / "memory" / "2026-04-12.md"
    note.write_text("# Daily note\n", encoding="utf-8")
    os.utime(note, (1893456600, 1893456600))

    session_root = tmp_path / "agents"
    _write_session(
        session_root / "main" / "sessions" / "captured.jsonl",
        [
            ("user", "Summarize the release prep", "2026-04-12T09:00:00Z"),
            ("assistant", "Done", "2026-04-12T09:01:00Z"),
            ("user", "Add the final changelog note", "2026-04-12T09:02:00Z"),
            ("assistant", "Added", "2026-04-12T09:03:00Z"),
            ("user", "Great", "2026-04-12T09:04:00Z"),
            ("assistant", "All set", "2026-04-12T09:05:00Z"),
        ],
    )

    payload = build_guardrail_report(
        workspace=tmp_path,
        session_root=session_root,
        days=30,
        grace_minutes=0,
    )
    assert payload["status"] == "clear"
    assert payload["uncaptured_count"] == 0
