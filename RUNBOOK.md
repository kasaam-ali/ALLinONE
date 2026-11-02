# GODMODE Local Runbook

LOCAL ONLY. No production, Railway, or Vercel deploy without Kasaam's approval via CTO.

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
- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs (FastAPI): http://localhost:8000/docs

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
- Port in use: stop the other process on 3000/8000/5432/6379.
- Schema: the API runs `create_all` on startup. `infra/migrations/001_init.sql` is the canonical reference and is not auto-applied.
