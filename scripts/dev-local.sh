#!/usr/bin/env bash
# Runs API (SQLite, mock LLM) and web locally without Docker.
set -e
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate && pip install -q -r apps/api/requirements.txt
(cd apps/api && JWT_SECRET=${JWT_SECRET:-local-dev-secret-at-least-32-bytes-long} uvicorn app.main:app --port 8000) &
(cd apps/web && npm install && npm run dev)
