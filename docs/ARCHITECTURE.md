# Architecture

## Overview

```
Browser (Next.js) --JWT--> FastAPI --SQLAlchemy--> PostgreSQL
                              |
                              +--> LangGraph orchestrator (mock LLM)
                              +--> Redis queue (stub)
```

## Request flow for a task

1. `POST /tasks` stores the task and runs the LangGraph graph from the `plan` node.
2. If the task requires approval, the graph routes to a pause node. The API stores the plan, its steps, and a pending approval, and sets status `awaiting_approval`.
3. `POST /approvals/{id}/approve` resumes the run through research, execute, and verify, then writes a report and a memory entry. Status becomes `completed`.
4. `POST /approvals/{id}/reject` marks the task `rejected` and skips pending steps.
5. Every action writes an `audit_logs` row.

## Data model

users, roles, agents (workforce), tasks, plans, steps, approvals, audit_logs, memories, reports. The runtime schema lives in `infra/migrations/000_runtime_schema.sql` and is applied by the API at startup.

## Permissions

| Role | Permissions |
|------|-------------|
| admin | read, write, approve, admin |
| operator | read, write, approve |
| viewer | read |

## MVP limitations

Orchestration runs synchronously inside the request. The Redis queue receives events but no worker consumes them yet. LLM calls are mocked.
