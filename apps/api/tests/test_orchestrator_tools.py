"""Tests that research/execute stage helpers honor tools_allowlist (stub-only)."""
from app.tools import run_phase_tools


def test_execute_runs_allowlisted_stubs_only():
    agents = [
        {"name": "Scout", "role": "research", "tools_allowlist": ["http_fetch"]},
        {"name": "Forge", "role": "execute", "tools_allowlist": ["http_fetch", "browser_stub"]},
    ]
    research = run_phase_tools("research", "ship stub wiring", agents)
    execute = run_phase_tools("execute", "ship stub wiring", agents)
    calls = research + execute
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
    assert run_phase_tools("research", "no tools", agents) == []
    assert run_phase_tools("execute", "no tools", agents) == []
