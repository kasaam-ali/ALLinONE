<!--
Job: GODMODE Database
Purpose: Redis key design for run locks, approval notify, sessions, and short-lived cache.
-->

# GODMODE Redis keys (Architect lock: run / approval)

Owner: GODMODE Database  
Updated: 2026-11-03 Asia/Karachi  
Postgres is the source of truth. Redis holds locks, sessions/jti, notify channels, and an optional queue.

## Prefix

`gm:` (legacy scaffold used `godmode:jobs`; migrate callers to the patterns below)

## Run / approval (required)

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `gm:lock:run:{run_id}` | string (worker_id) | 30s refresh | Exclusive stage mutation (Architect `run:{id}:lock`) |
| `gm:notify:run:{run_id}` | pub/sub | none | UI poll wake after stage/approval change |
| `gm:queue:runs` | list | none | Run ids ready for worker (`BRPOP`) |
| `gm:queue:approvals` | list | none | Notify fan-out when Approval becomes pending |
| `gm:idempotency:approval:{run_id}:{gate}` | string | 24h | Decide idempotency companion (Postgres remains SoT; HTTP 409 if non-pending) |

### Lock value

```json
{"worker_id":"api-1","run_id":"...","acquired_at":"ISO-8601"}
```

### Queue element

```json
{"run_id":"uuid","attempt":1,"enqueued_at":"ISO-8601"}
```

## Session / auth

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `gm:session:{session_id}` | string JSON | 7d sliding | Session blob |
| `gm:jti:deny:{jti}` | string | until access exp | JWT denylist after logout |
| `gm:session:user:{user_id}` | set | 7d | Revoke-all helper |

## Cache (optional, short TTL)

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `gm:cache:task:{task_id}` | string JSON | 60s | Task card |
| `gm:cache:dashboard` | string JSON | 15s | Command Center summary |

## Env

```
REDIS_URL=redis://localhost:6379/0
REDIS_RUN_LOCK_TTL_SECONDS=30
REDIS_SESSION_TTL_SECONDS=604800
```

## Non-goals (MVP)

No Redis Streams, no embeddings in Redis, no dual-write of Approval status (gates live in Postgres only).
