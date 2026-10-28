"""SQLite storage. Every query uses bound parameters, never string formatting."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL CHECK (length(text) BETWEEN 1 AND 200),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@dataclass(frozen=True)
class Task:
    id: int
    text: str


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db  # type: ignore[no-any-return]


def close_db(_: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app: Flask) -> None:
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.executescript(SCHEMA)
    app.teardown_appcontext(close_db)


def list_tasks() -> list[Task]:
    rows = get_db().execute("SELECT id, text FROM tasks ORDER BY id").fetchall()
    return [Task(row["id"], row["text"]) for row in rows]


def add_task(text: str) -> int:
    conn = get_db()
    with conn:
        cursor = conn.execute("INSERT INTO tasks (text) VALUES (?)", (text,))
    return int(cursor.lastrowid or 0)


def delete_task(task_id: int) -> bool:
    conn = get_db()
    with conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount == 1
