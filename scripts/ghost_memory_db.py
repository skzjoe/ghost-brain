#!/usr/bin/env python3
"""
Ghost Brain — SQLite + sqlite-vec Memory Layer v2

Searchable SQLite database with vector embeddings, full-text search,
knowledge graph, deduplication, analytics, and maintenance pipeline.

Requires: pip install sqlite-vec
Optional: pip install google-genai (for Gemini semantic embeddings, free tier)

Usage:
  ghost_memory_db.py index              # Full re-index
  ghost_memory_db.py index --incremental # Only changed files
  ghost_memory_db.py search "query"      # Hybrid search (FTS + vector)
  ghost_memory_db.py search "query" fts  # Full-text only
  ghost_memory_db.py search "query" vec  # Vector only
  ghost_memory_db.py sql "SELECT ..."    # Raw SQL
  ghost_memory_db.py stats              # Analytics dashboard
  ghost_memory_db.py query decision --project NAME --days 30
  ghost_memory_db.py dedup              # Find duplicates
  ghost_memory_db.py dedup --merge      # Find and merge duplicates
  ghost_memory_db.py links              # Show knowledge graph
  ghost_memory_db.py links --rebuild    # Auto-link from content
  ghost_memory_db.py pipeline           # Full maintenance: index→dedup→links→report
  ghost_memory_db.py export --json      # Export all items as JSON
  ghost_memory_db.py context            # Generate session startup context
  ghost_memory_db.py context --json     # Session context as JSON
  ghost_memory_db.py temporal           # Temporal intelligence report
  ghost_memory_db.py temporal --stale   # Show stale items needing review
  ghost_memory_db.py temporal --hot     # Show most accessed items

Best practice:
  - For automation/cron, prefer `bash scripts/run_memory_pipeline.sh`
    instead of calling `python3 scripts/ghost_memory_db.py pipeline` directly.
  - The wrapper selects a Python runtime that actually has `sqlite-vec` installed.
"""

import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ghost_core.workspace import get_workspace_paths

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace
DB_PATH = _paths.local_dir / "ghost_memory.db"

# Auto-load Gemini API key from secrets file if not already in env
def _load_gemini_key_from_secrets():
    secrets_path = WORKSPACE / "secrets" / "gemini_api_key.txt"
    if secrets_path.exists() and not os.environ.get("GEMINI_API_KEY"):
        key = secrets_path.read_text().strip()
        if key:
            os.environ["GEMINI_API_KEY"] = key
_load_gemini_key_from_secrets()

_has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
EMBEDDING_PROVIDER = os.environ.get("GHOST_EMBEDDING_PROVIDER",
    "gemini" if _has_gemini else "local")
EMBEDDING_DIM = int(os.environ.get("GHOST_EMBEDDING_DIM",
    "256" if EMBEDDING_PROVIDER == "gemini" else "64"))

MEMORY_FILES = {
    "decisions": "memory/decisions.md",
    "people": "memory/people.md",
    "ideas": "memory/ideas.md",
    "commitments": "memory/commitments.md",
    "follow-ups": "memory/follow-ups.md",
    "learnings": ".learnings/LEARNINGS.md",
    "errors": ".learnings/ERRORS.md",
}

SCAN_DIRS = {
    "daily_notes": ("memory", "????-??-??.md"),
    "domain_learnings": (".learnings/domains", "*.md"),
    "project_learnings": (".learnings/projects", "*.md"),
    "weekly_notes": ("memory/weekly", "*.md"),
}

_last_api_call = 0
_API_DELAY = 0.05

# ---------------------------------------------------------------------------
# GhostMemory class — core API
# ---------------------------------------------------------------------------

class GhostMemory:
    """SQLite + sqlite-vec memory layer for Ghost Brain."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db = self._connect()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        import sqlite_vec
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(str(self.db_path))
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _init_schema(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                logged_date TEXT,
                area TEXT DEFAULT '',
                priority TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                source_type TEXT DEFAULT 'markdown',
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                metadata_json TEXT DEFAULT '',
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
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (from_id, to_id, link_type)
            );
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY, hash TEXT NOT NULL,
                last_indexed TEXT DEFAULT (datetime('now')), item_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS duplicates (
                item_a INTEGER REFERENCES items(id) ON DELETE CASCADE,
                item_b INTEGER REFERENCES items(id) ON DELETE CASCADE,
                similarity REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (item_a, item_b)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                title, content, item_type, area, content='items', content_rowid='id'
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
            -- Access log for temporal intelligence
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
                accessed_at TEXT DEFAULT (datetime('now')),
                context TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);
            CREATE INDEX IF NOT EXISTS idx_items_date ON items(logged_date);
            CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_file);
            CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
            CREATE INDEX IF NOT EXISTS idx_items_source_type ON items(source_type);
            CREATE INDEX IF NOT EXISTS idx_items_access_count ON items(access_count);
            CREATE INDEX IF NOT EXISTS idx_access_log_item ON access_log(item_id);
            CREATE INDEX IF NOT EXISTS idx_access_log_time ON access_log(accessed_at);
        """)
        self.db.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS items_vec USING vec0(
                item_id INTEGER PRIMARY KEY, embedding float[{EMBEDDING_DIM}]
            )
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    # --- Item CRUD ---

    def add_item(self, item_type, title, content, source_file,
                 logged_date=None, area="", priority="", status="active",
                 tags=None, metadata=None, source_type="markdown") -> int:
        """Add an item and return its ID."""
        cur = self.db.execute("""
            INSERT INTO items (item_type, title, content, source_file, source_hash,
                             logged_date, area, priority, status, source_type, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_type, title, content, source_file,
              hashlib.sha256(content.encode()).hexdigest()[:16],
              logged_date, area, priority, status, source_type,
              json.dumps(metadata) if metadata else ""))
        item_id = cur.lastrowid

        for tag_name in (tags or []):
            if not tag_name:
                continue
            self.db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tid = self.db.execute("SELECT id FROM tags WHERE name=?", (tag_name,)).fetchone()[0]
            self.db.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (item_id, tid))

        # Embedding
        embed_text = f"{title} {content[:500]}"
        vec = get_embedding(embed_text)
        self.db.execute("INSERT INTO items_vec (item_id, embedding) VALUES (?,?)",
                       (item_id, serialize_vec(vec)))
        return item_id

    def get_item(self, item_id: int) -> Optional[dict]:
        row = self.db.execute(
            "SELECT id, item_type, title, content, source_file, logged_date, area, priority, status, metadata_json FROM items WHERE id=?",
            (item_id,)).fetchone()
        if not row:
            return None
        tags = [r[0] for r in self.db.execute(
            "SELECT t.name FROM tags t JOIN item_tags it ON t.id=it.tag_id WHERE it.item_id=?", (item_id,)).fetchall()]
        return {"id": row[0], "type": row[1], "title": row[2], "content": row[3],
                "source": row[4], "date": row[5], "area": row[6], "priority": row[7],
                "status": row[8], "metadata": row[9], "tags": tags}

    def delete_item(self, item_id: int):
        self.db.execute("DELETE FROM items_vec WHERE item_id=?", (item_id,))
        self.db.execute("DELETE FROM items WHERE id=?", (item_id,))

    # --- Batch indexing ---

    def index_items(self, items: list[dict]):
        """Batch insert items with batch embeddings."""
        if not items:
            return
        texts = [f"{i['title']} {i['content'][:500]}" for i in items]
        vecs = _batch_gemini_embeddings(texts) if EMBEDDING_PROVIDER == "gemini" and len(items) > 1 else [get_embedding(t) for t in texts]

        for item, vec in zip(items, vecs):
            cur = self.db.execute("""
                INSERT INTO items (item_type, title, content, source_file, source_hash,
                                 logged_date, area, priority, status, source_type, metadata_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (item["item_type"], item["title"], item["content"], item["source_file"],
                  hashlib.sha256(item["content"].encode()).hexdigest()[:16],
                  item.get("logged_date"), item.get("area", ""), item.get("priority", ""),
                  item.get("status", "active"), item.get("source_type", "markdown"),
                  item.get("metadata_json", "")))
            iid = cur.lastrowid
            for tag in item.get("tags", []):
                if not tag: continue
                self.db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                tid = self.db.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()[0]
                self.db.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (iid, tid))
            self.db.execute("INSERT INTO items_vec (item_id, embedding) VALUES (?,?)",
                           (iid, serialize_vec(vec)))

    # --- Search ---

    def search_fts(self, query: str, limit: int = 10) -> list[dict]:
        return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3], "source": r[4],
                 "status": r[5], "snippet": r[6]}
                for r in self.db.execute("""
                    SELECT i.id, i.item_type, i.title, i.logged_date, i.source_file, i.status,
                           snippet(items_fts, 1, '→', '←', '...', 30)
                    FROM items_fts f JOIN items i ON i.id=f.rowid
                    WHERE items_fts MATCH ? ORDER BY rank LIMIT ?
                """, (query, limit)).fetchall()]

    def search_vector(self, query: str, limit: int = 10) -> list[dict]:
        vec = get_embedding(query)
        return [{"id": r[0], "distance": round(r[1], 4), "type": r[2], "title": r[3],
                 "date": r[4], "source": r[5], "status": r[6], "snippet": r[7]}
                for r in self.db.execute("""
                    SELECT v.item_id, v.distance, i.item_type, i.title, i.logged_date,
                           i.source_file, i.status, substr(i.content, 1, 200)
                    FROM items_vec v JOIN items i ON i.id=v.item_id
                    WHERE embedding MATCH ? AND k=? ORDER BY v.distance
                """, (serialize_vec(vec), limit)).fetchall()]

    def search_hybrid(self, query: str, limit: int = 10) -> list[dict]:
        seen = {r["id"]: {**r, "match": "fts"} for r in self.search_fts(query, limit * 2)}
        for r in self.search_vector(query, limit * 2):
            if r["id"] in seen:
                seen[r["id"]]["match"] = "both"
            else:
                seen[r["id"]] = {**r, "match": "vec"}
        return sorted(seen.values(), key=lambda x: (0 if x["match"] == "both" else 1 if x["match"] == "fts" else 2))[:limit]

    def structured_query(self, item_type, project=None, days=None, status=None, limit=20) -> list[dict]:
        sql, p = "SELECT id, item_type, title, logged_date, source_file, status, substr(content,1,200) FROM items WHERE item_type=?", [item_type]
        if project:
            sql += " AND (title LIKE ? OR content LIKE ?)"; p += [f"%{project}%"] * 2
        if days:
            sql += " AND logged_date>=?"; p.append((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"))
        if status:
            sql += " AND status=?"; p.append(status)
        sql += " ORDER BY logged_date DESC LIMIT ?"; p.append(limit)
        return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3], "source": r[4], "status": r[5], "snippet": r[6]}
                for r in self.db.execute(sql, p).fetchall()]

    # --- Knowledge Graph ---

    def add_link(self, from_id: int, to_id: int, link_type: str = "relates_to", confidence: float = 1.0):
        self.db.execute(
            "INSERT OR IGNORE INTO links (from_id, to_id, link_type, confidence) VALUES (?,?,?,?)",
            (from_id, to_id, link_type, confidence))

    def get_links(self, item_id: int) -> list[dict]:
        """Get all links for an item (both directions)."""
        rows = self.db.execute("""
            SELECT l.from_id, l.to_id, l.link_type, l.confidence,
                   i1.title as from_title, i2.title as to_title
            FROM links l
            JOIN items i1 ON i1.id = l.from_id
            JOIN items i2 ON i2.id = l.to_id
            WHERE l.from_id=? OR l.to_id=?
        """, (item_id, item_id)).fetchall()
        return [{"from_id": r[0], "to_id": r[1], "type": r[2], "confidence": r[3],
                 "from_title": r[4], "to_title": r[5]} for r in rows]

    def rebuild_links(self) -> int:
        """Auto-detect relationships between items based on content overlap."""
        self.db.execute("DELETE FROM links")
        link_count = 0

        # Strategy 1: Link decisions to daily notes by date
        decisions = self.db.execute(
            "SELECT id, logged_date, title FROM items WHERE item_type='decision' AND logged_date IS NOT NULL").fetchall()
        for dec_id, dec_date, dec_title in decisions:
            # Find daily notes from same date
            notes = self.db.execute(
                "SELECT id FROM items WHERE item_type='daily_note' AND logged_date=? AND id!=?",
                (dec_date, dec_id)).fetchall()
            for (note_id,) in notes:
                self.add_link(dec_id, note_id, "documented_in", 0.8)
                link_count += 1

        # Strategy 2: Link learnings to related decisions by keyword overlap
        learnings = self.db.execute(
            "SELECT id, title, content FROM items WHERE item_type IN ('learning','error')").fetchall()
        for lrn_id, lrn_title, lrn_content in learnings:
            # Extract significant words from learning title
            words = set(re.findall(r'\b[a-zA-Z]{4,}\b', lrn_title.lower()))
            if not words:
                continue
            # Find decisions with matching words
            for word in list(words)[:5]:
                matches = self.db.execute(
                    "SELECT id FROM items WHERE item_type='decision' AND (lower(title) LIKE ? OR lower(content) LIKE ?) AND id!=?",
                    (f"%{word}%", f"%{word}%", lrn_id)).fetchall()
                for (match_id,) in matches:
                    self.add_link(lrn_id, match_id, "relates_to", 0.6)
                    link_count += 1

        # Strategy 3: Link people to items that mention them
        people = self.db.execute(
            "SELECT id, title FROM items WHERE item_type='person'").fetchall()
        for person_id, person_name in people:
            name_lower = person_name.lower().strip()
            if len(name_lower) < 3:
                continue
            mentions = self.db.execute(
                "SELECT id FROM items WHERE item_type!='person' AND (lower(title) LIKE ? OR lower(content) LIKE ?) AND id!=?",
                (f"%{name_lower}%", f"%{name_lower}%", person_id)).fetchall()
            for (mention_id,) in mentions[:10]:  # cap at 10 per person
                self.add_link(person_id, mention_id, "mentioned_in", 0.7)
                link_count += 1

        # Strategy 4: Link follow-ups/commitments to related items
        followups = self.db.execute(
            "SELECT id, title FROM items WHERE item_type IN ('follow-up','commitment')").fetchall()
        for fu_id, fu_title in followups:
            words = set(re.findall(r'\b[a-zA-Z]{4,}\b', fu_title.lower()))
            for word in list(words)[:3]:
                matches = self.db.execute(
                    "SELECT id FROM items WHERE item_type IN ('decision','daily_note') AND lower(content) LIKE ? AND id!=? LIMIT 3",
                    (f"%{word}%", fu_id)).fetchall()
                for (match_id,) in matches:
                    self.add_link(fu_id, match_id, "tracks", 0.5)
                    link_count += 1

        self.db.commit()
        return link_count

    def get_graph_stats(self) -> dict:
        total = self.db.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        by_type = self.db.execute(
            "SELECT link_type, COUNT(*) FROM links GROUP BY link_type ORDER BY COUNT(*) DESC").fetchall()
        most_connected = self.db.execute("""
            SELECT i.title, i.item_type, COUNT(*) as cnt
            FROM (SELECT from_id as id FROM links UNION ALL SELECT to_id FROM links) x
            JOIN items i ON i.id = x.id
            GROUP BY x.id ORDER BY cnt DESC LIMIT 5
        """).fetchall()
        return {"total_links": total, "by_type": dict(by_type),
                "most_connected": [{"title": r[0], "type": r[1], "connections": r[2]} for r in most_connected]}

    # --- Deduplication ---

    def find_duplicates(self, threshold: float = 0.85) -> list[dict]:
        """Find potential duplicates using content hash similarity."""
        self.db.execute("DELETE FROM duplicates WHERE status='pending'")
        dupes = []

        # Group by type for efficiency
        for item_type in ['decision', 'learning', 'error', 'idea', 'follow-up', 'commitment']:
            items = self.db.execute(
                "SELECT id, title, content FROM items WHERE item_type=?", (item_type,)).fetchall()

            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    sim = _text_similarity(items[i][1] + " " + items[i][2],
                                          items[j][1] + " " + items[j][2])
                    if sim >= threshold:
                        self.db.execute(
                            "INSERT OR IGNORE INTO duplicates (item_a, item_b, similarity) VALUES (?,?,?)",
                            (items[i][0], items[j][0], sim))
                        dupes.append({
                            "a_id": items[i][0], "a_title": items[i][1],
                            "b_id": items[j][0], "b_title": items[j][1],
                            "similarity": round(sim, 3), "type": item_type,
                        })
        self.db.commit()
        return dupes

    def merge_duplicates(self) -> int:
        """Merge pending duplicates: keep the one with more content, delete the other."""
        pending = self.db.execute(
            "SELECT item_a, item_b FROM duplicates WHERE status='pending'").fetchall()
        merged = 0
        for a_id, b_id in pending:
            a = self.db.execute("SELECT id, content FROM items WHERE id=?", (a_id,)).fetchone()
            b = self.db.execute("SELECT id, content FROM items WHERE id=?", (b_id,)).fetchone()
            if not a or not b:
                continue
            # Keep the one with more content
            keep, remove = (a_id, b_id) if len(a[1]) >= len(b[1]) else (b_id, a_id)
            self.delete_item(remove)
            self.db.execute("UPDATE duplicates SET status='merged' WHERE item_a=? AND item_b=?", (a_id, b_id))
            merged += 1
        self.db.commit()
        return merged

    # --- Analytics ---

    def get_stats(self) -> dict:
        total = self.db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        by_type = dict(self.db.execute(
            "SELECT item_type, COUNT(*) FROM items GROUP BY item_type ORDER BY COUNT(*) DESC").fetchall())
        files = self.db.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
        tags = self.db.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        links = self.db.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        dupes = self.db.execute("SELECT COUNT(*) FROM duplicates WHERE status='pending'").fetchone()[0]
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        return {"total": total, "by_type": by_type, "files": files, "tags": tags,
                "links": links, "pending_dupes": dupes, "db_size_kb": db_size / 1024}

    def get_analytics(self) -> dict:
        """Detailed analytics dashboard."""
        stats = self.get_stats()

        # Activity by date (last 14 days)
        activity = dict(self.db.execute("""
            SELECT logged_date, COUNT(*) FROM items
            WHERE logged_date >= date('now', '-14 days') AND logged_date IS NOT NULL
            GROUP BY logged_date ORDER BY logged_date
        """).fetchall())

        # Top tags
        top_tags = self.db.execute("""
            SELECT t.name, COUNT(*) as cnt FROM tags t
            JOIN item_tags it ON t.id = it.tag_id
            GROUP BY t.name ORDER BY cnt DESC LIMIT 10
        """).fetchall()

        # Items by area
        by_area = dict(self.db.execute("""
            SELECT area, COUNT(*) FROM items WHERE area != '' AND area IS NOT NULL
            GROUP BY area ORDER BY COUNT(*) DESC
        """).fetchall())

        # Items by status
        by_status = dict(self.db.execute("""
            SELECT status, COUNT(*) FROM items
            GROUP BY status ORDER BY COUNT(*) DESC
        """).fetchall())

        # Source file distribution (top 10)
        top_sources = self.db.execute("""
            SELECT source_file, COUNT(*) FROM items
            GROUP BY source_file ORDER BY COUNT(*) DESC LIMIT 10
        """).fetchall()

        # Freshness: oldest and newest items
        oldest = self.db.execute(
            "SELECT logged_date, title FROM items WHERE logged_date IS NOT NULL ORDER BY logged_date LIMIT 1").fetchone()
        newest = self.db.execute(
            "SELECT logged_date, title FROM items WHERE logged_date IS NOT NULL ORDER BY logged_date DESC LIMIT 1").fetchone()

        return {
            **stats,
            "activity_14d": activity,
            "top_tags": [{"tag": r[0], "count": r[1]} for r in top_tags],
            "by_area": by_area,
            "by_status": by_status,
            "top_sources": [{"source": r[0], "count": r[1]} for r in top_sources],
            "oldest": {"date": oldest[0], "title": oldest[1]} if oldest else None,
            "newest": {"date": newest[0], "title": newest[1]} if newest else None,
        }

    # --- Pipeline ---

    def run_pipeline(self, workspace: Path) -> dict:
        """Full maintenance pipeline: index → dedup → links → report."""
        report = {"steps": [], "started_at": datetime.now().isoformat()}

        # Step 1: Incremental index
        t0 = time.time()
        changed = _do_incremental_index(self, workspace)
        report["steps"].append({"step": "index", "duration_s": round(time.time() - t0, 1), "changed": changed})

        # Step 2: Dedup
        t0 = time.time()
        dupes = self.find_duplicates(threshold=0.85)
        report["steps"].append({"step": "dedup", "duration_s": round(time.time() - t0, 1), "found": len(dupes)})

        # Step 3: Auto-link
        t0 = time.time()
        link_count = self.rebuild_links()
        report["steps"].append({"step": "links", "duration_s": round(time.time() - t0, 1), "links": link_count})

        # Step 4: Sync LR tags
        t0 = time.time()
        lr_count = self.sync_lr_tags(workspace)
        report["steps"].append({"step": "lr_sync", "duration_s": round(time.time() - t0, 1), "tagged": lr_count})

        # Step 5: Stats
        report["stats"] = self.get_stats()
        report["finished_at"] = datetime.now().isoformat()
        return report

    # --- Learning Review Integration ---

    def sync_lr_tags(self, workspace: Path) -> int:
        """Sync learning review SR state as tags on matching DB items.
        Reads learning-review-state.json + scans learnings for summaries,
        then tags matching DB items with sr:L0..L6 or sr:graduated.
        Returns count of items tagged."""
        lr_state_path = workspace / ".learnings" / "learning-review-state.json"
        if not lr_state_path.exists():
            return 0

        import json as _json
        state = _json.load(open(lr_state_path))
        sr_items = state.get("items", {})
        if not sr_items:
            return 0

        # Try to get summaries from learning_review scanner
        lr_summaries = {}
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("lr", workspace / "scripts" / "learning_review.py")
            lr_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lr_mod)
            scanned = lr_mod.scan_learnings()
            lr_summaries = {k: v.get("summary", "")[:50] for k, v in scanned.items()}
        except Exception:
            pass

        # Remove old sr: tags
        self.db.execute("""
            DELETE FROM item_tags WHERE tag_id IN (
                SELECT id FROM tags WHERE name LIKE 'sr:%'
            )
        """)

        count = 0
        for lr_id, sr in sr_items.items():
            # Strategy 1: match by LR ID in title/content
            row = self.db.execute(
                "SELECT id FROM items WHERE title LIKE ? OR content LIKE ? LIMIT 1",
                (f"%{lr_id}%", f"%{lr_id}%")).fetchone()

            # Strategy 2: match by summary text against learning/error items
            if not row and lr_id in lr_summaries and lr_summaries[lr_id]:
                summary = lr_summaries[lr_id]
                row = self.db.execute(
                    "SELECT id FROM items WHERE item_type IN ('learning','error') AND title LIKE ? LIMIT 1",
                    (f"%{summary}%",)).fetchone()

            if not row:
                continue

            item_id = row[0]
            tag_name = "sr:graduated" if sr.get("graduated") else f"sr:L{sr.get('level', 0)}"

            self.db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tid = self.db.execute("SELECT id FROM tags WHERE name=?", (tag_name,)).fetchone()[0]
            self.db.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (item_id, tid))
            count += 1

        self.db.commit()
        return count

    # --- Export ---

    def export_items(self, item_type=None) -> list[dict]:
        """Export items as list of dicts."""
        sql = "SELECT id, item_type, title, content, source_file, logged_date, area, priority, status FROM items"
        params = []
        if item_type:
            sql += " WHERE item_type=?"
            params.append(item_type)
        sql += " ORDER BY logged_date DESC, id DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [{"id": r[0], "type": r[1], "title": r[2], "content": r[3], "source": r[4],
                 "date": r[5], "area": r[6], "priority": r[7], "status": r[8]} for r in rows]

    # --- Source Tracking ---

    def get_by_source_type(self, source_type: str, limit: int = 20) -> list[dict]:
        """Query items by source type."""
        rows = self.db.execute("""
            SELECT id, item_type, title, logged_date, source_file, status
            FROM items WHERE source_type=? ORDER BY logged_date DESC LIMIT ?
        """, (source_type, limit)).fetchall()
        return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3], "source": r[4], "status": r[5]}
                for r in rows]

    def source_distribution(self) -> dict:
        """Show distribution of items by source type."""
        return dict(self.db.execute(
            "SELECT source_type, COUNT(*) FROM items GROUP BY source_type ORDER BY COUNT(*) DESC"
        ).fetchall())

    # --- Temporal Intelligence ---

    def record_access(self, item_id: int, context: str = ""):
        """Record that an item was accessed (search result clicked, context loaded, etc.)."""
        self.db.execute("INSERT INTO access_log (item_id, context) VALUES (?,?)", (item_id, context))
        self.db.execute("""
            UPDATE items SET access_count = access_count + 1,
                           last_accessed = datetime('now')
            WHERE id = ?
        """, (item_id,))
        self.db.commit()

    def get_stale_items(self, days: int = 90) -> list[dict]:
        """Find items that haven't been accessed or updated in N days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self.db.execute("""
            SELECT id, item_type, title, logged_date, status, access_count, last_accessed
            FROM items
            WHERE item_type NOT IN ('daily_note')
              AND (last_accessed IS NULL OR last_accessed < ?)
              AND (logged_date IS NULL OR logged_date < ?)
              AND status = 'active'
            ORDER BY logged_date
            LIMIT 20
        """, (cutoff, cutoff)).fetchall()
        return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3], "status": r[4],
                 "access_count": r[5], "last_accessed": r[6]} for r in rows]

    def get_hot_items(self, limit: int = 10) -> list[dict]:
        """Items most frequently accessed — these are the important ones."""
        rows = self.db.execute("""
            SELECT id, item_type, title, logged_date, access_count, last_accessed
            FROM items WHERE access_count > 0
            ORDER BY access_count DESC LIMIT ?
        """, (limit,)).fetchall()
        return [{"id": r[0], "type": r[1], "title": r[2], "date": r[3],
                 "access_count": r[4], "last_accessed": r[5]} for r in rows]

    def get_review_candidates(self) -> list[dict]:
        """Decisions older than 30 days that haven't been reviewed — might be stale."""
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        rows = self.db.execute("""
            SELECT id, title, logged_date, access_count
            FROM items
            WHERE item_type = 'decision'
              AND logged_date IS NOT NULL AND logged_date < ?
              AND status = 'active'
            ORDER BY logged_date
            LIMIT 10
        """, (cutoff,)).fetchall()
        return [{"id": r[0], "title": r[1], "date": r[2], "access_count": r[3]} for r in rows]

    # --- Cross-Session Context Bridge ---

    def get_session_context(self, max_items: int = 30) -> dict:
        """Generate startup context for a new session.
        Returns the most relevant current state from the DB,
        replacing static MEMORY.md for dynamic context."""
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        context = {}

        # 1. Recent decisions (last 7 days)
        context["recent_decisions"] = [r[0] for r in self.db.execute("""
            SELECT title FROM items WHERE item_type='decision'
            AND logged_date >= ? ORDER BY logged_date DESC LIMIT 10
        """, (week_ago,)).fetchall()]

        # 2. Active follow-ups
        context["active_followups"] = [{"title": r[0], "content": r[1]} for r in self.db.execute("""
            SELECT title, substr(content, 1, 150) FROM items
            WHERE item_type='follow-up' AND status='active'
            ORDER BY logged_date DESC LIMIT 10
        """).fetchall()]

        # 3. Active commitments
        context["active_commitments"] = [{"title": r[0], "content": r[1]} for r in self.db.execute("""
            SELECT title, substr(content, 1, 150) FROM items
            WHERE item_type='commitment' AND status='active'
            ORDER BY logged_date DESC LIMIT 5
        """).fetchall()]

        # 4. Active ideas
        context["active_ideas"] = [r[0] for r in self.db.execute("""
            SELECT title FROM items WHERE item_type='idea'
            AND status IN ('active', 'parked')
            ORDER BY id DESC LIMIT 5
        """).fetchall()]

        # 5. Recent learnings (last 7 days)
        context["recent_learnings"] = [{"title": r[0], "priority": r[1]} for r in self.db.execute("""
            SELECT title, priority FROM items
            WHERE item_type IN ('learning', 'error')
            AND logged_date >= ?
            ORDER BY logged_date DESC LIMIT 5
        """, (week_ago,)).fetchall()]

        # 6. People with recent mentions
        context["active_people"] = [r[0] for r in self.db.execute("""
            SELECT title FROM items WHERE item_type='person' AND status='active'
            ORDER BY id LIMIT 10
        """).fetchall()]

        # 7. Hot items (most accessed)
        hot = self.db.execute("""
            SELECT title, item_type, access_count FROM items
            WHERE access_count > 2 ORDER BY access_count DESC LIMIT 5
        """).fetchall()
        if hot:
            context["hot_items"] = [{"title": r[0], "type": r[1], "accesses": r[2]} for r in hot]

        # 8. Stale decisions needing review
        cutoff_30d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        stale_decisions = self.db.execute("""
            SELECT title, logged_date FROM items
            WHERE item_type='decision' AND logged_date < ? AND status='active'
            ORDER BY logged_date LIMIT 3
        """, (cutoff_30d,)).fetchall()
        if stale_decisions:
            context["stale_decisions"] = [{"title": r[0], "date": r[1]} for r in stale_decisions]

        # 9. Today's activity so far
        today_count = self.db.execute(
            "SELECT COUNT(*) FROM items WHERE logged_date=?", (today,)).fetchone()[0]
        context["today_items"] = today_count

        # 10. Brain health snapshot
        total = self.db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        links = self.db.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        context["brain_size"] = {"items": total, "links": links}

        # Record access for returned items (boosts their ranking over time)
        for row in self.db.execute("""
            SELECT id FROM items WHERE item_type IN ('follow-up','commitment')
            AND status='active' LIMIT 20
        """).fetchall():
            self.db.execute("""
                UPDATE items SET access_count = access_count + 1,
                               last_accessed = datetime('now')
                WHERE id = ?
            """, (row[0],))
        self.db.commit()

        return context

    def format_session_context(self) -> str:
        """Format session context as readable markdown for injection into agent prompt."""
        ctx = self.get_session_context()
        lines = ["## 🧠 Session Context (from Memory DB)", ""]

        if ctx.get("recent_decisions"):
            lines.append(f"**Recent decisions ({len(ctx['recent_decisions'])}):**")
            for d in ctx["recent_decisions"][:5]:
                lines.append(f"- {d}")
            lines.append("")

        if ctx.get("active_followups"):
            lines.append(f"**Active follow-ups ({len(ctx['active_followups'])}):**")
            for f in ctx["active_followups"]:
                lines.append(f"- {f['title']}")
            lines.append("")

        if ctx.get("active_commitments"):
            real_commitments = [c for c in ctx["active_commitments"] if c["title"] != "Fulfilled Date"]
            if real_commitments:
                lines.append(f"**Commitments ({len(real_commitments)}):**")
                for c in real_commitments:
                    # title is a date; extract meaningful summary from content
                    content = c.get("content", "")
                    parts = [p.strip() for p in content.split("|") if p.strip()]
                    # format: date | to | commitment | context
                    if len(parts) >= 3:
                        to = parts[1] if len(parts) > 1 else ""
                        commitment_text = parts[2] if len(parts) > 2 else parts[-1]
                        lines.append(f"- [{c['title']}] {to} — {commitment_text}")
                    else:
                        lines.append(f"- {content[:120]}")
                lines.append("")

        if ctx.get("recent_learnings"):
            lines.append(f"**Recent learnings:**")
            for l in ctx["recent_learnings"]:
                prio = "🔴" if l["priority"] == "critical" else "🟡" if l["priority"] == "high" else ""
                lines.append(f"- {prio} {l['title']}")
            lines.append("")

        if ctx.get("stale_decisions"):
            lines.append("**⚠️ Decisions needing review (>30 days):**")
            for s in ctx["stale_decisions"]:
                lines.append(f"- [{s['date']}] {s['title']}")
            lines.append("")

        if ctx.get("hot_items"):
            lines.append("**🔥 Frequently accessed:**")
            for h in ctx["hot_items"]:
                lines.append(f"- [{h['type']}] {h['title']} ({h['accesses']}×)")
            lines.append("")

        brain = ctx.get("brain_size", {})
        lines.append(f"_Brain: {brain.get('items', 0)} items, {brain.get('links', 0)} links, {ctx.get('today_items', 0)} today_")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Embeddings (module-level for reuse)
# ---------------------------------------------------------------------------

def _local_embedding(text: str) -> list[float]:
    vec = []
    for i in range(EMBEDDING_DIM):
        h = hashlib.sha256(f"{i}:{text.lower().strip()}".encode()).digest()
        val = (struct.unpack('f', h[:4])[0] % 2) - 1
        vec.append(val)
    mag = sum(v * v for v in vec) ** 0.5
    return [v / mag for v in vec] if mag > 0 else vec

_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        try:
            from google import genai
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not key: return None
            _gemini_client = genai.Client(api_key=key)
        except (ImportError, Exception):
            return None
    return _gemini_client

def _gemini_embedding(text: str) -> list[float]:
    global _last_api_call
    client = _get_gemini_client()
    if not client: return _local_embedding(text)
    now = time.time()
    if now - _last_api_call < _API_DELAY:
        time.sleep(_API_DELAY - (now - _last_api_call))
    _last_api_call = time.time()
    try:
        result = client.models.embed_content(
            model='gemini-embedding-001',
            contents=text.replace("\n", " ").strip()[:2000],
            config={'output_dimensionality': EMBEDDING_DIM})
        return list(result.embeddings[0].values)
    except Exception:
        return _local_embedding(text)

def _batch_gemini_embeddings(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    client = _get_gemini_client()
    if not client: return [_local_embedding(t) for t in texts]
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = [t.replace("\n", " ").strip()[:2000] for t in texts[i:i + batch_size]]
        try:
            result = client.models.embed_content(
                model='gemini-embedding-001', contents=batch,
                config={'output_dimensionality': EMBEDDING_DIM})
            all_vecs.extend([list(e.values) for e in result.embeddings])
            if i + batch_size < len(texts): time.sleep(0.1)
        except Exception:
            all_vecs.extend([_local_embedding(t) for t in texts[i:i + batch_size]])
    return all_vecs

def get_embedding(text: str) -> list[float]:
    return _gemini_embedding(text) if EMBEDDING_PROVIDER == "gemini" else _local_embedding(text)

def serialize_vec(vec: list[float]) -> bytes:
    return struct.pack(f'{len(vec)}f', *vec)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _text_similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity on word sets."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb: return 0.0
    return len(wa & wb) / len(wa | wb)

def file_hash(fp: Path) -> str:
    return hashlib.sha256(fp.read_bytes()).hexdigest()

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _detect_source_type(source_file: str) -> str:
    """Detect source type from file path."""
    if "memory/" in source_file:
        if re.search(r'\d{4}-\d{2}-\d{2}', source_file):
            return "daily_log"
        return "second_brain"
    elif ".learnings/" in source_file:
        return "learning_system"
    return "markdown"

def parse_decisions(content, src):
    items = []
    st = _detect_source_type(src)
    for line in content.split("\n"):
        m = re.match(r'\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)(?:\s+—\s+(.+))?$', line.strip())
        if m:
            # Detect if decision came from a conversation/meeting/email context
            reasoning = m[3] or ""
            decision_source = st
            if any(kw in reasoning.lower() for kw in ("meeting", "discussion", "call")):
                decision_source = "meeting"
            elif any(kw in reasoning.lower() for kw in ("email", "mail")):
                decision_source = "email"
            elif any(kw in reasoning.lower() for kw in ("user", "feedback", "correction")):
                decision_source = "conversation"
            items.append({"item_type": "decision", "title": m[2][:200],
                "content": f"{m[2]}\n\nReasoning: {reasoning}" if reasoning else m[2],
                "source_file": src, "logged_date": m[1], "status": "active",
                "source_type": decision_source})
    return items

def parse_learning_blocks(content, src):
    items = []
    st = _detect_source_type(src)
    for m in re.finditer(r'## \[((?:LRN|ERR)-\d{8}-\d{3})\]\s+(\S+)(.*?)(?=\n## \[|$)', content, re.DOTALL):
        eid, block = m[1], m[3]
        title, priority, status, area, logged, tags = "", "medium", "active", "", "", []
        for line in block.split("\n"):
            ls = line.strip()
            if ls.startswith("**Logged**:"): logged = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Priority**:"): priority = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Status**:"): status = ls.split(":", 1)[1].strip().strip("*")
            elif ls.startswith("**Area**:"): area = ls.split(":", 1)[1].strip().strip("*")
            elif not title and ls and not ls.startswith(("**", "###", "- ")): title = ls
        tm = re.search(r'Tags:\s*(.+)', block)
        if tm: tags = [t.strip() for t in tm[1].split(",")]
        dm = re.match(r'(\d{4}-\d{2}-\d{2})', logged) if logged else None
        # Detect source from block content
        lrn_source = st
        source_match = re.search(r'Source:\s*(\S+)', block)
        if source_match:
            s = source_match.group(1).lower()
            if "user_feedback" in s or "correction" in s: lrn_source = "conversation"
            elif "conversation" in s: lrn_source = "conversation"
        items.append({"item_type": "error" if eid.startswith("ERR") else "learning",
            "title": title[:200] or f"[{eid}]", "content": block.strip()[:2000],
            "source_file": src, "logged_date": dm[1] if dm else None,
            "area": area, "priority": priority, "status": status, "tags": tags,
            "source_type": lrn_source,
            "metadata_json": json.dumps({"entry_id": eid})})
    return items

def parse_people(content, src):
    items = []
    st = _detect_source_type(src)
    for s in re.split(r'\n(?=##[^#]|###[^#])', content):
        m = re.match(r'#{2,3}\s+(.+)', s.strip())
        if m and m[1].strip() not in ("Personal", "Active", "Archived"):
            items.append({"item_type": "person", "title": m[1].strip(),
                         "content": s.strip()[:1000], "source_file": src,
                         "status": "active", "source_type": st})
    return items

def parse_ideas(content, src):
    items = []
    src_type = _detect_source_type(src)
    for s in re.split(r'\n(?=###[^#])', content):
        m = re.match(r'###\s+(.+)', s.strip())
        if m and m[1].strip() != "Archived Ideas":
            st = "active"
            sm = re.search(r'\*\*Status:\*\*\s*(.+)', s)
            if sm:
                t = sm[1].lower()
                if "park" in t: st = "parked"
                elif "archiv" in t: st = "archived"
            items.append({"item_type": "idea", "title": m[1][:200],
                         "content": s.strip()[:1000], "source_file": src,
                         "status": st, "source_type": src_type})
    return items

def parse_table_rows(content, src, item_type):
    items = []
    st = _detect_source_type(src)
    for line in content.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[1] and not parts[1].startswith("---") and parts[1] not in ("Item", "Date", "—"):
            if parts[1] != "No active commitments":
                date = parts[1] if re.match(r'\d{4}-\d{2}-\d{2}', parts[1]) else (
                    parts[3] if len(parts) > 3 and re.match(r'\d{4}-\d{2}-\d{2}', parts[3]) else None)
                items.append({"item_type": item_type, "title": parts[1][:200],
                             "content": " | ".join(parts[1:]), "source_file": src,
                             "status": "active", "logged_date": date, "source_type": st})
    return items

def parse_daily_note(content, src):
    items = []
    dm = re.search(r'(\d{4}-\d{2}-\d{2})', src)
    date = dm[1] if dm else None
    for s in re.split(r'\n(?=## )', content):
        m = re.match(r'## (.+)', s.strip())
        if m:
            items.append({"item_type": "daily_note",
                "title": f"[{date}] {m[1]}" if date else m[1],
                "content": s.strip()[:2000], "source_file": src,
                "logged_date": date, "status": "active",
                "source_type": "daily_log",
                "metadata_json": json.dumps({"section": m[1].strip()})})
    return items

PARSERS = {
    "decisions": parse_decisions, "people": parse_people,
    "ideas": parse_ideas, "learnings": parse_learning_blocks,
    "errors": parse_learning_blocks,
    "commitments": lambda c, s: parse_table_rows(c, s, "commitment"),
    "follow-ups": lambda c, s: parse_table_rows(c, s, "follow-up"),
}

# ---------------------------------------------------------------------------
# Indexing functions
# ---------------------------------------------------------------------------

def _do_full_index(mem: GhostMemory, ws: Path) -> int:
    print("🔄 Full re-index starting...")
    mem.db.executescript("DELETE FROM item_tags;DELETE FROM links;DELETE FROM duplicates;DELETE FROM items_vec;DELETE FROM items;DELETE FROM file_index;")
    total = 0
    for key, rel in MEMORY_FILES.items():
        fp = ws / rel
        if not fp.exists(): continue
        items = PARSERS.get(key, parse_daily_note)(fp.read_text(encoding="utf-8"), rel)
        mem.index_items(items)
        mem.db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)",
                      (rel, file_hash(fp), len(items)))
        total += len(items)
        if items: print(f"  ✅ {rel}: {len(items)} items")
    for key, (dp, pat) in SCAN_DIRS.items():
        d = ws / dp
        if not d.exists(): continue
        for fp in sorted(d.glob(pat)):
            if fp.name == "README.md": continue
            rel = str(fp.relative_to(ws))
            parser = parse_learning_blocks if "learnings" in key else parse_daily_note
            items = parser(fp.read_text(encoding="utf-8"), rel)
            mem.index_items(items)
            mem.db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)",
                          (rel, file_hash(fp), len(items)))
            total += len(items)
            if items: print(f"  ✅ {rel}: {len(items)} items")
    mem.db.commit()
    print(f"\n✅ Indexed {total} items total")
    return total

def _do_incremental_index(mem: GhostMemory, ws: Path) -> int:
    changed = 0
    files = {}
    for key, rel in MEMORY_FILES.items():
        fp = ws / rel
        if fp.exists(): files[rel] = (key, fp)
    for key, (dp, pat) in SCAN_DIRS.items():
        d = ws / dp
        if not d.exists(): continue
        for fp in d.glob(pat):
            if fp.name == "README.md": continue
            files[str(fp.relative_to(ws))] = (key, fp)
    for rel, (key, fp) in files.items():
        h = file_hash(fp)
        row = mem.db.execute("SELECT hash FROM file_index WHERE path=?", (rel,)).fetchone()
        if row and row[0] == h: continue
        changed += 1
        for oid in [r[0] for r in mem.db.execute("SELECT id FROM items WHERE source_file=?", (rel,)).fetchall()]:
            mem.db.execute("DELETE FROM items_vec WHERE item_id=?", (oid,))
        mem.db.execute("DELETE FROM items WHERE source_file=?", (rel,))
        parser = PARSERS.get(key) or (parse_learning_blocks if "learnings" in key else parse_daily_note)
        items = parser(fp.read_text(encoding="utf-8"), rel)
        mem.index_items(items)
        mem.db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)", (rel, h, len(items)))
        print(f"  🔄 {rel}: {len(items)} items")
    mem.db.commit()
    return changed

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _format_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def main():
    if len(sys.argv) < 2:
        print(__doc__); return

    cmd = sys.argv[1]
    json_mode = "--json" in sys.argv

    try:
        import sqlite_vec
    except ImportError:
        print("❌ sqlite-vec not installed. Run: pip install sqlite-vec"); sys.exit(1)

    mem = GhostMemory()

    try:
        if cmd == "index":
            if "--incremental" in sys.argv:
                print("🔄 Incremental index...")
                changed = _do_incremental_index(mem, WORKSPACE)
                if changed == 0: print("  ℹ️  No files changed")
                else: print(f"\n✅ Re-indexed {changed} files")
            else:
                _do_full_index(mem, WORKSPACE)

        elif cmd == "search":
            if len(sys.argv) < 3: print("Usage: ghost_memory_db.py search \"query\" [fts|vec|hybrid]"); return
            query = sys.argv[2]
            mode = [a for a in sys.argv[3:] if a in ("fts", "vec", "hybrid")]
            mode = mode[0] if mode else "hybrid"
            results = {"fts": mem.search_fts, "vec": mem.search_vector, "hybrid": mem.search_hybrid}[mode](query)
            if json_mode:
                _format_json(results)
            else:
                for r in (results or []):
                    ml = f" [{r.get('match', '')}]" if 'match' in r else ""
                    d = f" (dist:{r['distance']})" if 'distance' in r else ""
                    print(f"  [{r['type']}] {r['title']}{ml}{d}")
                    print(f"    Date: {r.get('date', '-')} | Source: {r['source']}")
                    if r.get('snippet'): print(f"    {r['snippet'][:150]}...")
                    print()
                if not results: print("No results found.")

        elif cmd == "sql":
            if len(sys.argv) < 3: print("Usage: ghost_memory_db.py sql \"SELECT ...\""); return
            try:
                rows = mem.db.execute(sys.argv[2]).fetchall()
                if json_mode:
                    _format_json([list(r) for r in rows])
                else:
                    for row in rows: print(" | ".join(str(v) for v in row))
            except Exception as e:
                print(f"SQL error: {e}")

        elif cmd == "query":
            if len(sys.argv) < 3: print("Usage: ghost_memory_db.py query <type> [--project X] [--days N]"); return
            kw = {}; args = sys.argv[3:]; i = 0
            while i < len(args):
                if args[i].startswith("--") and i + 1 < len(args) and args[i] != "--json":
                    k = args[i][2:]; kw[k] = int(args[i + 1]) if k in ("days", "limit") else args[i + 1]; i += 2
                else: i += 1
            results = mem.structured_query(sys.argv[2], **kw)
            if json_mode:
                _format_json(results)
            else:
                for r in (results or []):
                    print(f"  [{r.get('date', '-')}] {r['title']}\n    Source: {r['source']}")
                if not results: print("No results.")

        elif cmd == "stats":
            analytics = mem.get_analytics()
            if json_mode:
                _format_json(analytics)
            else:
                print(f"📊 Ghost Memory DB")
                print(f"   Size: {analytics['db_size_kb']:.1f}KB | Embedding: {EMBEDDING_PROVIDER} ({EMBEDDING_DIM}d)")
                print(f"   Items: {analytics['total']} | Files: {analytics['files']} | Tags: {analytics['tags']} | Links: {analytics['links']}")
                if analytics['pending_dupes']:
                    print(f"   ⚠️  Pending duplicates: {analytics['pending_dupes']}")
                print(f"\n   📦 By type:")
                for t, c in analytics['by_type'].items():
                    print(f"     {t}: {c}")
                if analytics['by_area']:
                    print(f"\n   🏷️ By area:")
                    for a, c in analytics['by_area'].items():
                        print(f"     {a}: {c}")
                if analytics['top_tags']:
                    print(f"\n   🏷️ Top tags:")
                    for t in analytics['top_tags'][:5]:
                        print(f"     {t['tag']}: {t['count']}")
                if analytics['activity_14d']:
                    print(f"\n   📈 Activity (14 days):")
                    for date, cnt in analytics['activity_14d'].items():
                        bar = "█" * min(cnt, 20)
                        print(f"     {date}: {bar} {cnt}")
                if analytics['oldest']:
                    print(f"\n   📅 Range: {analytics['oldest']['date']} → {analytics['newest']['date']}")

        elif cmd == "dedup":
            dupes = mem.find_duplicates()
            if json_mode:
                _format_json(dupes)
            elif dupes:
                print(f"🔍 Found {len(dupes)} potential duplicates:")
                for d in dupes:
                    print(f"  [{d['type']}] {d['similarity']:.0%} match:")
                    print(f"    A: #{d['a_id']} {d['a_title'][:60]}")
                    print(f"    B: #{d['b_id']} {d['b_title'][:60]}")
                    print()
                if "--merge" in sys.argv:
                    merged = mem.merge_duplicates()
                    print(f"✅ Merged {merged} duplicates")
            else:
                print("✅ No duplicates found")

        elif cmd == "links":
            if "--rebuild" in sys.argv:
                count = mem.rebuild_links()
                print(f"✅ Built {count} links")
            graph = mem.get_graph_stats()
            if json_mode:
                _format_json(graph)
            else:
                print(f"🕸️ Knowledge Graph: {graph['total_links']} links")
                if graph['by_type']:
                    print(f"   By type:")
                    for t, c in graph['by_type'].items():
                        print(f"     {t}: {c}")
                if graph['most_connected']:
                    print(f"   Most connected:")
                    for m in graph['most_connected']:
                        print(f"     [{m['type']}] {m['title'][:50]} ({m['connections']} links)")

        elif cmd == "pipeline":
            report = mem.run_pipeline(WORKSPACE)
            if json_mode:
                _format_json(report)
            else:
                print("🔧 Pipeline complete:")
                for step in report["steps"]:
                    detail = step.get("changed", step.get("found", step.get("links", "")))
                    print(f"  {step['step']}: {detail} ({step['duration_s']}s)")
                s = report["stats"]
                print(f"\n📊 Items: {s['total']} | Links: {s['links']} | Dupes: {s['pending_dupes']}")

        elif cmd == "export":
            item_type = None
            for a in sys.argv[2:]:
                if not a.startswith("--"): item_type = a; break
            data = mem.export_items(item_type)
            _format_json(data)

        elif cmd == "context":
            if json_mode:
                _format_json(mem.get_session_context())
            else:
                print(mem.format_session_context())

        elif cmd == "temporal":
            if "--stale" in sys.argv:
                stale = mem.get_stale_items(days=90)
                if json_mode:
                    _format_json(stale)
                elif stale:
                    print(f"📦 {len(stale)} stale items (>90 days, no access):")
                    for s in stale:
                        print(f"  [{s['type']}] {s['title'][:60]}")
                        print(f"    Date: {s.get('date', '-')} | Accesses: {s['access_count']}")
                else:
                    print("✅ No stale items")
            elif "--hot" in sys.argv:
                hot = mem.get_hot_items()
                if json_mode:
                    _format_json(hot)
                elif hot:
                    print(f"🔥 Top {len(hot)} most accessed items:")
                    for h in hot:
                        print(f"  [{h['type']}] {h['title'][:60]} ({h['access_count']}× accessed)")
                else:
                    print("ℹ️  No items accessed yet")
            else:
                # Full temporal report
                review = mem.get_review_candidates()
                stale = mem.get_stale_items(days=90)
                hot = mem.get_hot_items(limit=5)
                sources = mem.source_distribution()
                if json_mode:
                    _format_json({"review_candidates": review, "stale": stale, "hot": hot, "sources": sources})
                else:
                    print("⏰ Temporal Intelligence Report")
                    print(f"\n📊 Source distribution:")
                    for src, cnt in sources.items():
                        print(f"  {src}: {cnt}")
                    if review:
                        print(f"\n🔍 Decisions to review ({len(review)}):")
                        for r in review:
                            print(f"  [{r['date']}] {r['title'][:60]} (accessed {r['access_count']}×)")
                    if hot:
                        print(f"\n🔥 Hot items:")
                        for h in hot:
                            print(f"  [{h['type']}] {h['title'][:50]} ({h['access_count']}×)")
                    if stale:
                        print(f"\n📦 Stale items ({len(stale)}):")
                        for s in stale[:5]:
                            print(f"  [{s['type']}] {s['title'][:60]}")
                    elif not stale:
                        print(f"\n✅ No stale items")

        else:
            print(f"Unknown: {cmd}"); print(__doc__)
    finally:
        mem.close()

if __name__ == "__main__":
    main()
