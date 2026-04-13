#!/usr/bin/env python3

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ghost_memory_db import file_hash
from ghost_memory_sync import build_memory_sync_report


def _seed_db(db_path: Path, entries: dict[str, tuple[str, int]]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE file_index (path TEXT PRIMARY KEY, hash TEXT NOT NULL, last_indexed TEXT DEFAULT '', item_count INTEGER DEFAULT 0)")
    for rel_path, (digest, item_count) in entries.items():
        conn.execute(
            "INSERT INTO file_index (path, hash, last_indexed, item_count) VALUES (?, ?, ?, ?)",
            (rel_path, digest, "2026-04-12T10:00:00Z", item_count),
        )
    conn.commit()
    conn.close()


def test_memory_sync_healthy_when_hashes_match(tmp_path):
    decisions = tmp_path / "memory" / "decisions.md"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    decisions.write_text("# Decisions\n\n- Keep markdown canonical\n", encoding="utf-8")

    db_path = tmp_path / ".local" / "ghost_memory.db"
    _seed_db(db_path, {"memory/decisions.md": (file_hash(decisions), 1)})

    payload = build_memory_sync_report(workspace=tmp_path)
    assert payload["schema_version"] == "ghost-memory-sync/v1"
    assert payload["status"] == "healthy"
    assert payload["drifted_count"] == 0


def test_memory_sync_detects_drift_for_critical_file(tmp_path):
    decisions = tmp_path / "memory" / "decisions.md"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    decisions.write_text("# Decisions\n\n- Original\n", encoding="utf-8")

    db_path = tmp_path / ".local" / "ghost_memory.db"
    _seed_db(db_path, {"memory/decisions.md": ("oldhash", 1)})

    payload = build_memory_sync_report(workspace=tmp_path)
    assert payload["status"] == "drifted"
    assert payload["drifted_count"] == 1
    assert payload["drifted"][0]["path"] == "memory/decisions.md"


def test_memory_sync_missing_db_is_reported(tmp_path):
    payload = build_memory_sync_report(workspace=tmp_path)
    assert payload["status"] == "missing"
    assert payload["warnings"] == ["memory_db_missing"]
