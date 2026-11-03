# app/

FastAPI application package for ALLinONE API.

- `orchestrator.py`: LangGraph plan -> research -> execute -> verify -> report (Agentic AI)
- `main.py`: HTTP routes, approvals, audit (Backend)
- `models.py` / `db.py`: ORM and engine (Backend / Database)
- `tools/`: stub tool registry for research/execute stages (Integrations / Backend)

## Orchestrator MVP notes
- Resume: DB `runs.current_stage` restart via `resume_after_gate` (no LangGraph checkpointer yet).
- start/decide: inline blocking; Redis worker is DevOps later.
- Memory: `memory_hooks.py`; tools: `run_phase_tools` on research/execute.
