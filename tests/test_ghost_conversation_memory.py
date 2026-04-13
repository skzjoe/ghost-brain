#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_conversation_memory import recent_conversations, search_conversation_hits, search_conversations


def _write_session(path: Path, messages: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {"type": "session", "id": path.stem, "timestamp": "2026-04-12T01:00:00Z"},
    ]
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
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")


def test_search_conversation_hits_finds_matching_messages(tmp_path):
    root = tmp_path / "agents"
    _write_session(
        root / "main" / "sessions" / "a.jsonl",
        [
            ("user", "Need to finish the Project Atlas launch checklist today", "2026-04-12T01:02:00Z"),
            ("assistant", "We still need hosting access and donation QR details", "2026-04-12T01:03:00Z"),
        ],
    )

    hits = search_conversation_hits("Project Atlas hosting", session_root=root, days=30)
    assert hits
    assert hits[0]["source_bucket"] == "conversation"
    assert "Project Atlas" in hits[0]["snippet"]


def test_recent_conversations_skips_automated_cron_sessions(tmp_path):
    root = tmp_path / "agents"
    _write_session(
        root / "main" / "sessions" / "cron.jsonl",
        [
            ("user", "[cron:abc] Read and follow the prompt at: /tmp/cron.md", "2026-04-12T02:00:00Z"),
        ],
    )
    _write_session(
        root / "main" / "sessions" / "real.jsonl",
        [
            ("user", "Let's review the Ghost Brain release gaps", "2026-04-12T03:00:00Z"),
            ("assistant", "We should close conversation recall and guardrails next", "2026-04-12T03:01:00Z"),
        ],
    )

    payload = recent_conversations(session_root=root, days=30, limit=5)
    assert payload["schema_version"] == "ghost-conversations/v1"
    assert payload["session_count"] == 1
    assert payload["sessions"][0]["session_id"] == "real"


def test_search_conversations_builds_report(tmp_path):
    root = tmp_path / "agents"
    _write_session(
        root / "main" / "sessions" / "b.jsonl",
        [
            ("user", "We need better auto skill matching, not just keyword overlap", "2026-04-12T04:00:00Z"),
            ("assistant", "Agreed, weighted matching would be better", "2026-04-12T04:01:00Z"),
        ],
    )

    payload = search_conversations("keyword overlap", session_root=root, days=30)
    assert payload["schema_version"] == "ghost-conversations/v1"
    assert payload["mode"] == "search"
    assert payload["results"]
