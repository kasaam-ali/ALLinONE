# GODMODE Stack (CTO lock - 2026-11-03 PKT)

## Goal
Runnable MVP: natural-language business task → AI agents plan/research/execute/verify/report.

## Locked stack
- Frontend: Next.js (App Router) + React + TypeScript
- Backend: FastAPI (Python 3.12+)
- Orchestration: LangGraph multi-agent (plan → research → execute → verify → report)
- DB: PostgreSQL + Redis (queues/cache/session)
- Auth: session/JWT + role permissions (admin/operator/viewer) - DevOps hardens
- Deploy: Docker Compose for local MVP; production deploy needs Kasaam yes
- Monorepo: `apps/web`, `apps/api`, `packages/shared` (types), `infra/`

## MVP surfaces (must ship by 7:00 AM PKT)
1. Command Center dashboard
2. Workforce management (agents/roles)
3. Multi-agent orchestration + planning/delegation
4. Browser+API tools where credentials exist
5. Human approval gates
6. Activity/audit logs
7. Persistent memory
8. Reports/analytics
9. Secure auth + permissions

## Non-goals tonight
Polish UI, DaleelAI/Elevate/Slack work, paid services without Kasaam yes, production deploy without yes.
