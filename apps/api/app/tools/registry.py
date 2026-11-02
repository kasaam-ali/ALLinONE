"""Tool registry: registers stub tools and enforces per-agent allowlists on invoke."""
from .base import ToolResult
from .http_fetch import HttpFetchStub
from .browser_stub import BrowserStub
from .webhook_inbound import WebhookInboundStub

KNOWN_STUB_TOOLS = ("http_fetch", "browser_stub", "webhook_inbound")
_REGISTRY: dict = {}

class ToolNotAllowed(PermissionError): pass

def register(tool):
    if not getattr(tool, "is_stub", False):
        raise ValueError("only stub tools may be registered without CTO/Kasaam approval")
    _REGISTRY[tool.name] = tool

def validate_allowlist(names) -> list[str]:
    bad = [n for n in names if n not in KNOWN_STUB_TOOLS]
    if bad: raise ValueError(f"unknown tools: {bad}; allowed: {list(KNOWN_STUB_TOOLS)}")
    return list(dict.fromkeys(names))

def invoke(tool_name: str, payload: dict, allowlist: list[str]) -> ToolResult:
    if tool_name not in (allowlist or []):
        raise ToolNotAllowed(f"tool '{tool_name}' not in allowlist {allowlist}")
    if tool_name not in _REGISTRY:
        raise KeyError(f"tool '{tool_name}' not registered")
    return _REGISTRY[tool_name].run(payload or {})

for _t in (HttpFetchStub(), BrowserStub(), WebhookInboundStub()): register(_t)
