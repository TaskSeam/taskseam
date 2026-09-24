"""SQLite storage for explicit task events and versioned checkpoints."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id():
    return uuid.uuid4().hex[:12]


class Store:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA busy_timeout = 5000")
        schema_version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if schema_version > 2:
            self.db.close()
            raise ValueError("Database was created by a newer TaskSeam version")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                source TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                kind TEXT NOT NULL CHECK (kind IN ('decision','question','constraint')),
                body TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES events(id),
                supersedes TEXT REFERENCES items(id), created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                created_at TEXT NOT NULL, snapshot TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS resolutions (
                question_id TEXT PRIMARY KEY REFERENCES items(id),
                resolution_item_id TEXT NOT NULL UNIQUE REFERENCES items(id),
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS events_task_idx ON events(task_id);
            CREATE INDEX IF NOT EXISTS items_task_idx ON items(task_id);
            CREATE INDEX IF NOT EXISTS checkpoints_task_idx ON checkpoints(task_id);
            PRAGMA user_version = 2;
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def create_task(self, title):
        task_id = _id()
        with self.db:
            self.db.execute("INSERT INTO tasks VALUES (?, ?, ?)", (task_id, title, _now()))
        return task_id

    def task(self, task_id):
        row = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown task: " + task_id)
        return dict(row)

    def tasks(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM tasks ORDER BY created_at DESC")]

    def events(self, task_id):
        self.task(task_id)
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM events WHERE task_id = ? ORDER BY created_at, rowid", (task_id,)
        )]

    def add_event(self, task_id, source, body):
        self.task(task_id)
        event_id = _id()
        with self.db:
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                            (event_id, task_id, source, body, _now()))
        return event_id

    def add_item(self, task_id, kind, body, source, supersedes=None):
        self.task(task_id)
        if kind not in ("decision", "question", "constraint"):
            raise ValueError("Invalid item kind: " + kind)
        if supersedes:
            old = self.db.execute("SELECT task_id, kind FROM items WHERE id = ?", (supersedes,)).fetchone()
            if old is None or old["task_id"] != task_id or old["kind"] != kind:
                raise ValueError("Superseded item must exist in the same task and have the same kind")
            if self.db.execute("SELECT 1 FROM items WHERE supersedes = ?", (supersedes,)).fetchone():
                raise ValueError("Item has already been superseded")
        event_id, item_id = _id(), _id()
        with self.db:
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                            (event_id, task_id, source, body, _now()))
            self.db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (item_id, task_id, kind, body, event_id, supersedes, _now()))
        return item_id

    def import_items(self, task_id, source, evidence, items):
        self.task(task_id)
        if not isinstance(items, list) or not items:
            raise ValueError("Import packet must contain at least one item")
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each imported item must be an object")
            kind, body = item.get("kind"), item.get("body")
            if kind not in ("decision", "question", "constraint"):
                raise ValueError("Invalid imported item kind: " + str(kind))
            if not isinstance(body, str) or not body.strip():
                raise ValueError("Each imported item requires a non-empty body")
            normalized.append((kind, body.strip()))
        event_id = _id()
        created = _now()
        item_ids = []
        with self.db:
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                            (event_id, task_id, source, evidence, created))
            for kind, body in normalized:
                item_id = _id()
                self.db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (item_id, task_id, kind, body, event_id, None, created))
                item_ids.append(item_id)
        return {"event_id": event_id, "item_ids": item_ids}

    def items(self, task_id):
        self.task(task_id)
        rows = self.db.execute("""
            SELECT i.*, e.source,
                   (SELECT r.question_id FROM resolutions r WHERE r.resolution_item_id = i.id) AS resolves
            FROM items i JOIN events e ON e.id = i.event_id
            WHERE i.task_id = ? ORDER BY i.created_at, i.rowid
        """, (task_id,)).fetchall()
        return [dict(row) for row in rows]

    def current_items(self, task_id):
        rows = self.items(task_id)
        replaced = {row["supersedes"] for row in rows if row["supersedes"]}
        resolved = {row[0] for row in self.db.execute(
            "SELECT question_id FROM resolutions WHERE question_id IN "
            "(SELECT id FROM items WHERE task_id = ?)", (task_id,)
        )}
        return [row for row in rows if row["id"] not in replaced and row["id"] not in resolved]

    def resolve_question(self, task_id, question_id, decision, source, supersedes=None):
        self.task(task_id)
        question = self.db.execute(
            "SELECT task_id, kind FROM items WHERE id = ?", (question_id,)
        ).fetchone()
        if question is None or question["task_id"] != task_id or question["kind"] != "question":
            raise ValueError("Question must exist in the active task")
        if self.db.execute("SELECT 1 FROM resolutions WHERE question_id = ?", (question_id,)).fetchone():
            raise ValueError("Question has already been resolved")
        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("Resolution decision cannot be empty")
        if supersedes:
            old = self.db.execute("SELECT task_id, kind FROM items WHERE id = ?", (supersedes,)).fetchone()
            if old is None or old["task_id"] != task_id or old["kind"] != "decision":
                raise ValueError("Superseded decision must exist in the active task")
            if self.db.execute("SELECT 1 FROM items WHERE supersedes = ?", (supersedes,)).fetchone():
                raise ValueError("Decision has already been superseded")
        event_id, item_id, created = _id(), _id(), _now()
        with self.db:
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                            (event_id, task_id, source, decision.strip(), created))
            self.db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (item_id, task_id, "decision", decision.strip(), event_id, supersedes, created))
            self.db.execute("INSERT INTO resolutions VALUES (?, ?, ?)",
                            (question_id, item_id, created))
        return item_id

    def set_supersession(self, task_id, old_item_id, new_item_id):
        self.task(task_id)
        rows = self.db.execute(
            "SELECT id, task_id, kind, supersedes FROM items WHERE id IN (?, ?)",
            (old_item_id, new_item_id),
        ).fetchall()
        by_id = {row["id"]: row for row in rows}
        old, new = by_id.get(old_item_id), by_id.get(new_item_id)
        if old is None or new is None or old["task_id"] != task_id or new["task_id"] != task_id:
            raise ValueError("Both items must exist in the active task")
        if old_item_id == new_item_id or old["kind"] != new["kind"]:
            raise ValueError("Supersession requires two different items of the same kind")
        if new["supersedes"] and new["supersedes"] != old_item_id:
            raise ValueError("New item already supersedes another item")
        cursor = old
        seen = set()
        while cursor and cursor["id"] not in seen:
            if cursor["id"] == new_item_id:
                raise ValueError("Supersession would create a cycle")
            seen.add(cursor["id"])
            cursor = (self.db.execute(
                "SELECT id, task_id, kind, supersedes FROM items WHERE id = ?", (cursor["supersedes"],)
            ).fetchone() if cursor["supersedes"] else None)
        if self.db.execute(
            "SELECT 1 FROM items WHERE supersedes = ? AND id != ?", (old_item_id, new_item_id)
        ).fetchone():
            raise ValueError("Old item has already been superseded")
        with self.db:
            self.db.execute("UPDATE items SET supersedes = ? WHERE id = ?", (old_item_id, new_item_id))

    def explain(self, item_id):
        row = self.db.execute("""
            SELECT i.*, e.source, e.body AS evidence, e.created_at AS event_time
            FROM items i JOIN events e ON e.id = i.event_id WHERE i.id = ?
        """, (item_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown item: " + item_id)
        return dict(row)

    def checkpoint(self, task_id):
        snapshot = [row["id"] for row in self.current_items(task_id)]
        checkpoint_id = _id()
        with self.db:
            self.db.execute("INSERT INTO checkpoints VALUES (?, ?, ?, ?)",
                            (checkpoint_id, task_id, _now(), json.dumps(snapshot)))
        return checkpoint_id

    def checkpoints(self, task_id):
        self.task(task_id)
        return [dict(row) for row in self.db.execute(
            "SELECT id, task_id, created_at FROM checkpoints WHERE task_id = ? ORDER BY rowid",
            (task_id,),
        )]

    def context(self, task_id):
        return {"task": self.task(task_id), "items": self.current_items(task_id)}

    def _checkpoint(self, checkpoint_id):
        row = self.db.execute("SELECT rowid AS sequence, * FROM checkpoints WHERE id = ?", (checkpoint_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown checkpoint: " + checkpoint_id)
        return dict(row)

    def delta(self, base_id, head_id):
        base, head = self._checkpoint(base_id), self._checkpoint(head_id)
        if base["task_id"] != head["task_id"]:
            raise ValueError("Checkpoints belong to different tasks")
        if base["sequence"] > head["sequence"]:
            raise ValueError("Base checkpoint is newer than head checkpoint")
        before, after = set(json.loads(base["snapshot"])), set(json.loads(head["snapshot"]))
        by_id = {row["id"]: row for row in self.items(base["task_id"])}
        return {
            "task": self.task(base["task_id"]), "base": base_id, "head": head_id,
            "added": [by_id[item_id] for item_id in json.loads(head["snapshot"]) if item_id not in before],
            "removed": [by_id[item_id] for item_id in json.loads(base["snapshot"]) if item_id not in after],
        }
