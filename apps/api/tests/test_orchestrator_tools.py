"""Tests that start/execute path honors Agent.tools_allowlist via stub invoke only."""
from app import orchestrator


def test_execute_runs_allowlisted_stubs_only():
    agents = [
        {"name": "Scout", "role": "research", "tools_allowlist": ["http_fetch"]},
        {"name": "Forge", "role": "execute", "tools_allowlist": ["http_fetch", "browser_stub"]},
    ]
    state = orchestrator.run_full("ship stub wiring", agents)
    calls = state["outputs"].get("tool_calls") or []
    assert calls, "expected stub tool_calls on execute path"
    assert all(c.get("stub") is True for c in calls)
    tools = {c["tool"] for c in calls}
    assert "http_fetch" in tools
    assert "browser_stub" in tools


def test_empty_allowlist_skips_tools():
    agents = [
        {"name": "Scout", "role": "research", "tools_allowlist": []},
        {"name": "Forge", "role": "execute", "tools_allowlist": []},
    ]
    state = orchestrator.run_full("no tools", agents)
    calls = state["outputs"].get("tool_calls") or []
    assert calls == []
