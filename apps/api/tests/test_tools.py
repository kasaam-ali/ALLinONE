"""Tests for stub tools, allowlist enforcement, and the inbound webhook stub endpoint."""
import socket, pytest
from fastapi.testclient import TestClient
from app.tools import invoke, ToolNotAllowed, KNOWN_STUB_TOOLS, validate_allowlist
from app.tools.http_fetch import http_fetch
from app.tools.browser_stub import browser_stub

@pytest.fixture
def no_network(monkeypatch):
    def boom(*a, **k): raise AssertionError("network attempted")
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket.socket, "connect", boom)

def test_stubs_flagged_and_offline(no_network):
    for r in (http_fetch("https://example.com"), browser_stub("open", "https://example.com"),
              invoke("webhook_inbound", {"source": "gh", "body": {"a": 1}}, ["webhook_inbound"])):
        assert r["stub"] is True and "Kasaam" in r["note"] and r["ok"]
    assert http_fetch("https://a") == http_fetch("https://a")

def test_allowlist_enforced():
    with pytest.raises(ToolNotAllowed): invoke("browser_stub", {}, ["http_fetch"])
    with pytest.raises(ToolNotAllowed): invoke("http_fetch", {}, [])
    with pytest.raises(ValueError): validate_allowlist(["mock"])
    assert set(KNOWN_STUB_TOOLS) == {"http_fetch", "browser_stub", "webhook_inbound"}

def test_webhook_endpoint_and_tools_list(no_network):
    from app.main import app
    c = TestClient(app)
    r = c.post("/api/v1/integrations/webhooks/github", json={"event": "push"})
    assert r.status_code == 200 and r.json()["stub"] is True and r.json()["data"]["fanout"] is False
    assert c.post("/api/v1/integrations/webhooks/Bad!Src", json={}).status_code in (404, 422)
    t = c.get("/api/v1/integrations/tools").json()
    assert t["stub"] is True and {x["name"] for x in t["tools"]} == set(KNOWN_STUB_TOOLS)
