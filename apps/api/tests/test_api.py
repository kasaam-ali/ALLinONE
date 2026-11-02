# API tests: health check, auth guard, and the create-task with approval flow.
import os
import uuid
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "test_godmode.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["GODMODE_MOCK_LLM"] = "1"
if DB.exists():
    DB.unlink()

from fastapi.testclient import TestClient
from app.main import app

def client():
    return TestClient(app)

def token(c):
    r = c.post("/auth/login", json={"email": "admin@godmode.local", "password": "godmode123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_health():
    with client() as c:
        r = c.get("/health")
        assert r.status_code == 200 and r.json()["status"] == "ok"

def test_auth_required():
    with client() as c:
        assert c.get("/tasks").status_code == 401

def test_create_task_with_approval_flow():
    with client() as c:
        h = token(c)
        r = c.post("/tasks", json={"prompt": "Research top 3 competitors and draft a pricing memo"}, headers=h)
        assert r.status_code == 201, r.text
        t = r.json()
        assert t["status"] == "awaiting_approval"
        assert [s["phase"] for s in t["plans"][0]["steps"]] == ["plan", "research", "execute", "verify", "report"]
        assert t["approvals"][0]["gate"] == "after_plan"
        aid = t["approvals"][0]["id"]
        r = c.post(f"/approvals/{aid}/approve", json={"reason": "plan ok"}, headers=h)
        assert r.status_code == 200, r.text
        t2 = r.json()
        assert t2["status"] == "awaiting_approval"
        gates = [a["gate"] for a in t2["approvals"]]
        assert "before_publish" in gates
        pub = next(a for a in t2["approvals"] if a["gate"] == "before_publish" and a["status"] == "pending")
        r = c.post(f"/approvals/{pub['id']}/approve", json={"reason": "publish ok"}, headers=h)
        assert r.status_code == 200 and r.json()["status"] == "completed"
        assert any(x["task_id"] == t["id"] for x in c.get("/reports", headers=h).json())
        assert any(a["action"] == "approval.approved" for a in c.get("/audit", headers=h).json())

def test_create_task_no_approval_and_register_viewer_perms():
    with client() as c:
        h = token(c)
        r = c.post("/tasks", json={"prompt": "Summarize weekly KPIs", "requires_approval": False}, headers=h)
        assert r.json()["status"] == "completed"
        email = f"op-{uuid.uuid4().hex[:8]}@x.io"
        r = c.post("/auth/register", json={"email": email, "password": "pw123456"})
        assert r.status_code == 200 and r.json()["user"]["role"] == "operator"
        assert c.post("/workforce", json={"name": "N", "role": "research"}, headers=h).status_code == 201
