#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ghost_core.contracts import SCHEMA_MEMORY_SYNC
from ghost_core.workspace import get_workspace_paths
from ghost_memory_db import MEMORY_FILES, SCAN_DIRS, file_hash

CRITICAL_MEMORY_PATHS = {
    "memory/decisions.md",
    "memory/people.md",
    "memory/commitments.md",
    "memory/follow-ups.md",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _collect_source_files(workspace: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for rel_path in MEMORY_FILES.values():
        path = workspace / rel_path
        if path.exists():
            files[rel_path] = path
    for directory, pattern in SCAN_DIRS.values():
        root = workspace / directory
        if not root.exists():
            continue
        for path in sorted(root.glob(pattern)):
            if path.name == "README.md":
                continue
            files[str(path.relative_to(workspace))] = path
    return files


def _load_file_index(db_path: Path) -> tuple[dict[str, dict[str, Any]], str | None]:
    if not db_path.exists():
        return {}, "memory_db_missing"
    try:
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT path, hash, last_indexed, item_count FROM file_index").fetchall()
    except sqlite3.Error as exc:
        return {}, f"file_index_unavailable:{exc}"
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {
        row[0]: {"hash": row[1], "last_indexed": row[2], "item_count": row[3]}
        for row in rows
    }, None


def _status_for(drifted: list[dict[str, Any]], missing: list[dict[str, Any]], orphaned: list[dict[str, Any]], db_error: str | None) -> str:
    if db_error == "memory_db_missing":
        return "missing"
    if db_error:
        return "degraded"
    if not drifted and not missing and not orphaned:
        return "healthy"
    if any(item["path"] in CRITICAL_MEMORY_PATHS for item in drifted + missing):
        return "drifted"
    if len(drifted) + len(missing) >= 3:
        return "drifted"
    return "stale"


def build_memory_sync_report(workspace: str | Path | None = None, *, limit: int = 10) -> dict[str, Any]:
    paths = get_workspace_paths(workspace or os.environ.get("OPENCLAW_WORKSPACE"))
    db_path = paths.local_dir / "ghost_memory.db"
    source_files = _collect_source_files(paths.workspace)
    indexed, db_error = _load_file_index(db_path)

    drifted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    clean = 0
    db_mtime = datetime.fromtimestamp(db_path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z") if db_path.exists() else ""

    for rel_path, path in source_files.items():
        current_hash = file_hash(path)
        row = indexed.get(rel_path)
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
        if row is None:
            missing.append({"path": rel_path, "modified_at": modified_at})
            continue
        if row.get("hash") != current_hash:
            drifted.append(
                {
                    "path": rel_path,
                    "modified_at": modified_at,
                    "last_indexed": row.get("last_indexed", ""),
                    "item_count": row.get("item_count", 0),
                }
            )
            continue
        clean += 1

    orphaned = [
        {"path": rel_path, "last_indexed": row.get("last_indexed", ""), "item_count": row.get("item_count", 0)}
        for rel_path, row in indexed.items()
        if rel_path not in source_files
    ]

    status = _status_for(drifted, missing, orphaned, db_error)
    if status == "healthy":
        recommendation = "Memory DB appears aligned with markdown sources."
    else:
        recommendation = "Run: bash scripts/run_memory_pipeline.sh"

    return {
        "schema_version": SCHEMA_MEMORY_SYNC,
        "generated_at": _now_iso(),
        "status": status,
        "database_path": str(db_path),
        "database_updated_at": db_mtime,
        "source_files": len(source_files),
        "indexed_files": len(indexed),
        "clean_files": clean,
        "drifted_count": len(drifted),
        "missing_from_db_count": len(missing),
        "orphaned_count": len(orphaned),
        "drifted": drifted[:limit],
        "missing_from_db": missing[:limit],
        "orphaned": orphaned[:limit],
        "warnings": [db_error] if db_error else [],
        "recommendation": recommendation,
    }


def print_memory_sync_report(payload: dict[str, Any]) -> None:
    print("🧠 Ghost Memory Sync")
    print(f"   Status: {payload.get('status', 'unknown')}")
    print(f"   Sources: {payload.get('source_files', 0)} | indexed: {payload.get('indexed_files', 0)} | clean: {payload.get('clean_files', 0)}")
    print(f"   Drifted: {payload.get('drifted_count', 0)} | missing: {payload.get('missing_from_db_count', 0)} | orphaned: {payload.get('orphaned_count', 0)}")
    if payload.get("warnings"):
        for warning in payload["warnings"][:3]:
            print(f"   Warning: {warning}")
    for item in payload.get("drifted", [])[:5]:
        print(f"   - drifted: {item['path']} (modified {item.get('modified_at', '-')}, indexed {item.get('last_indexed', '-')})")
    for item in payload.get("missing_from_db", [])[:5]:
        print(f"   - missing: {item['path']} (modified {item.get('modified_at', '-')})")
    if payload.get("recommendation"):
        print(f"   Next: {payload['recommendation']}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost_memory_sync", description="Ghost markdown↔DB freshness checks")
    sub = parser.add_subparsers(dest="command")
    check_p = sub.add_parser("check", help="Check markdown↔DB freshness and drift")
    check_p.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    payload = build_memory_sync_report()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_memory_sync_report(payload)


if __name__ == "__main__":
    main()
