# GODMODE Command Center (apps/web)

Next.js 14 App Router + React + TypeScript admin UI for GODMODE. It talks only to the `/api/v1` contract defined in `handoffs/ARCHITECTURE.md`.

## Run

```bash
cd apps/web
npm install
npm run dev      # http://localhost:3000
npm run build    # production build
npm test         # Vitest unit and smoke tests (fetch is mocked)
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | `/api/v1` | Base URL used by the browser client. Keep the default to use the proxy. |
| `API_PROXY_TARGET` | `http://localhost:8000/api/v1` | Where Next.js rewrites forward `/api/v1/*`. Read at build/start time. |

## Routes

| Path | Data source |
|------|-------------|
| `/login` | `POST /auth/login`, session via `GET /auth/me` |
| `/` Dashboard | `GET /dashboard/summary` |
| `/tasks` | `GET /tasks` |
| `/tasks/[id]` | `GET /tasks/{id}`, `GET /runs/{id}/events`, `GET /runs/{id}/artifacts`, `GET /approvals`, `POST /approvals/{id}/decide` |
| `/workforce` | `GET /agents` |
| `/activity` | `GET /audit` |
| `/reports` | `GET /reports` |

## Auth

Access and refresh tokens are kept in `localStorage`. A 401 triggers one `POST /auth/refresh`, then a redirect to `/login`. Authorization is enforced by the API, not the UI.

## Behavior when the API is down

Every page shows a loading state, then either real data, an empty state, or an error card with Retry. No demo or invented data is ever shown.

## Layout

- `app/` routes and the app shell
- `components/` shared state and layout components
- `lib/` typed API client, domain types, data hook
- `tests/` Vitest tests
