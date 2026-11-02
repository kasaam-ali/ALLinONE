"""Job: GODMODE Backend stub. Purpose: Placeholder for Agentic AI LangGraph ownership.
Gates locked by Architect: after_plan then before_publish only. No before_execute.
"""
import os

MOCK = os.getenv("GODMODE_MOCK_LLM", "1") == "1"
GATES = ("after_plan", "before_publish")


def enqueue_run(run_id: int) -> dict:
    """Stub start hook. Agentic AI replaces this with real graph execution."""
    return {
        "enqueued": True,
        "run_id": run_id,
        "mock_llm": MOCK,
        "gates": list(GATES),
        "note": "Orchestration stub; Agentic AI owns LangGraph plan-research-execute-verify-report",
    }
