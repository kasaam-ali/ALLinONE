"""Tool interface. All tools are STUBS until Kasaam approves live mode via GODMODE CTO."""
from typing import Any, Protocol, TypedDict

STUB_NOTE = "STUB ONLY: no real outbound. Live mode requires Kasaam approval via GODMODE CTO."

class ToolResult(TypedDict, total=False):
    ok: bool
    tool: str
    stub: bool
    note: str
    data: dict
    error: str

class BaseTool(Protocol):
    name: str
    is_stub: bool
    def run(self, payload: dict[str, Any]) -> ToolResult: ...

def stub_result(tool: str, data: dict) -> ToolResult:
    return {"ok": True, "tool": tool, "stub": True, "note": STUB_NOTE, "data": data}
