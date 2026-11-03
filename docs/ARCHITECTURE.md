# ALLinONE Architecture (Architect handoff)

Updated: 2026-11-03 ~00:27 Asia/Karachi (SoT synced to live Backend DTOs)
Owner: ALLinONE Architect → CTO
**Status: CTO LOCKED for MVP** (2026-11-03). Cuts: no WS, no AgentInstance multiplicity, Memory w/o embeddings, `GODMODE_MOCK_LLM=1` required.  
Stack: locked (see `/workspace/godmode/STACK.md`)  
Repo target: `/workspace/godmode/repo` → `apps/web`, `apps/api`, `packages/shared`, `infra/`

## 1. Domain entities + relationships

```
User 1──* Task
User 1──* ApprovalDecision (as decided_by)
User 1──* AuditLog (as actor)

AgentDefinition 1──* AgentInstance (MVP may collapse to 1:1)
AgentDefinition 1──* StageEvent (as executor)

Task 1──* Run
Task 1──* Report
Task *──0..1 Task (parent_task_id, optional subtasks)

Run 1──* StageEvent
Run 1──* Artifact
Run 1──* Approval
Run 1──0..1 Report

MemoryItem (scoped: global | user | task | agent) - soft refs via scope+scope_id
```

### Entity fields (MVP)

| Entity | Key fields |
|--------|------------|
| **User** | id, email, display_name, role(`admin`\|`operator`\|`viewer`), password_hash, is_active, timestamps |
| **AgentDefinition** | id, slug, name, role_prompt, tools_allowlist(jsonb), model_config_json(jsonb), status(`active`\|`disabled`), version, created_by. **Live Agent DTO**: `id`, `slug`, `name`, `role_prompt`, `tools_allowlist`, `status`, `version` |
| **AgentInstance** | id, definition_id, label, runtime_status(`idle`\|`busy`\|`error`\|`offline`), last_heartbeat_at - **cut if behind** |
| **Task** | id, title, description, priority, status, created_by, assigned_orchestrator, parent_task_id? |
| **Run** | id, task_id, status, current_stage(`plan`\|`research`\|`execute`\|`verify`\|`report`), mock_llm, started_at, finished_at, error_summary |
| **StageEvent** | id, run_id, stage, status(`started`\|`succeeded`\|`failed`\|`skipped`), agent_definition_id?, input_ref, output_ref, timestamps |
| **Artifact** | id, run_id, stage, kind(`plan`\|`research`\|`result`\|`verification`\|`report`\|`other`), body_text \| storage_uri, mime |
| **Approval** | id, run_id, gate(`after_plan`\|`before_execute`\|`before_publish`), status(`pending`\|`approved`\|`rejected`), decided_by?, decision_note?, decided_at? |
| **AuditLog** | id, actor_user_id?, action, entity_type, entity_id, before_json(jsonb), after_json(jsonb), created_at - **append-only** |
| **MemoryItem** | id, scope, scope_id?, key, content(jsonb/text), importance, expires_at? |
| **Report** | id, run_id, task_id, title, body_md, status(`draft`\|`published`), published_by?, published_at? |

**Task/Run status:** `draft` → `queued` → `running` → `awaiting_approval` → `running` → `succeeded` \| `failed` \| `cancelled`

**SoT:** Postgres for all domain state. Redis: run locks, session/jti blacklist, pubsub/notify, optional job queue.

---

## 2. API surface (`/api/v1`)

### Auth
- `POST /auth/login` `{email,password}` → access + refresh
- `POST /auth/refresh`
- `GET /auth/me`

### Users (admin)
- `GET /users`, `POST /users`, `PATCH /users/{id}` (role, is_active)

### Workforce
- `GET /agents`, `POST /agents`, `GET /agents/{id}`, `PATCH /agents/{id}`
- `POST /agents/{id}/disable`

### Tasks & runs
- `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`
- `POST /tasks/{id}/start` → create Run, enqueue LangGraph
- `GET /runs/{id}`, `GET /runs/{id}/events`, `GET /runs/{id}/artifacts`
- `POST /runs/{id}/cancel` (operator+)

### Approvals
- `GET /approvals?status=pending`
- `POST /approvals/{id}/decide` `{decision: approve|reject, note?}` (operator+)

### Memory
- `GET /memory`, `POST /memory`, `GET|PATCH|DELETE /memory/{id}` (scoped by role)

### Reports
- `GET /reports`, `GET /reports/{id}`
- `POST /reports/{id}/publish` (operator+)

### Command Center
- `GET /dashboard/summary` - **live DTO only**: `tasks_total`, `tasks_by_status`, `runs_by_status`, `pending_approvals`, `agents_active`, `reports_total`, `recent_audit` (do **not** invent old KPI fields like `running` / `failed_24h` / `agents_by_status`)
- `GET /audit` - filter entity_type, entity_id, limit (admin/operator)

### Health
- `GET /health`, `GET /ready` (db + redis)

**MVP transport:** HTTP + poll. WebSocket `WS /runs/{id}/stream` = cut-candidate.

**AuthZ:** viewer = read; operator = start/cancel/approve/publish; admin = users + disable agents. Enforce on API, not UI.

**shared:** `packages/shared` DTOs aligned with OpenAPI (TaskStatus, Stage, Role, Gate, ApprovalDecision).

---

## Live API DTOs (Backend SoT, Frontend adapted)

Synced 2026-11-03 to live `apps/api` serializers. Frontend already adapted. **Do not invent old KPI fields.**

### `GET /api/v1/dashboard/summary` → `DashboardSummary`
- `tasks_total` (int)
- `tasks_by_status` (object status→count)
- `runs_by_status` (object status→count)
- `pending_approvals` (int)
- `agents_active` (int)
- `reports_total` (int)
- `recent_audit` (array of Audit DTO, last 10)

### Agent (list/get/create/patch response)
- `slug`, `role_prompt`, `tools_allowlist`, `status` (`active`|`disabled`)
- also live: `id`, `name`, `version`

### User (`/auth/me` and user serializers)
- `display_name` (plus `id`, `email`, `role`)

### Audit (`/audit` and `recent_audit` items)
- `actor_user_id`, `after_json` (plus `id`, `action`, `entity_type`, `entity_id`, `created_at`; store also has `before_json`)

### Stubs
- `GET /api/v1/integrations` (auth read): returns `[]` (stub; no third-party integrations yet)

## 3. Approval-gate state machine

Default gates (configurable later; MVP hardcode both):

1. **`after_plan`** - after plan stage succeeds, before research  
2. **`before_publish`** - after verify succeeds, before report marked published (execute still auto after research if after_plan approved)

```
                    ┌─────────┐
                    │  queued │
                    └────┬────┘
                         │ start
                         ▼
                    ┌─────────┐
              ┌─────│ running │◄──────────────────────┐
              │     └────┬────┘                       │
              │          │ stage=plan                 │
              │          ▼                            │
              │   StageEvent plan succeeded           │
              │          │                            │
              │          ▼                            │
              │  create Approval(gate=after_plan)     │
              │          │                            │
              │          ▼                            │
              │ ┌──────────────────┐                  │
              │ │ awaiting_approval│                  │
              │ └────────┬─────────┘                  │
              │     ┌────┴────┐                       │
              │  reject    approve                    │
              │     │         │                       │
              │     ▼         ▼                       │
              │  failed/   running                    │
              │ cancelled  research→execute→verify    │
              │                    │                  │
              │                    ▼                  │
              │         create Approval               │
              │         (gate=before_publish)         │
              │                    │                  │
              │                    ▼                  │
              │         awaiting_approval ────────────┤
              │              │                        │
              │         approve → publish Report      │
              │              │         + run=succeeded│
              │         reject → run=failed/cancelled │
              └──────────────────────────────────────┘
```

### Invariants
- Never advance past a gate without `Approval.status=approved` for that `run_id+gate`.
- `awaiting_approval` is Run.status; stage pointer stays on completed stage until approve.
- Decide is idempotent: second decide on non-pending → 409.
- Every transition writes `StageEvent` + `AuditLog`.
- Cancel from queued/running/awaiting_approval → `cancelled` (operator+); pending Approvals → rejected with system note `cancelled`.
- `GODMODE_MOCK_LLM=1`: deterministic fake artifacts per stage; same gate rules apply.

### Redis
- Lock key `run:{id}:lock` while worker mutates stage.
- Pubsub `run:{id}` for UI poll wake (optional).

---

## 4. ADR risks (file as ADRs when repo has `docs/adr/`)

| ID | Decision / risk | Call |
|----|-----------------|------|
| **ADR-001** | Mock LLM behind `GODMODE_MOCK_LLM` | **Accept** - ship CI/compose with zero keys; real provider later |
| **ADR-002** | Postgres SoT for run+approval; Redis locks only | **Accept** - avoids dual-write drift |
| **ADR-003** | Two hard gates: after_plan + before_publish | **Accept for MVP** - skip before_execute to save time |
| **ADR-004** | JWT roles in claims + DB role as source on refresh | **Accept** - DevOps hardens secrets/rotation |
| **ADR-005** | Shared types via OpenAPI export → TS | **Accept** - hand-sync only if generator late |
| **ADR-006** | No WebSocket / no AgentInstance multiplicity if behind | **Accept cut** - poll + AgentDefinition only |
| **ADR-007** | Memory without embeddings tonight | **Accept** - text/jsonb store only |
| **ADR-008** | Browser tools only with existing credentials | **Accept** - Integrations owns; Architect does not block MVP on live browser |

### Schedule killers (watch)
1. LangGraph not stubbed first → whole pipeline blocked  
2. Frontend/Backend DTO drift  
3. Approval transitions without audit/stage events → QA fails honesty bar  

---

## 5. IMPLEMENTATION_STATUS structure (Architect owns honesty)

Keep `/workspace/godmode/IMPLEMENTATION_STATUS.md` (and mirror in-repo when scaffold lands) with:

- Phase / working E2E yes-no / evidence  
- Checklist per slice: auth, workforce, runs+graph, approvals, memory, reports, dashboard, compose  
- Status values: `stub` \| `wip` \| `done` \| `blocked` - **done requires runnable proof**  
- Blockers + Bugs - no fake green  

---

## 6. Next for Backend / Database

- DB: tables + enums + seed admin/operator/viewer + sample AgentDefinitions  
- API: auth + tasks/runs/approvals stubs wiring mock graph  
- Agentic: graph nodes plan→research→execute→verify→report honoring gates + mock mode  
