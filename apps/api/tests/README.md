# apps/api/tests

Purpose: pytest suite for the ALLinONE API (in-process TestClient, SQLite).

Run: cd apps/api && PYTHONPATH=. ../../.venv/bin/pytest -q
- test_api.py: health, auth, task create, approval flow, viewer permissions.
- test_tools.py: tool stubs, allowlist, webhook endpoint.
Note: tests target legacy routes until Backend aligns with the /api/v1 contract.
