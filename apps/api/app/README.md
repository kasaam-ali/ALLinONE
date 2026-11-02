# app/

FastAPI application package for GODMODE API.

- `orchestrator.py`: LangGraph plan -> research -> execute -> verify -> report (Agentic AI)
- `main.py`: HTTP routes, approvals, audit (Backend)
- `models.py` / `db.py`: ORM and engine (Backend / Database)
- `tools/`: stub tool registry for research/execute stages (Integrations / Backend)
