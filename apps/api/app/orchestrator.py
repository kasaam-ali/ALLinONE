"""Job: GODMODE Agentic AI. Purpose: LangGraph run orchestration with two human gates.

Flow: plan -> after_plan gate -> research -> execute -> verify -> before_publish gate -> report.
Each invocation runs from run.current_stage until it hits a pending gate or finishes.
Approval decisions resume the run via resume_after_gate. Mock LLM by default.
"""
import os
from datetime import datetime, timezone
from typing import TypedDict
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from .models import Run, StageEvent, Artifact, Approval, AgentDefinition, Report
from .tools import run_phase_tools, agents_from_definitions

MOCK = os.getenv("GODMODE_MOCK_LLM", "1") == "1"
GATES = ("after_plan", "before_publish")
STAGES = ("plan", "research", "execute", "verify", "report")
# Gate that must be approved after a stage completes.
GATE_AFTER = {"plan": "after_plan", "verify": "before_publish"}
SLUG_FOR = {"plan": "planner", "research": "researcher", "execute": "executor", "verify": "verifier", "report": "reporter"}


def _now():
    return datetime.now(timezone.utc)


class RunState(TypedDict, total=False):
    run_id: int
    stage: str
    halted: bool


def _mock_output(stage: str, title: str, tool_calls: list) -> str:
    base = {
        "plan": f"Plan for '{title}': 1) research 2) execute 3) verify 4) report",
        "research": f"Research notes for '{title}' (mock)",
        "execute": f"Execution output for '{title}' (mock)",
        "verify": f"Verification passed for '{title}' (mock)",
        "report": f"# Report: {title}\n\nAll stages completed (mock LLM).",
    }[stage]
    if tool_calls:
        base += f"\nTool calls: {[c['tool'] for c in tool_calls]}"
    return base


def _agent_id(db: Session, stage: str):
    a = db.query(AgentDefinition).filter(AgentDefinition.slug.like(f"{SLUG_FOR[stage]}%"),
                                         AgentDefinition.status == "active").first()
    return a.id if a else None


def build_graph(db: Session):
    def run_stage(state: RunState) -> RunState:
        run = db.get(Run, state["run_id"])
        stage = state["stage"]
        run.current_stage = stage
        run.status = "running"
        run.task.status = "running"
        ev = StageEvent(run_id=run.id, stage=stage, status="started", agent_definition_id=_agent_id(db, stage))
        db.add(ev)
        db.flush()
        calls = []
        if stage in ("research", "execute"):
            defs = db.query(AgentDefinition).filter_by(status="active").all()
            calls = run_phase_tools(stage, run.task.title, agents_from_definitions(defs))
        body = _mock_output(stage, run.task.title, calls)
        kind_map = {"plan": "plan", "research": "research", "execute": "result", "verify": "verification", "report": "report"}
        art = Artifact(run_id=run.id, stage=stage, kind=kind_map.get(stage, "other"),
                       body_text=body, mime="text/markdown")
        if calls:
            # Integrations stub tool_calls on the stage artifact body (SoT still Artifact row)
            art.body_text = body + "\n\n<!-- tool_calls:" + str(calls) + " -->"
        db.add(art)
        db.flush()
        ev.status = "succeeded"
        ev.output_ref = f"artifact:{art.id}"
        if stage == "report":
            db.add(Report(run_id=run.id, task_id=run.task_id, title=f"Report: {run.task.title}", body_md=body))
            run.status = "succeeded"
            run.task.status = "succeeded"
            run.finished_at = _now()
            db.commit()
            return {"halted": True}
        gate = GATE_AFTER.get(stage)
        nxt = STAGES[STAGES.index(stage) + 1]
        if gate:
            db.add(Approval(run_id=run.id, gate=gate, status="pending"))
            run.status = "awaiting_approval"
            run.task.status = "awaiting_approval"
            run.current_stage = nxt
            db.commit()
            return {"halted": True}
        db.commit()
        return {"stage": nxt, "halted": False}

    g = StateGraph(RunState)
    g.add_node("stage", run_stage)
    g.set_entry_point("stage")
    g.add_conditional_edges("stage", lambda s: END if s.get("halted") else "stage")
    return g.compile()


def advance(db: Session, run: Run) -> Run:
    """Run the graph from the run's current stage until a gate or completion."""
    build_graph(db).invoke({"run_id": run.id, "stage": run.current_stage, "halted": False},
                           {"recursion_limit": 20})
    db.refresh(run)
    return run


def start_run(db: Session, run: Run) -> Run:
    run.started_at = _now()
    run.current_stage = "plan"
    run.mock_llm = MOCK
    db.commit()
    return advance(db, run)


def resume_after_gate(db: Session, approval: Approval) -> Run:
    """Approve resumes the graph; reject fails the run."""
    run = approval.run
    if approval.status == "approved":
        return advance(db, run)
    run.status = "failed"
    run.task.status = "failed"
    run.error_summary = f"Rejected at gate {approval.gate}"
    run.finished_at = _now()
    db.commit()
    return run
