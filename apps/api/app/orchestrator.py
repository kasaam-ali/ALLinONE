"""Job: GODMODE Agentic AI.
Purpose: LangGraph multi-agent graph plan -> research -> execute -> verify -> report
with human approval gates after_plan and before_publish. GODMODE_MOCK_LLM=1 default.
"""
from __future__ import annotations

import json
import os
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from .tools import run_phase_tools

MOCK = os.getenv("GODMODE_MOCK_LLM", "1") == "1"
GATES = ("after_plan", "before_publish")


class S(TypedDict, total=False):
    prompt: str
    agents: list
    requires_approval: bool
    after_plan_approved: bool
    before_publish_approved: bool
    plan: list
    outputs: dict
    paused: bool
    pause_gate: str
    report: str
    verification: dict
    memory_refs: list
    audit: list
    tool_calls: list


def llm(role: str, prompt: str) -> str:
    if MOCK:
        return f"[mock-{role}] {prompt[:240]}"
    raise RuntimeError("Real LLM not wired in MVP; set GODMODE_MOCK_LLM=1")


def _agent(state: S, phase: str) -> str:
    agents = state.get("agents") or []
    for a in agents:
        if phase in (a.get("role") or "").lower():
            return a["name"]
    return agents[0]["name"] if agents else f"{phase.title()} Agent"


def _audit(state: S, node: str, detail: str) -> list:
    events = list(state.get("audit") or [])
    events.append({"node": node, "detail": detail})
    return events


def plan_node(state: S) -> dict:
    p = state["prompt"]
    steps = [
        {"phase": "plan", "description": f"Decompose objective: {p[:80]}"},
        {"phase": "research", "description": "Gather context and constraints"},
        {"phase": "execute", "description": "Carry out the work (sandboxed / mock tools)"},
        {"phase": "verify", "description": "Check results against objective"},
        {"phase": "report", "description": "Summarize outcome for humans"},
    ]
    for s in steps:
        s["agent"] = _agent(state, s["phase"])
    out = dict(state.get("outputs") or {})
    out["plan"] = llm("planner", "Plan for: " + p)
    return {
        "plan": steps,
        "outputs": out,
        "paused": False,
        "pause_gate": "",
        "audit": _audit(state, "plan", f"steps={len(steps)}"),
    }


def after_plan_gate(state: S) -> dict:
    if state.get("requires_approval") and not state.get("after_plan_approved"):
        return {
            "paused": True,
            "pause_gate": "after_plan",
            "audit": _audit(state, "after_plan_gate", "awaiting_approval"),
        }
    return {
        "paused": False,
        "pause_gate": "",
        "after_plan_approved": True,
        "audit": _audit(state, "after_plan_gate", "cleared"),
    }


def research_node(state: S) -> dict:
    out = dict(state.get("outputs") or {})
    out["research"] = llm("research", f"research for: {state['prompt']}")
    if MOCK:
        out["research"] += "\n[evidence:mock] stub sources only - no external fetch"
    calls = list(state.get("tool_calls") or [])
    calls.extend(run_phase_tools("research", state["prompt"], state.get("agents") or []))
    out["tool_calls"] = calls
    return {
        "outputs": out,
        "tool_calls": calls,
        "audit": _audit(state, "research", f"tools={len(calls)}"),
    }


def execute_node(state: S) -> dict:
    out = dict(state.get("outputs") or {})
    evidence = {"mock": MOCK, "note": "stub only - no external side effect"}
    out["execute"] = llm("execute", f"execute for: {state['prompt']}") + f"\nevidence={evidence}"
    calls = list(state.get("tool_calls") or [])
    new_calls = run_phase_tools("execute", state["prompt"], state.get("agents") or [])
    calls.extend(new_calls)
    out["tool_calls"] = calls
    return {
        "outputs": out,
        "tool_calls": calls,
        "audit": _audit(state, "execute", f"tools={len(new_calls)}"),
    }


def verify_node(state: S) -> dict:
    out = dict(state.get("outputs") or {})
    checks = [
        {"name": "has_plan", "ok": bool(state.get("plan")), "detail": "plan present"},
        {"name": "has_research", "ok": "research" in out, "detail": "research output"},
        {"name": "has_execute", "ok": "execute" in out, "detail": "execute output"},
        {
            "name": "after_plan_cleared",
            "ok": (not state.get("requires_approval")) or bool(state.get("after_plan_approved")),
            "detail": "after_plan gate",
        },
    ]
    passed = all(c["ok"] for c in checks) if checks else False
    verification = {"passed": passed, "checks": checks}
    out["verify"] = llm("verify", f"verify for: {state['prompt']} passed={passed}")
    return {
        "outputs": out,
        "verification": verification,
        "audit": _audit(state, "verify", f"passed={passed}"),
    }


def before_publish_gate(state: S) -> dict:
    if state.get("requires_approval") and not state.get("before_publish_approved"):
        return {
            "paused": True,
            "pause_gate": "before_publish",
            "audit": _audit(state, "before_publish_gate", "awaiting_approval"),
        }
    return {
        "paused": False,
        "pause_gate": "",
        "before_publish_approved": True,
        "audit": _audit(state, "before_publish_gate", "cleared"),
    }


def report_node(state: S) -> dict:
    out = dict(state.get("outputs") or {})
    body = "\n".join(f"## {k}\n{v}" for k, v in out.items() if k != "tool_calls")
    ver = state.get("verification") or {}
    headline = "Task completed" if ver.get("passed", True) else "Task finished with issues"
    report = f"# {headline}\nObjective: {state['prompt']}\n\n{body}\n"
    out["report"] = headline
    mem = list(state.get("memory_refs") or [])
    mem.append("task:last_report")
    return {
        "outputs": out,
        "report": report,
        "paused": False,
        "pause_gate": "",
        "memory_refs": mem,
        "audit": _audit(state, "report", headline),
    }


def _route_after_plan_gate(state: S) -> Literal["pause_sink", "research"]:
    return "pause_sink" if state.get("paused") else "research"


def _route_after_publish_gate(state: S) -> Literal["pause_sink", "report"]:
    return "pause_sink" if state.get("paused") else "report"


def pause_sink(state: S) -> dict:
    return {"paused": True}


def build():
    g = StateGraph(S)
    g.add_node("plan", plan_node)
    g.add_node("after_plan_gate", after_plan_gate)
    g.add_node("research", research_node)
    g.add_node("execute", execute_node)
    g.add_node("verify", verify_node)
    g.add_node("before_publish_gate", before_publish_gate)
    g.add_node("report", report_node)
    g.add_node("pause_sink", pause_sink)

    g.set_entry_point("plan")
    g.add_edge("plan", "after_plan_gate")
    g.add_conditional_edges(
        "after_plan_gate",
        _route_after_plan_gate,
        {"pause_sink": "pause_sink", "research": "research"},
    )
    g.add_edge("research", "execute")
    g.add_edge("execute", "verify")
    g.add_edge("verify", "before_publish_gate")
    g.add_conditional_edges(
        "before_publish_gate",
        _route_after_publish_gate,
        {"pause_sink": "pause_sink", "report": "report"},
    )
    g.add_edge("report", END)
    g.add_edge("pause_sink", END)
    return g.compile()


GRAPH = build()


def enqueue_run(run_id: int) -> dict:
    """Compatibility hook for Backend. Real execution goes through run_planning/run_full."""
    return {
        "enqueued": True,
        "run_id": run_id,
        "mock_llm": MOCK,
        "gates": list(GATES),
        "note": "Use run_planning / continue_after_* / run_full for graph execution",
    }


def _base(prompt: str, agents: list, requires_approval: bool) -> S:
    return {
        "prompt": prompt,
        "agents": agents,
        "requires_approval": requires_approval,
        "after_plan_approved": False,
        "before_publish_approved": False,
        "outputs": {},
        "plan": [],
        "paused": False,
        "pause_gate": "",
        "audit": [],
        "memory_refs": [],
        "tool_calls": [],
    }


def run_planning(prompt: str, agents: list, requires_approval: bool) -> dict[str, Any]:
    """Run through plan and after_plan gate. May pause awaiting approval."""
    return GRAPH.invoke(_base(prompt, agents, requires_approval))


def continue_after_plan(prompt: str, agents: list, prior: dict | None = None) -> dict[str, Any]:
    """Resume after after_plan approval through verify / before_publish gate."""
    state: S = _base(prompt, agents, True)
    if prior:
        state["plan"] = prior.get("plan") or state["plan"]
        state["outputs"] = dict(prior.get("outputs") or {})
        state["tool_calls"] = list(prior.get("tool_calls") or [])
    state["after_plan_approved"] = True
    state["requires_approval"] = True
    return GRAPH.invoke(state)


def continue_after_publish(prompt: str, agents: list, prior: dict | None = None) -> dict[str, Any]:
    """Resume after before_publish approval into report."""
    state: S = _base(prompt, agents, True)
    if prior:
        state["plan"] = prior.get("plan") or []
        state["outputs"] = dict(prior.get("outputs") or {})
        state["verification"] = prior.get("verification") or {"passed": True, "checks": []}
        state["tool_calls"] = list(prior.get("tool_calls") or [])
    state["after_plan_approved"] = True
    state["before_publish_approved"] = True
    state["requires_approval"] = True
    return GRAPH.invoke(state)


def run_full(prompt: str, agents: list) -> dict[str, Any]:
    """No human gates. Both approvals pre-cleared."""
    state = _base(prompt, agents, False)
    state["after_plan_approved"] = True
    state["before_publish_approved"] = True
    return GRAPH.invoke(state)


if __name__ == "__main__":
    os.environ.setdefault("GODMODE_MOCK_LLM", "1")
    out = run_full("Solo graph smoke: draft a one-page ops brief", [])
    print(
        json.dumps(
            {
                "paused": out.get("paused"),
                "pause_gate": out.get("pause_gate"),
                "phases": list((out.get("outputs") or {}).keys()),
                "report_head": (out.get("report") or "")[:180],
                "audit_len": len(out.get("audit") or []),
                "mock": MOCK,
                "gates": list(GATES),
            },
            indent=2,
        )
    )
