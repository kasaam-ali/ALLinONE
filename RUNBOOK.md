# GODMODE Local Runbook

LOCAL ONLY. Compose binds ports to 127.0.0.1 only. No production, Railway, or Vercel deploy without Kasaam's approval via CTO.

## Prerequisites
- Docker with the Compose plugin (`docker compose version`).

## Start
```bash
cd /workspace/godmode/repo
cp .env.example .env
# Edit .env: JWT_SECRET must be >=32 chars (openssl rand -hex 32), plus POSTGRES_PASSWORD, SEED_ADMIN_PASSWORD
docker compose up --build -d
docker compose ps
```

## URLs
- Web: http://localhost:3010
- API health: http://localhost:8010/health
- API docs (FastAPI): http://localhost:8010/docs

## Seed admin (dev defaults, not secrets)
- Email: value of `SEED_ADMIN_EMAIL` (default `admin@godmode.local`)
- Password: value of `SEED_ADMIN_PASSWORD` in your `.env`. The API code falls back to `godmode123` only if unset. Change it after first login.
- The admin is created on API startup only if that email does not exist yet.

## Stop / reset
```bash
docker compose down        # stop, keep data
docker compose down -v     # stop and DELETE the postgres volume (fresh DB)
docker compose logs -f api # follow API logs
```

## Run API tests (no Docker)
```bash
cd /workspace/godmode/repo/apps/api
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

## Troubleshooting
- Postgres not ready / API crash loop: `docker compose logs postgres`; API waits for the healthcheck. If you changed `POSTGRES_PASSWORD` after first run, the old volume keeps the old password, so run `docker compose down -v`.
- JWT_SECRET / InsecureKeyLengthWarning: set `JWT_SECRET` to at least 32 characters in `.env` (see `.env.example`). API refuses to start if shorter.
- CORS error in browser: add the exact origin (scheme+host+port) to `CORS_ORIGINS` in `.env`, then `docker compose up -d api`. `*` is ignored.
- `POSTGRES_PASSWORD` required error: you did not create `.env`.
- Port in use: stop the other process on 3010/8010/5432/6379.
- Schema: the API runs `create_all` on startup. `infra/migrations/001_init.sql` is the canonical reference and is not auto-applied.

## Host ports

Host ports 8000 and 3000 are used by other apps on this box. GODMODE maps API to 127.0.0.1:8010 (container 8000) and web to 127.0.0.1:3010 (container 3000). Postgres 5432 and Redis 6379 bind to 127.0.0.1 only. Inside the compose network the web container reaches the API at http://api:8000.

## Docker on the box (2026-11-03)
Docker works on the box with `dockerd --iptables=false` plus `docker-compose.box.yml` (host networking, same ports 8010/3010). See handoffs/DOCKER_STATUS.md. API smoke: `scripts/smoke-local.sh`.
