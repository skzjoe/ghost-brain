#!/usr/bin/env python3
"""
ghost_todos.py — Intra-session todo store for Ghost Brain.

Lightweight JSON-backed todo list that persists within a session and survives
context compression. Ghost uses this for multi-step tasks (3+ steps) to avoid
losing track of pending sub-tasks.

Backed by: .local/todos.json (cleared on /new or explicit --clear)

Usage:
    python3 scripts/ghost_todos.py add "Fix merge script"
    python3 scripts/ghost_todos.py add "Run tests" --tag testing
    python3 scripts/ghost_todos.py list
    python3 scripts/ghost_todos.py done 1
    python3 scripts/ghost_todos.py status          # compact summary for context
    python3 scripts/ghost_todos.py clear           # wipe all (use on /new)

From Python:
    from ghost_todos import TodoStore
    store = TodoStore()
    store.add("Fix merge script")
    store.done(1)
    print(store.status())
"""

import os, sys, json, argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field

from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace
TODOS_FILE = _paths.local_dir / "todos.json"


@dataclass
class TodoItem:
    id: int
    text: str
    tag: str = ""
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    done_at: str = ""


class TodoStore:
    def __init__(self, path: Path = TODOS_FILE):
        self.path = path
        self._items: list[TodoItem] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self._items = [TodoItem(**d) for d in data.get("items", [])]
            except Exception:
                self._items = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"items": [asdict(i) for i in self._items]},
            ensure_ascii=False, indent=2
        ))

    def _next_id(self) -> int:
        return max((i.id for i in self._items), default=0) + 1

    def add(self, text: str, tag: str = "") -> TodoItem:
        item = TodoItem(id=self._next_id(), text=text, tag=tag)
        self._items.append(item)
        self._save()
        return item

    def done(self, item_id: int) -> TodoItem | None:
        for item in self._items:
            if item.id == item_id and not item.done:
                item.done = True
                item.done_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save()
                return item
        return None

    def remove(self, item_id: int) -> bool:
        before = len(self._items)
        self._items = [i for i in self._items if i.id != item_id]
        if len(self._items) < before:
            self._save()
            return True
        return False

    def clear(self, done_only: bool = False):
        if done_only:
            self._items = [i for i in self._items if not i.done]
        else:
            self._items = []
        self._save()

    def pending(self) -> list[TodoItem]:
        return [i for i in self._items if not i.done]

    def all_items(self) -> list[TodoItem]:
        return list(self._items)

    def status(self) -> str:
        """Compact one-line summary for embedding in Ghost context."""
        p = self.pending()
        done = [i for i in self._items if i.done]
        if not self._items:
            return "todos: empty"
        parts = []
        if p:
            pending_labels = ", ".join(f"[{i.id}] {i.text}" for i in p[:5])
            if len(p) > 5:
                pending_labels += f" (+{len(p)-5} more)"
            parts.append(f"pending: {pending_labels}")
        if done:
            parts.append(f"done: {len(done)}")
        return "todos → " + " | ".join(parts)

    def format_list(self) -> str:
        if not self._items:
            return "  (empty)"
        lines = []
        for item in self._items:
            check = "✅" if item.done else "⬜"
            tag = f" [{item.tag}]" if item.tag else ""
            lines.append(f"  {check} {item.id}. {item.text}{tag}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Ghost session todo store")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a todo item")
    p_add.add_argument("text")
    p_add.add_argument("--tag", default="")

    p_done = sub.add_parser("done", help="Mark item done by ID")
    p_done.add_argument("id", type=int)

    p_rm = sub.add_parser("remove", help="Remove item by ID")
    p_rm.add_argument("id", type=int)

    sub.add_parser("list", help="List all todos")
    sub.add_parser("status", help="Compact status summary")

    p_clear = sub.add_parser("clear", help="Clear todos")
    p_clear.add_argument("--done-only", action="store_true", help="Clear only completed items")

    args = parser.parse_args()
    store = TodoStore()

    if args.cmd == "add":
        item = store.add(args.text, args.tag)
        print(f"  ⬜ Added [{item.id}] {item.text}")

    elif args.cmd == "done":
        item = store.done(args.id)
        if item:
            print(f"  ✅ Done [{item.id}] {item.text}")
        else:
            print(f"  Item {args.id} not found or already done.", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "remove":
        ok = store.remove(args.id)
        print(f"  {'Removed' if ok else 'Not found'}: {args.id}")

    elif args.cmd == "list":
        pending = store.pending()
        print(f"\n📋 Todos ({len(pending)} pending / {len(store.all_items())} total)\n")
        print(store.format_list())
        print()

    elif args.cmd == "status":
        print(store.status())

    elif args.cmd == "clear":
        store.clear(done_only=args.done_only)
        label = "completed" if args.done_only else "all"
        print(f"  Cleared {label} todos.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
