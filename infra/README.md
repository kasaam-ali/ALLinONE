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

## G2 notes

- Primary tables: `runs`, `stage_events`, `artifacts` (not `plans` / `steps`)
- Approval gates only: `after_plan`, `before_publish`
- `reports.status=published` requires `publish_approval_id` pointing at an approved `before_publish` row

Admin password is hashed by the API seed from `GODMODE_ADMIN_PASSWORD` / `SEED_ADMIN_PASSWORD`.
