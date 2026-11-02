"""Run allowlisted stub tools for research/execute stages (for Agentic/Backend hooks)."""
from __future__ import annotations

from .registry import ToolNotAllowed, invoke
from .runtime_agents import definition_to_runtime_agent


def _allowlist(agent: dict) -> list:
    return list(agent.get("tools_allowlist") or [])


def _match_agent(agents: list[dict], phase: str) -> dict:
    for a in agents:
        if phase in (a.get("role") or "").lower():
            return a
    return agents[0] if agents else {}


def run_phase_tools(phase: str, prompt: str, agents: list[dict]) -> list[dict]:
    """Invoke stub tools allowed for the agent assigned to this phase.

    agents: runtime dicts with name, role, tools_allowlist (see runtime_agents).
    Returns list of result dicts, each including stub:true. No real outbound I/O.
    """
    agent = _match_agent(agents, phase)
    allow = _allowlist(agent)
    specs: list[tuple[str, dict]] = []
    key = (prompt or "")[:48]
    if phase == "research":
        specs = [("http_fetch", {"url": f"stub://research/{key}", "method": "GET"})]
    elif phase == "execute":
        specs = [
            ("http_fetch", {"url": f"stub://execute/{key}", "method": "GET"}),
            ("browser_stub", {"action": "snapshot", "url": f"stub://execute/{key}"}),
        ]
    else:
        return []

    calls: list[dict] = []
    for name, payload in specs:
        if name not in allow:
            continue
        try:
            result = invoke(name, payload, allow)
            calls.append({"phase": phase, "tool": name, "agent": agent.get("name"), **result})
        except ToolNotAllowed as e:
            calls.append(
                {
                    "phase": phase,
                    "tool": name,
                    "agent": agent.get("name"),
                    "stub": True,
                    "ok": False,
                    "error": str(e),
                }
            )
    return calls


def agents_from_definitions(definitions) -> list[dict]:
    """Convenience: AgentDefinition ORM rows -> runtime agent dicts."""
    return [definition_to_runtime_agent(d) for d in definitions]
