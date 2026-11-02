"""Map AgentDefinition rows to orchestrator runtime agent dicts (tools_allowlist)."""
from __future__ import annotations

# slug/name hints → phase role string used by orchestrator._agent matching
_ROLE_HINTS = (
    ("plan", "planner"),
    ("research", "research"),
    ("scout", "research"),
    ("execute", "execute"),
    ("forge", "execute"),
    ("verify", "verify"),
    ("sentinel", "verify"),
    ("report", "report"),
    ("scribe", "report"),
)


def infer_role(slug: str = "", name: str = "", role_prompt: str = "") -> str:
    blob = f"{slug} {name} {role_prompt}".lower()
    for hint, role in _ROLE_HINTS:
        if hint in blob:
            return role
    return "worker"


def definition_to_runtime_agent(defn) -> dict:
    """Build {name, role, tools_allowlist} for orchestrator from an AgentDefinition-like object."""
    slug = getattr(defn, "slug", "") or ""
    name = getattr(defn, "name", "") or slug or "agent"
    role_prompt = getattr(defn, "role_prompt", "") or ""
    allow = list(getattr(defn, "tools_allowlist", None) or [])
    return {
        "id": getattr(defn, "id", None),
        "name": name,
        "role": infer_role(slug, name, role_prompt),
        "tools_allowlist": allow,
        "slug": slug,
    }


def definitions_to_runtime_agents(definitions) -> list[dict]:
    return [definition_to_runtime_agent(d) for d in definitions]
