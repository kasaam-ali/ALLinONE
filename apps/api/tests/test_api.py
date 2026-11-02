"""Purpose: API tests for the canonical /api/v1 contract and the two-gate run flow (mock LLM)."""
import os
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "test_godmode.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["GODMODE_MOCK_LLM"] = "1"
os.environ["JWT_SECRET"] = "test-secret-at-least-32-bytes-long!!"
os.environ["GODMODE_REQUIRE_JWT_SECRET"] = "0"
if DB.exists():
    DB.unlink()

import pytest
from fastapi.testclient import TestClient
from app.main import app

V = "/api/v1"


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        yield client


def login(c, email="admin@godmode.local"):
    r = c.post(f"{V}/auth/login", json={"email": email, "password": "godmode123"})
    assert r.status_code == 200, r.text
    return r.json()


def hdr(tok):
    return {"Authorization": f"Bearer {tok['access_token']}"}


def test_health_ready(c):
    assert c.get(f"{V}/health").json()["status"] == "ok"
    assert c.get(f"{V}/ready").json()["status"] == "ready"


def test_auth_flow(c):
    assert c.get(f"{V}/tasks").status_code == 401
    tok = login(c)
    assert c.get(f"{V}/auth/me", headers=hdr(tok)).json()["role"] == "admin"
    r = c.post(f"{V}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 200 and r.json()["access_token"]
    assert c.post(f"{V}/auth/refresh", json={"refresh_token": tok["access_token"]}).status_code == 401


def test_agents(c):
    h = hdr(login(c))
    slugs = {a["slug"] for a in c.get(f"{V}/agents", headers=h).json()}
    assert {"planner", "researcher", "executor", "verifier", "reporter"} <= slugs
    r = c.post(f"{V}/agents", headers=h, json={"slug": "extra", "name": "Extra", "tools_allowlist": ["http_fetch"]})
    assert r.status_code == 201, r.text
    aid = r.json()["id"]
    assert c.patch(f"{V}/agents/{aid}", headers=h, json={"name": "Extra2"}).json()["version"] == 2
    assert c.post(f"{V}/agents/{aid}/disable", headers=h).json()["status"] == "disabled"
    assert c.post(f"{V}/agents", headers=h, json={"slug": "bad", "name": "B", "tools_allowlist": ["nope"]}).status_code == 422


def test_viewer_cannot_write(c):
    h = hdr(login(c, "viewer@godmode.local"))
    assert c.get(f"{V}/tasks", headers=h).status_code == 200
    assert c.post(f"{V}/tasks", headers=h, json={"title": "x"}).status_code == 403


def _start(c, h, title):
    t = c.post(f"{V}/tasks", headers=h, json={"title": title}).json()
    r = c.post(f"{V}/tasks/{t['id']}/start", headers=h)
    assert r.status_code == 201, r.text
    return t, r.json()


def test_two_gate_flow_and_publish(c):
    h = hdr(login(c))
    t, run = _start(c, h, "Ship MVP")
    assert run["status"] == "awaiting_approval"
    gate1 = run["pending_approvals"][0]
    assert gate1["gate"] == "after_plan"
    pend = c.get(f"{V}/approvals?status=pending", headers=h).json()
    assert any(a["id"] == gate1["id"] for a in pend)

    r = c.post(f"{V}/approvals/{gate1['id']}/decide", headers=h, json={"decision": "approve", "note": "ok"})
    assert r.status_code == 200, r.text
    run = r.json()["run"]
    assert run["status"] == "awaiting_approval"
    gate2 = run["pending_approvals"][0]
    assert gate2["gate"] == "before_publish"
    assert c.post(f"{V}/approvals/{gate1['id']}/decide", headers=h, json={"decision": "approve"}).status_code == 409

    run = c.post(f"{V}/approvals/{gate2['id']}/decide", headers=h, json={"decision": "approve"}).json()["run"]
    assert run["status"] == "succeeded"
    stages = [e["stage"] for e in c.get(f"{V}/runs/{run['id']}/events", headers=h).json()]
    assert stages == ["plan", "research", "execute", "verify", "report"]
    arts = c.get(f"{V}/runs/{run['id']}/artifacts", headers=h).json()
    assert len(arts) == 5
    assert c.get(f"{V}/tasks/{t['id']}", headers=h).json()["status"] == "succeeded"

    rep = [x for x in c.get(f"{V}/reports", headers=h).json() if x["run_id"] == run["id"]][0]
    assert c.get(f"{V}/reports/{rep['id']}", headers=h).json()["status"] == "draft"
    assert c.post(f"{V}/reports/{rep['id']}/publish", headers=h).json()["status"] == "published"


def test_reject_and_cancel(c):
    h = hdr(login(c))
    _, run = _start(c, h, "Reject me")
    aid = run["pending_approvals"][0]["id"]
    run = c.post(f"{V}/approvals/{aid}/decide", headers=h, json={"decision": "reject"}).json()["run"]
    assert run["status"] == "failed"
    assert c.post(f"{V}/approvals/{aid}/decide", headers=h, json={"decision": "maybe"}).status_code in (409, 422)

    _, run2 = _start(c, h, "Cancel me")
    r = c.post(f"{V}/runs/{run2['id']}/cancel", headers=h).json()
    assert r["status"] == "cancelled" and r["pending_approvals"] == []
    assert c.post(f"{V}/runs/{run2['id']}/cancel", headers=h).status_code == 409


def test_memory_crud(c):
    h = hdr(login(c))
    m = c.post(f"{V}/memory", headers=h, json={"key": "k1", "content": "v1"}).json()
    assert c.patch(f"{V}/memory/{m['id']}", headers=h, json={"content": "v2"}).json()["content"] == "v2"
    assert c.get(f"{V}/memory/{m['id']}", headers=h).status_code == 200
    assert c.delete(f"{V}/memory/{m['id']}", headers=h).status_code == 204
    assert c.get(f"{V}/memory/{m['id']}", headers=h).status_code == 404


def test_dashboard_and_audit(c):
    h = hdr(login(c))
    d = c.get(f"{V}/dashboard/summary", headers=h).json()
    assert d["tasks_total"] >= 3 and d["agents_active"] >= 5
    acts = {a["action"] for a in c.get(f"{V}/audit", headers=h).json()}
    assert {"auth.login", "run.start"} <= acts
