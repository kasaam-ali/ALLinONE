"""Job: GODMODE Backend. Purpose: Idempotent seed for roles users and agent definitions."""
import os
from sqlalchemy.orm import Session
from .models import User, AgentDefinition
from .security import hash_pw


def seed(db: Session) -> None:
    defaults = [
        (os.getenv("GODMODE_ADMIN_EMAIL", "admin@godmode.local"), "Admin", "admin",
         os.getenv("GODMODE_ADMIN_PASSWORD", "godmode123")),
        ("operator@godmode.local", "Operator", "operator", "godmode123"),
        ("viewer@godmode.local", "Viewer", "viewer", "godmode123"),
    ]
    for email, name, role, password in defaults:
        email_n = email.lower().strip()
        if not db.query(User).filter_by(email=email_n).first():
            db.add(User(email=email_n, display_name=name, role=role, password_hash=hash_pw(password)))
    db.flush()

    agents = [
        ("planner-1", "Atlas", "Break objectives into plans", ["http_fetch"]),
        ("researcher-1", "Scout", "Gather context", ["http_fetch", "browser_stub"]),
        ("executor-1", "Forge", "Execute steps with tools", ["http_fetch", "browser_stub", "webhook_inbound"]),
        ("verifier-1", "Sentinel", "Verify outputs", ["http_fetch"]),
        ("reporter-1", "Scribe", "Write reports", []),
    ]
    if db.query(AgentDefinition).count() == 0:
        admin = db.query(User).filter_by(role="admin").first()
        for slug, name, prompt, tools in agents:
            db.add(AgentDefinition(
                slug=slug,
                name=name,
                role_prompt=prompt,
                tools_allowlist=tools,
                status="active",
                created_by=admin.id if admin else None,
            ))
    db.commit()
