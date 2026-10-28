import re
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from todo import SECURITY_HEADERS, create_app


@pytest.fixture
def csrf_client(tmp_path: Path) -> FlaskClient:
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "csrf.db")}).test_client()


def _token(client: FlaskClient) -> str:
    match = re.search(rb'name="csrf_token" value="([^"]+)"', client.get("/").data)
    assert match, "page should contain a CSRF token"
    return match.group(1).decode()


def test_post_without_csrf_token_is_rejected(csrf_client: FlaskClient) -> None:
    assert csrf_client.post("/tasks", data={"task": "sneaky"}).status_code == 400
    assert b"sneaky" not in csrf_client.get("/").data


def test_delete_without_csrf_token_is_rejected(csrf_client: FlaskClient) -> None:
    csrf_client.post("/tasks", data={"task": "keep", "csrf_token": _token(csrf_client)})
    assert csrf_client.post("/tasks/1/delete").status_code == 400
    assert b"keep" in csrf_client.get("/").data


def test_post_with_csrf_token_works(csrf_client: FlaskClient) -> None:
    response = csrf_client.post("/tasks", data={"task": "ok", "csrf_token": _token(csrf_client)})
    assert response.status_code == 302


def test_token_from_another_session_is_rejected(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "x.db")})
    stolen = _token(app.test_client())
    attacker = app.test_client()
    assert attacker.post("/tasks", data={"task": "x", "csrf_token": stolen}).status_code == 400


def test_security_headers_on_every_response(client: FlaskClient) -> None:
    for response in (client.get("/"), client.post("/tasks/999/delete")):
        for name, value in SECURITY_HEADERS.items():
            assert response.headers[name] == value


def test_page_has_no_inline_styles_or_scripts(client: FlaskClient) -> None:
    page = client.get("/").data
    assert b"<style" not in page
    assert b"<script" not in page


def test_oversized_request_is_rejected(client: FlaskClient) -> None:
    assert client.post("/tasks", data={"task": "x" * 20_000}).status_code == 413


def test_session_cookie_flags(csrf_client: FlaskClient) -> None:
    response = csrf_client.get("/")
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_secret_key_from_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SECRET_KEY", "k" * 64)
    app = create_app({"DATABASE": str(tmp_path / "k.db")})
    assert app.config["SECRET_KEY"] == "k" * 64


def test_random_secret_key_when_unset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = create_app({"DATABASE": str(tmp_path / "a.db")}).config["SECRET_KEY"]
    second = create_app({"DATABASE": str(tmp_path / "b.db")}).config["SECRET_KEY"]
    assert len(first) == 64
    assert first != second


def test_debug_is_off_by_default(tmp_path: Path) -> None:
    assert create_app({"DATABASE": str(tmp_path / "d.db")}).debug is False
