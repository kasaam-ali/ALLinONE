"""STUB browser: fake page snapshot. No browser is launched."""
from .base import stub_result

ACTIONS = ("open", "snapshot", "click", "type", "extract")

class BrowserStub:
    name = "browser_stub"; is_stub = True
    def run(self, payload):
        action = payload.get("action", "snapshot"); url = payload.get("url") or "about:blank"
        if action not in ACTIONS:
            return {"ok": False, "tool": self.name, "stub": True, "note": "unknown action", "error": f"action must be one of {ACTIONS}"}
        return stub_result(self.name, {"action": action, "url": url, "title": f"Stub page for {url}",
            "snapshot": f"<html><body>[stub browser {action} {url}]</body></html>"})

def browser_stub(action: str = "snapshot", url: str | None = None, **kw):
    return BrowserStub().run({"action": action, "url": url, **kw})
