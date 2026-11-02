"""STUB inbound webhook: validates + records payloads in memory. No external fan-out."""
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from .base import stub_result

INBOX: list[dict] = []  # in-memory only, resets on restart
_SRC = re.compile(r"^[a-z0-9_-]{1,50}$")

class WebhookInboundStub:
    name = "webhook_inbound"; is_stub = True
    def run(self, payload):
        source = str(payload.get("source", "")); body = payload.get("body")
        if not _SRC.match(source):
            return {"ok": False, "tool": self.name, "stub": True, "note": "invalid source", "error": "source must match [a-z0-9_-]{1,50}"}
        if not isinstance(body, dict):
            return {"ok": False, "tool": self.name, "stub": True, "note": "invalid body", "error": "body must be a JSON object"}
        rec = {"id": len(INBOX) + 1, "source": source, "body": body, "received_at": datetime.now(timezone.utc).isoformat()}
        INBOX.append(rec)
        return stub_result(self.name, {"recorded": rec["id"], "source": source, "fanout": False})

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/webhooks/{source}")
async def inbound(source: str, request: Request):
    try: body = await request.json()
    except Exception: raise HTTPException(400, "JSON body required")
    r = WebhookInboundStub().run({"source": source, "body": body})
    if not r["ok"]: raise HTTPException(422, r["error"])
    return r

@router.get("/tools")
def list_tools():
    from . import KNOWN_STUB_TOOLS
    return {"stub": True, "tools": [{"name": n, "stub": True} for n in KNOWN_STUB_TOOLS]}
