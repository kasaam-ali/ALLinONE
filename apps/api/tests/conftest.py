"""Purpose: Isolated pytest harness. Each pytest process gets its own temp SQLite DB.

Never deletes godmode.db or any shared dev DB, so a live uvicorn keeps working.
Env vars are set at import time, before any test module imports app.*.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = Path(tempfile.mkdtemp(prefix="godmode_pytest_"))
TEST_DB = _TMP_DIR / "test_godmode.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["GODMODE_MOCK_LLM"] = "1"
os.environ["JWT_SECRET"] = "test-secret-at-least-32-bytes-long!!"
os.environ["GODMODE_REQUIRE_JWT_SECRET"] = "0"


@pytest.fixture(scope="session", autouse=True)
def _isolated_db():
    """Guard that the engine points at the temp DB, then clean up after the session."""
    from app import db as app_db

    assert str(TEST_DB) in str(app_db.engine.url), app_db.engine.url
    yield
    app_db.engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def c():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client
