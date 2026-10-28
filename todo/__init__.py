"""A small to-do list web app. Run with `flask --app todo run`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, abort, redirect, render_template, request, url_for

from todo import db

MAX_TASK_LENGTH = 200


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "todo.db"))
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    @app.get("/")
    def index() -> str:
        return render_template("index.html", tasks=db.list_tasks(), max_length=MAX_TASK_LENGTH)

    @app.post("/tasks")
    def add_task() -> Any:
        text = request.form.get("task", "").strip()
        if not text or len(text) > MAX_TASK_LENGTH:
            abort(400)
        db.add_task(text)
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id: int) -> Any:
        # Deleting by ID (not list position) means two open tabs can't delete
        # the wrong task, and a bad ID is a 404 instead of a crash.
        if not db.delete_task(task_id):
            abort(404)
        return redirect(url_for("index"))

    return app
