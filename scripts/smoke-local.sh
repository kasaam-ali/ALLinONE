#!/usr/bin/env bash
# Smoke test for the GODMODE API on host port 8010.
# If nothing listens on 8010, starts a local API (SQLite, GODMODE_MOCK_LLM=1) and stops it on exit.
# If an API already listens (dev-local.sh or docker compose), it is reused.
# Checks: GET /health, GET /ready, POST /api/v1/auth/login, GET /api/v1/dashboard/summary.
# Web checks are separate: cd apps/web && npx vitest run && npm run build
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="${API_BASE:-http://127.0.0.1:8010}"
EMAIL="${SMOKE_EMAIL:-admin@godmode.local}"
PASS="${SMOKE_PASSWORD:-${GODMODE_ADMIN_PASSWORD:-godmode123}}"
PID=""
fail() { echo "SMOKE FAIL: $*" >&2; exit 1; }
cleanup() { [ -n "$PID" ] && kill "$PID" 2>/dev/null || true; }
trap cleanup EXIT

if ! curl -fsS -m 3 "$BASE/health" >/dev/null 2>&1; then
  echo "No API on $BASE; starting local API (SQLite, mock LLM)"
  [ -d .venv ] || python3 -m venv .venv
  . .venv/bin/activate
  pip install -q -r apps/api/requirements.txt
  mkdir -p .smoke
  (cd apps/api && \
    GODMODE_MOCK_LLM=1 \
    DATABASE_URL="sqlite:///$PWD/../../.smoke/smoke.db" \
    JWT_SECRET="${JWT_SECRET:-smoke-local-secret-at-least-32-bytes-long}" \
    GODMODE_ADMIN_PASSWORD="$PASS" \
    exec uvicorn app.main:app --host 127.0.0.1 --port 8010) > .smoke/api.log 2>&1 &
  PID=$!
  for _ in $(seq 1 30); do curl -fsS -m 2 "$BASE/health" >/dev/null 2>&1 && break; sleep 1; done
  curl -fsS -m 2 "$BASE/health" >/dev/null 2>&1 || { tail -n 30 .smoke/api.log >&2; fail "API did not start on 8010"; }
else
  echo "Reusing API already on $BASE"
fi

echo "GET /health:  $(curl -fsS "$BASE/health" || fail /health)"
echo "GET /ready:   $(curl -fsS "$BASE/ready" || fail /ready)"
TOKEN=$(curl -fsS -X POST "$BASE/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])') || fail "login as $EMAIL"
echo "POST /api/v1/auth/login: ok (token len ${#TOKEN})"
SUM=$(curl -fsS "$BASE/api/v1/dashboard/summary" -H "Authorization: Bearer $TOKEN") || fail "dashboard/summary"
echo "GET /api/v1/dashboard/summary: $SUM"
echo "SMOKE OK (API only; web vitest/build is a separate check)"
