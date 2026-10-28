"""A small to-do list web app. Run with `flask --app todo run`."""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path
from typing import Any

from flask import Flask, Response, abort, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from todo import db

MAX_TASK_LENGTH = 200

log = logging.getLogger(__name__)

# Styles come from /static, so no inline script or style needs to be allowed.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}

csrf = CSRFProtect()


def _secret_key() -> str:
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    # Fine for one local process; sessions reset on restart. Set SECRET_KEY in production.
    log.warning("SECRET_KEY not set; using a random key for this process")
    return secrets.token_hex(32)


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE", str(Path(app.instance_path) / "todo.db")),
        SECRET_KEY=_secret_key(),
        MAX_CONTENT_LENGTH=16 * 1024,  # forms are tiny; reject anything bigger
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false") == "true",
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers.update(SECURITY_HEADERS)
        return response

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
