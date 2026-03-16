#!/usr/bin/env python3
"""
Ghost Brain — SQLite + sqlite-vec Memory Layer

Indexes second-brain markdown files into a searchable SQLite database with
vector embeddings for semantic search and full SQL for structured queries.

Requires: pip install sqlite-vec
No other external dependencies.

Usage:
  ghost_memory_db.py index              # Full re-index of all memory files
  ghost_memory_db.py index --incremental # Only index changed files
  ghost_memory_db.py search "query"      # Hybrid search (FTS + vector)
  ghost_memory_db.py search "query" fts  # Full-text search only
  ghost_memory_db.py sql "SELECT ..."    # Raw SQL query
  ghost_memory_db.py stats              # Show database statistics
  ghost_memory_db.py query decisions --project NAME --days 30  # Structured query
"""

import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config — all paths relative to workspace
# ---------------------------------------------------------------------------

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
    os.path.expanduser("~/.openclaw/workspace")))
DB_PATH = WORKSPACE / ".local" / "ghost_memory.db"
EMBEDDING_DIM = 64  # For local hash embeddings; increase if using API embeddings

# Second brain files to index (relative to workspace)
MEMORY_FILES = {
    "decisions": "memory/decisions.md",
    "people": "memory/people.md",
    "ideas": "memory/ideas.md",
    "commitments": "memory/commitments.md",
    "follow-ups": "memory/follow-ups.md",
    "learnings": ".learnings/LEARNINGS.md",
    "errors": ".learnings/ERRORS.md",
}

# Directories to scan
SCAN_DIRS = {
    "daily_notes": ("memory", "????-??-??.md"),
    "domain_learnings": (".learnings/domains", "*.md"),
    "project_learnings": (".learnings/projects", "*.md"),
    "weekly_notes": ("memory/weekly", "*.md"),
}

# Embedding provider: "local" (zero-cost deterministic hash) or future API provider
EMBEDDING_PROVIDER = os.environ.get("GHOST_EMBEDDING_PROVIDER", "local")

# ---------------------------------------------------------------------------
# Database Setup
# ---------------------------------------------------------------------------

def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open database with sqlite-vec loaded."""
    try:
        import sqlite_vec
    except ImportError:
        print("❌ sqlite-vec not installed. Run: pip install sqlite-vec")
        sys.exit(1)

    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(path))
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_schema(db: sqlite3.Connection):
    """Create tables if they don't exist."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            logged_date TEXT,
            area TEXT,
            priority TEXT,
            status TEXT,
            metadata_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS item_tags (
            item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (item_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS links (
            from_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
            to_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL DEFAULT 'relates_to',
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (from_id, to_id, link_type)
        );

        CREATE TABLE IF NOT EXISTS file_index (
            path TEXT PRIMARY KEY,
            hash TEXT NOT NULL,
            last_indexed TEXT DEFAULT (datetime('now')),
            item_count INTEGER DEFAULT 0
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
            title, content, item_type, area,
            content='items',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
            INSERT INTO items_fts(rowid, title, content, item_type, area)
            VALUES (new.id, new.title, new.content, new.item_type, new.area);
        END;
        CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
            INSERT INTO items_fts(items_fts, rowid, title, content, item_type, area)
            VALUES ('delete', old.id, old.title, old.content, old.item_type, old.area);
        END;
        CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
            INSERT INTO items_fts(items_fts, rowid, title, content, item_type, area)
            VALUES ('delete', old.id, old.title, old.content, old.item_type, old.area);
            INSERT INTO items_fts(rowid, title, content, item_type, area)
            VALUES (new.id, new.title, new.content, new.item_type, new.area);
        END;

        CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);
        CREATE INDEX IF NOT EXISTS idx_items_date ON items(logged_date);
        CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_file);
        CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
    """)

    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS items_vec USING vec0(
            item_id INTEGER PRIMARY KEY,
            embedding float[{EMBEDDING_DIM}]
        )
    """)
    db.commit()

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def _local_embedding(text: str) -> list[float]:
    """Deterministic hash-based embedding (zero-cost, offline).
    For production quality, switch GHOST_EMBEDDING_PROVIDER to an API provider."""
    vec = []
    for i in range(EMBEDDING_DIM):
        h = hashlib.sha256(f"{i}:{text.lower().strip()}".encode()).digest()
        val = struct.unpack('f', h[:4])[0]
        val = (val % 2) - 1
        vec.append(val)
    magnitude = sum(v * v for v in vec) ** 0.5
    if magnitude > 0:
        vec = [v / magnitude for v in vec]
    return vec


def get_embedding(text: str) -> list[float]:
    if EMBEDDING_PROVIDER == "local":
        return _local_embedding(text)
    raise NotImplementedError(f"Provider '{EMBEDDING_PROVIDER}' not implemented")


def serialize_vec(vec: list[float]) -> bytes:
    return struct.pack(f'{len(vec)}f', *vec)

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_decisions(content: str, source_file: str) -> list[dict]:
    items = []
    for line in content.split("\n"):
        m = re.match(r'\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)(?:\s+—\s+(.+))?$', line.strip())
        if m:
            date, decision, reasoning = m.group(1), m.group(2), m.group(3) or ""
            items.append({
                "item_type": "decision", "title": decision[:200],
                "content": f"{decision}\n\nReasoning: {reasoning}" if reasoning else decision,
                "source_file": source_file, "logged_date": date, "status": "active",
            })
    return items


def parse_learning_blocks(content: str, source_file: str) -> list[dict]:
    items = []
    pattern = r'## \[((?:LRN|ERR)-\d{8}-\d{3})\]\s+(\S+)(.*?)(?=\n## \[|$)'
    for match in re.finditer(pattern, content, re.DOTALL):
        entry_id, entry_type_label, block = match.group(1), match.group(2), match.group(3)
        title, priority, status, area, logged, tags = "", "medium", "active", "", "", []

        for line in block.split("\n"):
            ls = line.strip()
            if ls.startswith("**Logged**:"): logged = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Priority**:"): priority = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Status**:"): status = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Area**:"): area = ls.split(":", 1)[1].strip().strip("*")
            elif not title and ls and not ls.startswith(("**", "###", "- ")):
                title = ls

        tags_match = re.search(r'Tags:\s*(.+)', block)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(",")]

        logged_date = None
        if logged:
            dm = re.match(r'(\d{4}-\d{2}-\d{2})', logged)
            if dm: logged_date = dm.group(1)

        items.append({
            "item_type": "error" if entry_id.startswith("ERR") else "learning",
            "title": title[:200] if title else f"[{entry_id}]",
            "content": block.strip()[:2000], "source_file": source_file,
            "logged_date": logged_date, "area": area, "priority": priority,
            "status": status, "tags": tags,
            "metadata_json": json.dumps({"entry_id": entry_id, "entry_type": entry_type_label}),
        })
    return items


def parse_people(content: str, source_file: str) -> list[dict]:
    items = []
    for section in re.split(r'\n(?=##[^#]|###[^#])', content):
        m = re.match(r'#{2,3}\s+(.+)', section.strip())
        if m:
            name = m.group(1).strip()
            if name in ("Personal", "Active", "Archived"):
                continue
            items.append({"item_type": "person", "title": name,
                         "content": section.strip()[:1000],
                         "source_file": source_file, "status": "active"})
    return items


def parse_ideas(content: str, source_file: str) -> list[dict]:
    items = []
    for section in re.split(r'\n(?=###[^#])', content):
        m = re.match(r'###\s+(.+)', section.strip())
        if m:
            title = m.group(1).strip()
            if title in ("Archived Ideas",): continue
            status = "active"
            sm = re.search(r'\*\*Status:\*\*\s*(.+)', section)
            if sm:
                st = sm.group(1).strip().lower()
                if "parking" in st or "parked" in st: status = "parked"
                elif "archived" in st: status = "archived"
            items.append({"item_type": "idea", "title": title[:200],
                         "content": section.strip()[:1000],
                         "source_file": source_file, "status": status})
    return items


def parse_table_rows(content: str, source_file: str, item_type: str) -> list[dict]:
    """Generic parser for markdown table-based files (follow-ups, commitments)."""
    items = []
    for line in content.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[1] and not parts[1].startswith("---"):
            # Skip header row
            if parts[1] in ("Item", "Date", "—"): continue
            items.append({
                "item_type": item_type,
                "title": parts[1][:200] if parts[1] != "No active commitments" else "",
                "content": " | ".join(parts[1:]),
                "source_file": source_file, "status": "active",
                "logged_date": parts[1] if re.match(r'\d{4}-\d{2}-\d{2}', parts[1]) else
                              (parts[3] if len(parts) > 3 and re.match(r'\d{4}-\d{2}-\d{2}', parts[3]) else None),
            })
    return [i for i in items if i["title"]]


def parse_daily_note(content: str, source_file: str) -> list[dict]:
    items = []
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', source_file)
    date = date_match.group(1) if date_match else None
    for section in re.split(r'\n(?=## )', content):
        m = re.match(r'## (.+)', section.strip())
        if m:
            section_title = m.group(1).strip()
            items.append({
                "item_type": "daily_note",
                "title": f"[{date}] {section_title}" if date else section_title,
                "content": section.strip()[:2000], "source_file": source_file,
                "logged_date": date, "status": "active",
                "metadata_json": json.dumps({"section": section_title}),
            })
    return items

# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def file_hash(filepath: Path) -> str:
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def index_file(db: sqlite3.Connection, items: list[dict]):
    for item in items:
        cursor = db.execute("""
            INSERT INTO items (item_type, title, content, source_file, source_hash,
                             logged_date, area, priority, status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item["item_type"], item["title"], item["content"], item["source_file"],
              hashlib.sha256(item["content"].encode()).hexdigest()[:16],
              item.get("logged_date"), item.get("area", ""), item.get("priority", ""),
              item.get("status", "active"), item.get("metadata_json", "")))
        item_id = cursor.lastrowid

        for tag_name in item.get("tags", []):
            if not tag_name: continue
            db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = db.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?, ?)", (item_id, tag_id))

        embed_text = f"{item['title']} {item['content'][:500]}"
        vec = get_embedding(embed_text)
        db.execute("INSERT INTO items_vec (item_id, embedding) VALUES (?, ?)",
                  (item_id, serialize_vec(vec)))


def full_index(db: sqlite3.Connection, workspace: Path):
    print("🔄 Full re-index starting...")
    db.executescript("DELETE FROM item_tags; DELETE FROM links; DELETE FROM items_vec; DELETE FROM items; DELETE FROM file_index;")

    total_items = 0
    parsers = {
        "decisions": parse_decisions, "people": parse_people,
        "ideas": parse_ideas, "learnings": parse_learning_blocks,
        "errors": parse_learning_blocks,
        "commitments": lambda c, s: parse_table_rows(c, s, "commitment"),
        "follow-ups": lambda c, s: parse_table_rows(c, s, "follow-up"),
    }

    for key, rel_path in MEMORY_FILES.items():
        filepath = workspace / rel_path
        if not filepath.exists(): continue
        content = filepath.read_text(encoding="utf-8")
        items = parsers.get(key, parse_daily_note)(content, rel_path)
        index_file(db, items)
        db.execute("INSERT OR REPLACE INTO file_index (path, hash, item_count) VALUES (?, ?, ?)",
                  (rel_path, file_hash(filepath), len(items)))
        total_items += len(items)
        if items: print(f"  ✅ {rel_path}: {len(items)} items")

    for key, (dir_path, pattern) in SCAN_DIRS.items():
        full_dir = workspace / dir_path
        if not full_dir.exists(): continue
        for filepath in sorted(full_dir.glob(pattern)):
            if filepath.name == "README.md": continue
            rel = str(filepath.relative_to(workspace))
            content = filepath.read_text(encoding="utf-8")
            parser = parse_learning_blocks if "learnings" in key else parse_daily_note
            items = parser(content, rel)
            index_file(db, items)
            db.execute("INSERT OR REPLACE INTO file_index (path, hash, item_count) VALUES (?, ?, ?)",
                      (rel, file_hash(filepath), len(items)))
            total_items += len(items)
            if items: print(f"  ✅ {rel}: {len(items)} items")

    db.commit()
    print(f"\n✅ Indexed {total_items} items total")
    return total_items


def incremental_index(db: sqlite3.Connection, workspace: Path):
    print("🔄 Incremental index...")
    changed, total_new = 0, 0

    all_files = {}
    for key, rel_path in MEMORY_FILES.items():
        fp = workspace / rel_path
        if fp.exists(): all_files[rel_path] = (key, fp)
    for key, (dir_path, pattern) in SCAN_DIRS.items():
        full_dir = workspace / dir_path
        if not full_dir.exists(): continue
        for fp in full_dir.glob(pattern):
            if fp.name == "README.md": continue
            all_files[str(fp.relative_to(workspace))] = (key, fp)

    parsers = {
        "decisions": parse_decisions, "people": parse_people,
        "ideas": parse_ideas, "learnings": parse_learning_blocks,
        "errors": parse_learning_blocks,
        "commitments": lambda c, s: parse_table_rows(c, s, "commitment"),
        "follow-ups": lambda c, s: parse_table_rows(c, s, "follow-up"),
    }

    for rel_path, (key, filepath) in all_files.items():
        h = file_hash(filepath)
        row = db.execute("SELECT hash FROM file_index WHERE path = ?", (rel_path,)).fetchone()
        if row and row[0] == h: continue

        changed += 1
        for old_id in [r[0] for r in db.execute("SELECT id FROM items WHERE source_file = ?", (rel_path,)).fetchall()]:
            db.execute("DELETE FROM items_vec WHERE item_id = ?", (old_id,))
        db.execute("DELETE FROM items WHERE source_file = ?", (rel_path,))

        content = filepath.read_text(encoding="utf-8")
        parser = parsers.get(key)
        if not parser:
            parser = parse_learning_blocks if "learnings" in key else parse_daily_note
        items = parser(content, rel_path)
        index_file(db, items)
        db.execute("INSERT OR REPLACE INTO file_index (path, hash, item_count) VALUES (?, ?, ?)",
                  (rel_path, h, len(items)))
        total_new += len(items)
        print(f"  🔄 {rel_path}: {len(items)} items")

    db.commit()
    print("  ℹ️  No files changed" if changed == 0 else f"\n✅ Re-indexed {changed} files, {total_new} items")

# ---------------------------------------------------------------------------
# Search & Query
# ---------------------------------------------------------------------------

def search_fts(db, query, limit=10):
    return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3],
             "source": r[4], "status": r[5], "snippet": r[6]}
            for r in db.execute("""
                SELECT i.id, i.item_type, i.title, i.logged_date, i.source_file, i.status,
                       snippet(items_fts, 1, '→', '←', '...', 30)
                FROM items_fts f JOIN items i ON i.id = f.rowid
                WHERE items_fts MATCH ? ORDER BY rank LIMIT ?
            """, (query, limit)).fetchall()]


def search_vector(db, query, limit=10):
    vec = get_embedding(query)
    return [{"id": r[0], "distance": round(r[1], 4), "type": r[2], "title": r[3],
             "date": r[4], "source": r[5], "status": r[6], "snippet": r[7]}
            for r in db.execute("""
                SELECT v.item_id, v.distance, i.item_type, i.title, i.logged_date,
                       i.source_file, i.status, substr(i.content, 1, 200)
                FROM items_vec v JOIN items i ON i.id = v.item_id
                WHERE embedding MATCH ? AND k = ? ORDER BY v.distance
            """, (serialize_vec(vec), limit)).fetchall()]


def search_hybrid(db, query, limit=10):
    fts = {r["id"]: {**r, "match": "fts"} for r in search_fts(db, query, limit * 2)}
    for r in search_vector(db, query, limit * 2):
        if r["id"] in fts: fts[r["id"]]["match"] = "both"
        else: fts[r["id"]] = {**r, "match": "vec"}
    return sorted(fts.values(), key=lambda x: (0 if x["match"] == "both" else 1 if x["match"] == "fts" else 2))[:limit]


def structured_query(db, item_type, project=None, days=None, status=None, limit=20):
    sql = "SELECT id, item_type, title, logged_date, source_file, status, substr(content, 1, 200) FROM items WHERE item_type = ?"
    params = [item_type]
    if project:
        sql += " AND (title LIKE ? OR content LIKE ?)"; params.extend([f"%{project}%"] * 2)
    if days:
        sql += " AND logged_date >= ?"; params.append((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"))
    if status:
        sql += " AND status = ?"; params.append(status)
    sql += " ORDER BY logged_date DESC LIMIT ?"; params.append(limit)
    return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3], "source": r[4], "status": r[5], "snippet": r[6]}
            for r in db.execute(sql, params).fetchall()]

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def show_stats(db):
    total = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    by_type = db.execute("SELECT item_type, COUNT(*) FROM items GROUP BY item_type ORDER BY COUNT(*) DESC").fetchall()
    files = db.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
    tags = db.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    print(f"📊 Ghost Memory DB\n   Size: {db_size/1024:.1f}KB | Items: {total} | Files: {files} | Tags: {tags}")
    for t, c in by_type: print(f"   {t}: {c}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return

    cmd = sys.argv[1]
    db = get_db()
    init_schema(db)

    if cmd == "index":
        (incremental_index if "--incremental" in sys.argv else full_index)(db, WORKSPACE)
    elif cmd == "search":
        if len(sys.argv) < 3: print("Usage: ghost_memory_db.py search \"query\""); return
        mode = sys.argv[3] if len(sys.argv) > 3 else "hybrid"
        results = {"fts": search_fts, "vec": search_vector}.get(mode, search_hybrid)(db, sys.argv[2])
        for r in results or [print("No results.")]:
            if isinstance(r, type(None)): break
            ml = f" [{r.get('match','')}]" if 'match' in r else ""
            print(f"  [{r['type']}] {r['title']}{ml}")
            print(f"    Date: {r.get('date','-')} | Source: {r['source']}")
            if r.get('snippet'): print(f"    {r['snippet'][:150]}...")
            print()
    elif cmd == "sql":
        if len(sys.argv) < 3: print("Usage: ghost_memory_db.py sql \"SELECT ...\""); return
        try:
            rows = db.execute(sys.argv[2]).fetchall()
            for row in rows: print(" | ".join(str(v) for v in row))
        except Exception as e: print(f"SQL error: {e}")
    elif cmd == "query":
        if len(sys.argv) < 3: print("Usage: ghost_memory_db.py query <type> [--project X] [--days N]"); return
        kw = {}; args = sys.argv[3:]; i = 0
        while i < len(args):
            if args[i].startswith("--") and i+1 < len(args):
                key = args[i][2:]; val = args[i+1]
                kw[key] = int(val) if key in ("days", "limit") else val; i += 2
            else: i += 1
        for r in structured_query(db, sys.argv[2], **kw) or [print("No results.")]:
            if isinstance(r, type(None)): break
            print(f"  [{r.get('date','-')}] {r['title']}\n    Source: {r['source']}")
    elif cmd == "stats":
        show_stats(db)
    else:
        print(f"Unknown: {cmd}"); print(__doc__)
    db.close()


if __name__ == "__main__":
    main()
