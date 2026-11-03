<!--
Job: ALLinONE Database
Purpose: Redis key design for run locks, approval notify, sessions, and short-lived cache.
-->

# ALLinONE Redis keys (Architect lock: run / approval)

Owner: ALLinONE Database  
Updated: 2026-11-03 Asia/Karachi  
Postgres is the source of truth. Redis holds locks, sessions/jti, notify channels, and an optional queue.

## Prefix

`gm:` (legacy scaffold used `godmode:jobs`; migrate callers to the patterns below)

## Run / approval (required)

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `gm:lock:run:{run_id}` | string (worker_id) | 30s refresh | Exclusive stage mutation |
| `gm:notify:run:{run_id}` | pub/sub | none | UI poll wake after stage/approval change |
| `gm:queue:runs` | list | none | Run ids ready for worker (`BRPOP`) |
| `gm:queue:approvals` | list | none | Notify fan-out when Approval becomes pending |
| `gm:idempotency:approval:{run_id}:{gate}` | string | 24h | Decide idempotency companion (Postgres remains SoT; HTTP 409 if non-pending) |

## Gates (G2)

Approval gates in Postgres are only `after_plan` and `before_publish`. Report publish stores `publish_approval_id` for the approved `before_publish` row.

## Env

```
REDIS_URL=redis://localhost:6379/0
REDIS_RUN_LOCK_TTL_SECONDS=30
REDIS_SESSION_TTL_SECONDS=604800
```
