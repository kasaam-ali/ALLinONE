<!--
Job: GODMODE Database
Purpose: Document infra assets (Postgres migrations and Redis key design) for local MVP.
-->

# infra

Postgres migrations and Redis key documentation for GODMODE.

## Contents

| Path | Purpose |
|------|---------|
| `migrations/` | Ordered SQL migrations (`001_init.sql`, `002_seed.sql`) |
| `redis.md` | Redis key map for run locks, approval notify, sessions |

## Apply (Postgres)

```bash
psql "$DATABASE_URL" -f infra/migrations/001_init.sql
psql "$DATABASE_URL" -f infra/migrations/002_seed.sql
```

Admin user password is hashed by the API seed from `GODMODE_ADMIN_PASSWORD` / `SEED_ADMIN_PASSWORD` (see repo `.env.example`).

## Notes

- Schema matches Architect SoT: `/workspace/godmode/handoffs/ARCHITECTURE.md`
- Backend ORM must use these table names (`runs`, `stage_events`, `agent_definitions`, etc.)
