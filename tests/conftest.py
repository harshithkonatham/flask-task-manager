from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from todo import create_app


@pytest.fixture
def app(tmp_path: Path) -> Iterator[Flask]:
    # CSRF is switched off for most tests; tests/test_security.py checks it on.
    yield create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "DATABASE": str(tmp_path / "test.db")}
    )


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
