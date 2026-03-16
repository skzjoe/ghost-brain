#!/usr/bin/env python3
"""
Ghost Brain — SQLite + sqlite-vec Memory Layer

Indexes second-brain markdown files into a searchable SQLite database with
vector embeddings for semantic search and full SQL for structured queries.

Requires: pip install sqlite-vec
Optional: pip install google-genai (for Gemini semantic embeddings, free tier)

Usage:
  ghost_memory_db.py index              # Full re-index of all memory files
  ghost_memory_db.py index --incremental # Only index changed files
  ghost_memory_db.py search "query"      # Hybrid search (FTS + vector)
  ghost_memory_db.py search "query" fts  # Full-text search only
  ghost_memory_db.py search "query" vec  # Vector similarity only
  ghost_memory_db.py sql "SELECT ..."    # Raw SQL query
  ghost_memory_db.py stats              # Show database statistics
  ghost_memory_db.py query decision --project NAME --days 30  # Structured query
"""

import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
    os.path.expanduser("~/.openclaw/workspace")))
DB_PATH = WORKSPACE / ".local" / "ghost_memory.db"

# Embedding config — auto-detect provider
# If GEMINI_API_KEY exists → Gemini (free, semantic), otherwise → local hash (offline, basic)
_has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
EMBEDDING_PROVIDER = os.environ.get("GHOST_EMBEDDING_PROVIDER",
    "gemini" if _has_gemini else "local")
EMBEDDING_DIM = int(os.environ.get("GHOST_EMBEDDING_DIM",
    "256" if EMBEDDING_PROVIDER == "gemini" else "64"))

# Second brain files to index
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

# Rate limiting for API calls
_last_api_call = 0
_API_DELAY = 0.05  # 50ms between calls

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
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


def init_schema(db):
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
            path TEXT PRIMARY KEY, hash TEXT NOT NULL,
            last_indexed TEXT DEFAULT (datetime('now')), item_count INTEGER DEFAULT 0
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
        CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);
        CREATE INDEX IF NOT EXISTS idx_items_date ON items(logged_date);
        CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_file);
        CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
    """)
    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS items_vec USING vec0(
            item_id INTEGER PRIMARY KEY, embedding float[{EMBEDDING_DIM}]
        )
    """)
    db.commit()

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def _local_embedding(text: str) -> list[float]:
    """Deterministic hash-based embedding (zero-cost, offline). Not semantic."""
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
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                return None
            _gemini_client = genai.Client(api_key=key)
        except ImportError:
            return None
        except Exception:
            return None
    return _gemini_client

def _gemini_embedding(text: str) -> list[float]:
    global _last_api_call
    client = _get_gemini_client()
    if not client:
        return _local_embedding(text)
    now = time.time()
    if now - _last_api_call < _API_DELAY:
        time.sleep(_API_DELAY - (now - _last_api_call))
    _last_api_call = time.time()
    try:
        result = client.models.embed_content(
            model='gemini-embedding-001',
            contents=text.replace("\n", " ").strip()[:2000],
            config={'output_dimensionality': EMBEDDING_DIM}
        )
        return list(result.embeddings[0].values)
    except Exception:
        return _local_embedding(text)

def _batch_gemini_embeddings(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    client = _get_gemini_client()
    if not client:
        return [_local_embedding(t) for t in texts]
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = [t.replace("\n", " ").strip()[:2000] for t in texts[i:i+batch_size]]
        try:
            result = client.models.embed_content(
                model='gemini-embedding-001', contents=batch,
                config={'output_dimensionality': EMBEDDING_DIM}
            )
            all_vecs.extend([list(e.values) for e in result.embeddings])
            if i + batch_size < len(texts):
                time.sleep(0.1)
        except Exception:
            all_vecs.extend([_local_embedding(t) for t in texts[i:i+batch_size]])
    return all_vecs

def get_embedding(text: str) -> list[float]:
    if EMBEDDING_PROVIDER == "gemini":
        return _gemini_embedding(text)
    return _local_embedding(text)

def serialize_vec(vec: list[float]) -> bytes:
    return struct.pack(f'{len(vec)}f', *vec)

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_decisions(content, src):
    items = []
    for line in content.split("\n"):
        m = re.match(r'\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)(?:\s+—\s+(.+))?$', line.strip())
        if m:
            items.append({"item_type": "decision", "title": m[2][:200],
                "content": f"{m[2]}\n\nReasoning: {m[3]}" if m[3] else m[2],
                "source_file": src, "logged_date": m[1], "status": "active"})
    return items

def parse_learning_blocks(content, src):
    items = []
    for m in re.finditer(r'## \[((?:LRN|ERR)-\d{8}-\d{3})\]\s+(\S+)(.*?)(?=\n## \[|$)', content, re.DOTALL):
        eid, block = m[1], m[3]
        title, priority, status, area, logged, tags = "", "medium", "active", "", "", []
        for line in block.split("\n"):
            ls = line.strip()
            if ls.startswith("**Logged**:"): logged = ls.split(":",1)[1].strip().strip("*")
            elif ls.startswith("**Priority**:"): priority = ls.split(":",1)[1].strip().strip("*")
            elif ls.startswith("**Status**:"): status = ls.split(":",1)[1].strip().strip("*")
            elif ls.startswith("**Area**:"): area = ls.split(":",1)[1].strip().strip("*")
            elif not title and ls and not ls.startswith(("**","###","- ")): title = ls
        tm = re.search(r'Tags:\s*(.+)', block)
        if tm: tags = [t.strip() for t in tm[1].split(",")]
        dm = re.match(r'(\d{4}-\d{2}-\d{2})', logged) if logged else None
        items.append({"item_type": "error" if eid.startswith("ERR") else "learning",
            "title": title[:200] or f"[{eid}]", "content": block.strip()[:2000],
            "source_file": src, "logged_date": dm[1] if dm else None,
            "area": area, "priority": priority, "status": status, "tags": tags,
            "metadata_json": json.dumps({"entry_id": eid})})
    return items

def parse_people(content, src):
    items = []
    for s in re.split(r'\n(?=##[^#]|###[^#])', content):
        m = re.match(r'#{2,3}\s+(.+)', s.strip())
        if m and m[1].strip() not in ("Personal","Active","Archived"):
            items.append({"item_type":"person","title":m[1].strip(),"content":s.strip()[:1000],"source_file":src,"status":"active"})
    return items

def parse_ideas(content, src):
    items = []
    for s in re.split(r'\n(?=###[^#])', content):
        m = re.match(r'###\s+(.+)', s.strip())
        if m and m[1].strip() != "Archived Ideas":
            st = "active"
            sm = re.search(r'\*\*Status:\*\*\s*(.+)', s)
            if sm:
                t = sm[1].lower()
                if "park" in t: st = "parked"
                elif "archiv" in t: st = "archived"
            items.append({"item_type":"idea","title":m[1][:200],"content":s.strip()[:1000],"source_file":src,"status":st})
    return items

def parse_table_rows(content, src, item_type):
    items = []
    for line in content.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[1] and not parts[1].startswith("---") and parts[1] not in ("Item","Date","—"):
            if parts[1] != "No active commitments":
                date = parts[1] if re.match(r'\d{4}-\d{2}-\d{2}', parts[1]) else (parts[3] if len(parts)>3 and re.match(r'\d{4}-\d{2}-\d{2}', parts[3]) else None)
                items.append({"item_type":item_type,"title":parts[1][:200],"content":" | ".join(parts[1:]),"source_file":src,"status":"active","logged_date":date})
    return items

def parse_daily_note(content, src):
    items = []
    dm = re.search(r'(\d{4}-\d{2}-\d{2})', src)
    date = dm[1] if dm else None
    for s in re.split(r'\n(?=## )', content):
        m = re.match(r'## (.+)', s.strip())
        if m:
            items.append({"item_type":"daily_note","title":f"[{date}] {m[1]}" if date else m[1],
                "content":s.strip()[:2000],"source_file":src,"logged_date":date,"status":"active",
                "metadata_json":json.dumps({"section":m[1].strip()})})
    return items

# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def file_hash(fp): return hashlib.sha256(fp.read_bytes()).hexdigest()

PARSERS = {
    "decisions": parse_decisions, "people": parse_people,
    "ideas": parse_ideas, "learnings": parse_learning_blocks,
    "errors": parse_learning_blocks,
    "commitments": lambda c,s: parse_table_rows(c,s,"commitment"),
    "follow-ups": lambda c,s: parse_table_rows(c,s,"follow-up"),
}

def index_file(db, items):
    if not items: return
    texts = [f"{i['title']} {i['content'][:500]}" for i in items]
    vecs = _batch_gemini_embeddings(texts) if EMBEDDING_PROVIDER == "gemini" and len(items) > 1 else [get_embedding(t) for t in texts]
    for item, vec in zip(items, vecs):
        cur = db.execute("""INSERT INTO items (item_type,title,content,source_file,source_hash,logged_date,area,priority,status,metadata_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (item["item_type"],item["title"],item["content"],item["source_file"],
             hashlib.sha256(item["content"].encode()).hexdigest()[:16],
             item.get("logged_date"),item.get("area",""),item.get("priority",""),
             item.get("status","active"),item.get("metadata_json","")))
        iid = cur.lastrowid
        for tag in item.get("tags",[]):
            if not tag: continue
            db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)",(tag,))
            tid = db.execute("SELECT id FROM tags WHERE name=?",(tag,)).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO item_tags (item_id,tag_id) VALUES (?,?)",(iid,tid))
        db.execute("INSERT INTO items_vec (item_id,embedding) VALUES (?,?)",(iid,serialize_vec(vec)))

def full_index(db, ws):
    print("🔄 Full re-index starting...")
    db.executescript("DELETE FROM item_tags;DELETE FROM links;DELETE FROM items_vec;DELETE FROM items;DELETE FROM file_index;")
    total = 0
    for key, rel in MEMORY_FILES.items():
        fp = ws / rel
        if not fp.exists(): continue
        items = PARSERS.get(key, parse_daily_note)(fp.read_text(encoding="utf-8"), rel)
        index_file(db, items)
        db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)",(rel,file_hash(fp),len(items)))
        total += len(items)
        if items: print(f"  ✅ {rel}: {len(items)} items")
    for key,(dp,pat) in SCAN_DIRS.items():
        d = ws / dp
        if not d.exists(): continue
        for fp in sorted(d.glob(pat)):
            if fp.name == "README.md": continue
            rel = str(fp.relative_to(ws))
            parser = parse_learning_blocks if "learnings" in key else parse_daily_note
            items = parser(fp.read_text(encoding="utf-8"), rel)
            index_file(db, items)
            db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)",(rel,file_hash(fp),len(items)))
            total += len(items)
            if items: print(f"  ✅ {rel}: {len(items)} items")
    db.commit()
    print(f"\n✅ Indexed {total} items total")

def incremental_index(db, ws):
    print("🔄 Incremental index...")
    changed = 0
    files = {}
    for key,rel in MEMORY_FILES.items():
        fp = ws/rel
        if fp.exists(): files[rel] = (key, fp)
    for key,(dp,pat) in SCAN_DIRS.items():
        d = ws/dp
        if not d.exists(): continue
        for fp in d.glob(pat):
            if fp.name == "README.md": continue
            files[str(fp.relative_to(ws))] = (key, fp)
    for rel,(key,fp) in files.items():
        h = file_hash(fp)
        row = db.execute("SELECT hash FROM file_index WHERE path=?",(rel,)).fetchone()
        if row and row[0] == h: continue
        changed += 1
        for oid in [r[0] for r in db.execute("SELECT id FROM items WHERE source_file=?",(rel,)).fetchall()]:
            db.execute("DELETE FROM items_vec WHERE item_id=?",(oid,))
        db.execute("DELETE FROM items WHERE source_file=?",(rel,))
        parser = PARSERS.get(key) or (parse_learning_blocks if "learnings" in key else parse_daily_note)
        items = parser(fp.read_text(encoding="utf-8"), rel)
        index_file(db, items)
        db.execute("INSERT OR REPLACE INTO file_index (path,hash,item_count) VALUES (?,?,?)",(rel,h,len(items)))
        print(f"  🔄 {rel}: {len(items)} items")
    db.commit()
    print("  ℹ️  No files changed" if not changed else f"\n✅ Re-indexed {changed} files")

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_fts(db, q, limit=10):
    return [{"id":r[0],"type":r[1],"title":r[2],"date":r[3],"source":r[4],"status":r[5],"snippet":r[6]}
        for r in db.execute("""SELECT i.id,i.item_type,i.title,i.logged_date,i.source_file,i.status,
            snippet(items_fts,1,'→','←','...',30) FROM items_fts f JOIN items i ON i.id=f.rowid
            WHERE items_fts MATCH ? ORDER BY rank LIMIT ?""",(q,limit)).fetchall()]

def search_vector(db, q, limit=10):
    vec = get_embedding(q)
    return [{"id":r[0],"distance":round(r[1],4),"type":r[2],"title":r[3],"date":r[4],"source":r[5],"status":r[6],"snippet":r[7]}
        for r in db.execute("""SELECT v.item_id,v.distance,i.item_type,i.title,i.logged_date,
            i.source_file,i.status,substr(i.content,1,200) FROM items_vec v JOIN items i ON i.id=v.item_id
            WHERE embedding MATCH ? AND k=? ORDER BY v.distance""",(serialize_vec(vec),limit)).fetchall()]

def search_hybrid(db, q, limit=10):
    seen = {r["id"]:{**r,"match":"fts"} for r in search_fts(db,q,limit*2)}
    for r in search_vector(db,q,limit*2):
        if r["id"] in seen: seen[r["id"]]["match"] = "both"
        else: seen[r["id"]] = {**r,"match":"vec"}
    return sorted(seen.values(), key=lambda x:(0 if x["match"]=="both" else 1 if x["match"]=="fts" else 2))[:limit]

def structured_query(db, item_type, project=None, days=None, status=None, limit=20):
    sql,p = "SELECT id,item_type,title,logged_date,source_file,status,substr(content,1,200) FROM items WHERE item_type=?",[item_type]
    if project: sql+=" AND (title LIKE ? OR content LIKE ?)"; p+=[f"%{project}%"]*2
    if days: sql+=" AND logged_date>=?"; p.append((datetime.now()-timedelta(days=days)).strftime("%Y-%m-%d"))
    if status: sql+=" AND status=?"; p.append(status)
    sql+=" ORDER BY logged_date DESC LIMIT ?"; p.append(limit)
    return [{"id":r[0],"type":r[1],"title":r[2],"date":r[3],"source":r[4],"status":r[5],"snippet":r[6]} for r in db.execute(sql,p).fetchall()]

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def show_stats(db):
    total = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    by_type = db.execute("SELECT item_type,COUNT(*) FROM items GROUP BY item_type ORDER BY COUNT(*) DESC").fetchall()
    files = db.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
    tags = db.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    sz = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    print(f"📊 Ghost Memory DB\n   Size: {sz/1024:.1f}KB | Embedding: {EMBEDDING_PROVIDER} ({EMBEDDING_DIM}d)")
    print(f"   Items: {total} | Files: {files} | Tags: {tags}")
    for t,c in by_type: print(f"   {t}: {c}")

def main():
    if len(sys.argv) < 2: print(__doc__); return
    cmd = sys.argv[1]
    db = get_db(); init_schema(db)

    if cmd == "index":
        (incremental_index if "--incremental" in sys.argv else full_index)(db, WORKSPACE)
    elif cmd == "search":
        if len(sys.argv)<3: print("Usage: ghost_memory_db.py search \"query\""); return
        mode = sys.argv[3] if len(sys.argv)>3 else "hybrid"
        results = {"fts":search_fts,"vec":search_vector}.get(mode,search_hybrid)(db,sys.argv[2])
        for r in (results or []):
            ml = f" [{r.get('match','')}]" if 'match' in r else ""
            d = f" (dist:{r['distance']})" if 'distance' in r else ""
            print(f"  [{r['type']}] {r['title']}{ml}{d}")
            print(f"    Date: {r.get('date','-')} | Source: {r['source']}")
            if r.get('snippet'): print(f"    {r['snippet'][:150]}...")
            print()
        if not results: print("No results found.")
    elif cmd == "sql":
        if len(sys.argv)<3: print("Usage: ghost_memory_db.py sql \"SELECT ...\""); return
        try:
            for row in db.execute(sys.argv[2]).fetchall(): print(" | ".join(str(v) for v in row))
        except Exception as e: print(f"SQL error: {e}")
    elif cmd == "query":
        if len(sys.argv)<3: print("Usage: ghost_memory_db.py query <type> [--project X] [--days N]"); return
        kw={}; args=sys.argv[3:]; i=0
        while i<len(args):
            if args[i].startswith("--") and i+1<len(args):
                k=args[i][2:]; kw[k]=int(args[i+1]) if k in("days","limit") else args[i+1]; i+=2
            else: i+=1
        results = structured_query(db, sys.argv[2], **kw)
        for r in (results or []): print(f"  [{r.get('date','-')}] {r['title']}\n    Source: {r['source']}")
        if not results: print("No results.")
    elif cmd == "stats": show_stats(db)
    else: print(f"Unknown: {cmd}"); print(__doc__)
    db.close()

if __name__ == "__main__": main()
