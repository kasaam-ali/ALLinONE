# app/tools

Purpose: the tool interface and registry for ALLinONE agents. Every tool here is a STUB. None of them make real HTTP calls, launch a browser, or deliver webhooks. Live mode needs Kasaam's approval via ALLinONE CTO.

- `base.py`: ToolResult, BaseTool protocol, stub_result helper.
- `registry.py`: KNOWN_STUB_TOOLS, register, validate_allowlist, invoke (enforces the allowlist).
- `http_fetch.py`, `browser_stub.py`: fixed, repeatable fake outputs.
- `webhook_inbound.py`: in-memory inbound webhook stub plus the /integrations router (`GET /integrations` → `[]`, webhooks, tools list).

See /workspace/godmode/handoffs/integrations.md.

- `runtime_agents.py`: maps AgentDefinition rows to orchestrator `{name, role, tools_allowlist}` dicts.
- `stage_tools.py`: `run_phase_tools(phase, prompt, agents)` for research/execute hooks. Agentic should call this from graph nodes.
