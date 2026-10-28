from pathlib import Path

from flask.testing import FlaskClient

from todo import MAX_TASK_LENGTH, create_app


def test_empty_list_shows_placeholder(client: FlaskClient) -> None:
    assert b"Nothing to do yet." in client.get("/").data


def test_add_task_then_see_it(client: FlaskClient) -> None:
    response = client.post("/tasks", data={"task": "  Buy milk  "})
    assert response.status_code == 302
    page = client.get("/").data
    assert b"Buy milk" in page
    assert b"Nothing to do yet." not in page


def test_delete_task_by_id(client: FlaskClient) -> None:
    client.post("/tasks", data={"task": "first"})
    client.post("/tasks", data={"task": "second"})

    assert client.post("/tasks/1/delete").status_code == 302

    page = client.get("/").data
    assert b"first" not in page
    assert b"second" in page


def test_deleting_missing_task_is_404_not_a_crash(client: FlaskClient) -> None:
    assert client.post("/tasks/999/delete").status_code == 404


def test_non_numeric_id_is_404(client: FlaskClient) -> None:
    assert client.post("/tasks/abc/delete").status_code == 404


def test_blank_task_is_rejected(client: FlaskClient) -> None:
    assert client.post("/tasks", data={"task": "   "}).status_code == 400


def test_overlong_task_is_rejected(client: FlaskClient) -> None:
    response = client.post("/tasks", data={"task": "x" * (MAX_TASK_LENGTH + 1)})
    assert response.status_code == 400


def test_task_text_is_html_escaped(client: FlaskClient) -> None:
    client.post("/tasks", data={"task": "<script>alert(1)</script>"})
    page = client.get("/").data
    assert b"<script>alert(1)</script>" not in page
    assert b"&lt;script&gt;" in page


def test_sql_in_task_is_stored_as_text(client: FlaskClient) -> None:
    client.post("/tasks", data={"task": "x'); DROP TABLE tasks; --"})
    assert b"DROP TABLE" in client.get("/").data


def test_tasks_survive_a_restart(tmp_path: Path) -> None:
    config = {"TESTING": True, "WTF_CSRF_ENABLED": False, "DATABASE": str(tmp_path / "keep.db")}
    create_app(config).test_client().post("/tasks", data={"task": "persist me"})
    assert b"persist me" in create_app(config).test_client().get("/").data
