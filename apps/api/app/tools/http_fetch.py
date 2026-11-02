"""STUB http_fetch: deterministic fake response. Never opens a socket."""
import hashlib
from .base import stub_result

class HttpFetchStub:
    name = "http_fetch"; is_stub = True
    def run(self, payload):
        url = str(payload.get("url", "")); method = str(payload.get("method", "GET")).upper()
        digest = hashlib.sha256(f"{method} {url}".encode()).hexdigest()[:12]
        return stub_result(self.name, {"url": url, "method": method, "status_code": 200,
            "headers": {"content-type": "text/plain", "x-godmode-stub": "1"},
            "body": f"[stub http_fetch {method} {url}] fingerprint={digest}"})

def http_fetch(url: str, method: str = "GET", **kw):
    return HttpFetchStub().run({"url": url, "method": method, **kw})
