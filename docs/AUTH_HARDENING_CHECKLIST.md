# Auth Hardening Checklist

Path: `/workspace/godmode/repo/docs/AUTH_HARDENING_CHECKLIST.md`. Scope: local Docker Compose tonight. Prod items are marked N/A until Kasaam approves a deploy (via CTO).

## JWT
- [x] `JWT_SECRET` read from env (`apps/api/app/security.py`).
- [x] Minimum length 32 characters enforced in all environments (stops PyJWT InsecureKeyLengthWarning).
- [x] If `GODMODE_ENV` (or `ENV`) is `production`/`prod`/`staging`, the built-in dev default secret is refused.
- [x] `.env.example` and `infra/README.md` document the 32-character minimum (`openssl rand -hex 32`).
- [x] HS256 with explicit `algorithms=["HS256"]` on decode; 12h expiry.
- [ ] TODO: refresh tokens / revocation list (Redis) before any real users.
- [ ] TODO: rotate `JWT_SECRET` procedure documented for prod.

## CORS
- [x] `CORS_ORIGINS` is an explicit comma-separated allowlist (default `http://localhost:3000`).
- [x] `*` entries are ignored by the API (`apps/api/app/main.py`), because `allow_credentials=True` must never pair with a wildcard.
- [ ] TODO: narrow `allow_methods`/`allow_headers` from `*` to what the web app uses.

## Roles and permissions
- [x] Roles `admin` / `operator` / `viewer` enforced via `require(perm)` (see `docs/adr/002-authz-matrix.md`).
- [ ] TODO: confirm `/auth/register` cannot self-assign `admin`/`operator` (Database/API owner to verify).

## Seed admin
- [x] Seed admin email/password come from `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`.
- [ ] TODO: change the seed admin password after first login; add a password-change endpoint.
- [ ] TODO: in production, refuse the dev default password `godmode123`.

## Secrets hygiene
- [x] `.env`, `*.db`, `.venv`, `node_modules`, `__pycache__` in root `.gitignore`.
- [x] `.env` excluded from API and web Docker build contexts (`.dockerignore`).
- [x] `.env.example` holds placeholders only.
- [x] Compose binds all ports to `127.0.0.1` only.
- [ ] TODO: confirm no logs print tokens, passwords, or `DATABASE_URL`.
- [ ] TODO: add a secret scanner (e.g. gitleaks) to CI once the repo is on GitHub.

## Transport (prod only, N/A tonight)
- [ ] N/A: HTTPS everywhere, HSTS.
- [ ] N/A: if cookies are used, `Secure`, `HttpOnly`, `SameSite=Lax/Strict`.
- [ ] N/A: rate limiting on `/auth/login`.
