# GODMODE

GODMODE is an AI workforce command center. A user describes a business objective in plain language, and a team of AI agents plans, researches, executes, verifies, and reports on it, with human approval gates and a full audit trail.

This repository is the MVP. It runs end to end with a mock LLM, so no API keys are required.

## Features

- Secure auth with JWT and role permissions (admin, operator, viewer)
- Workforce management: create, pause, and delete AI agents
- Natural-language tasks orchestrated by LangGraph: plan, research, execute, verify, report
- Human approval gates that pause the graph until a person approves or rejects
- Audit log of every user and orchestrator action
- Persistent memory and generated reports with summary analytics
- Redis queue stub for background workers

## Tech stack

| Layer | Technology |
|-------|------------|
| Web | Next.js 14 (App Router), React 18, TypeScript |
| API | FastAPI, Python 3.12+, SQLAlchemy 2 |
| Orchestration | LangGraph (mock LLM via `GODMODE_MOCK_LLM=1`) |
| Data | PostgreSQL 16, Redis 7 (SQLite fallback for local dev) |
| Runtime | Docker Compose |

## Quick start (Docker)

```bash
cp .env.example .env        # optional, defaults work for local use
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000 (interactive docs at `/docs`)

## Quick start (no Docker)

Requires Python 3.12+ and Node 20+.

```bash
./scripts/dev-local.sh
```

This starts the API on port 8000 with a local SQLite database and the web app on port 3000.

## Demo credentials

| Email | Password | Role |
|-------|----------|------|
| admin@godmode.local | godmode123 | admin |

Change these with `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` before any shared deployment.

## Try it

1. Sign in with the demo credentials.
2. On Command Center, enter an objective such as "Research our top 3 competitors and draft a pricing memo" and click Launch.
3. The task pauses at an approval gate. Click Approve and run.
4. View the completed plan, the report, the Audit Log, and Reports.

## Tests

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r apps/api/requirements.txt
cd apps/api && python -m pytest -q
```

## Repository layout

```
apps/
  api/          FastAPI service, ORM models, LangGraph orchestrator, tests
  web/          Next.js Command Center
packages/
  shared/       Shared TypeScript types
infra/
  migrations/   SQL schema files
docs/           Architecture notes
scripts/        Local developer scripts
```

## Status

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for what works today and known gaps, and [STACK.md](STACK.md) for the locked stack.

## Security

No secrets are committed. Use `.env` (ignored by git) based on `.env.example`. The default JWT secret is for local development only.
