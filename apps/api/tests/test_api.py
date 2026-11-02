"""Job: GODMODE Backend. Purpose: Pytest coverage for Architect /api/v1 auth tasks runs authz."""
import os
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "test_godmode.db"
if DB.exists():
    DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["GODMODE_MOCK_LLM"] = "1"
os.environ["GODMODE_REQUIRE_REDIS"] = "0"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from app.main import app


def client():
    return TestClient(app)


def login(c, email="admin@godmode.local", password="godmode123"):
    r = c.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_and_ready():
    with client() as c:
        assert c.get("/health").status_code == 200
        assert c.get("/api/v1/health").json()["status"] == "ok"
        r = c.get("/ready")
        assert r.status_code == 200
        assert r.json()["db"] is True


def test_auth_me_and_refresh():
    with client() as c:
        assert c.get("/api/v1/auth/me").status_code == 401
        r = c.post("/api/v1/auth/login", json={"email": "admin@godmode.local", "password": "godmode123"})
        body = r.json()
        h = {"Authorization": f"Bearer {body['access_token']}"}
        me = c.get("/api/v1/auth/me", headers=h)
        assert me.status_code == 200 and me.json()["role"] == "admin"
        ref = c.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
        assert ref.status_code == 200 and "access_token" in ref.json()


def test_tasks_crud_and_start_creates_run():
    with client() as c:
        h = login(c)
        assert c.get("/api/v1/tasks").status_code == 401
        r = c.post("/api/v1/tasks", json={"title": "Price memo", "description": "Research competitors"}, headers=h)
        assert r.status_code == 201, r.text
        task = r.json()
        assert task["status"] == "draft"
        tid = task["id"]
        start = c.post(f"/api/v1/tasks/{tid}/start", headers=h)
        assert start.status_code == 200, start.text
        run = start.json()
        assert run["task_id"] == tid
        assert run["current_stage"] == "plan"
        assert run["mock_llm"] is True
        got = c.get(f"/api/v1/runs/{run['id']}", headers=h)
        assert got.status_code == 200
        assert len(got.json()["stage_events"]) >= 1


def test_viewer_cannot_start_operator_can():
    with client() as c:
        vh = login(c, "viewer@godmode.local")
        oh = login(c, "operator@godmode.local")
        created = c.post("/api/v1/tasks", json={"title": "Viewer blocked start"}, headers=oh)
        tid = created.json()["id"]
        assert c.post(f"/api/v1/tasks/{tid}/start", headers=vh).status_code == 403
        assert c.post(f"/api/v1/tasks/{tid}/start", headers=oh).status_code == 200


def test_agents_memory_dashboard_contract_paths():
    with client() as c:
        h = login(c)
        assert c.get("/api/v1/agents", headers=h).status_code == 200
        assert c.get("/api/v1/memory", headers=h).status_code == 200
        assert c.get("/api/v1/dashboard/summary", headers=h).status_code == 200
        # decide endpoint exists (404 on missing id, not 405)
        assert c.post("/api/v1/approvals/99999/decide", json={"decision": "approve"}, headers=h).status_code == 404
