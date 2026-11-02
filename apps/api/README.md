# GODMODE API (`apps/api`)

Job: FastAPI backend for GODMODE Autonomous Digital Workforce.

## What this package provides

- Architect-locked `/api/v1` HTTP API (auth, agents, tasks, runs, approvals, memory, reports, dashboard, audit)
- JWT roles: `admin`, `operator`, `viewer`
- Approval gates: `after_plan` and `before_publish` only
- SQLite by default for local MVP; Postgres via `DATABASE_URL`
- Stub orchestration hook for Agentic AI LangGraph ownership
- Integrations stub tools under `/integrations/*`

## Run locally

```bash
cd apps/api
source ../../.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
cd apps/api
../../.venv/bin/pytest -q
```

`pytest.ini` sets `pythonpath = .` so `PYTHONPATH` is not required.

## Seed users

- admin@godmode.local / godmode123 (override via GODMODE_ADMIN_* or alias SEED_ADMIN_*)
- operator@godmode.local / godmode123
- viewer@godmode.local / godmode123
