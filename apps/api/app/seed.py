"""Job: ALLinONE Backend. Purpose: Idempotent seed for roles users and agent definitions."""
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import User, AgentDefinition
from .security import hash_pw


def env_first(*names: str, default: str) -> str:
    """Prefer the first non-empty env var among names (GODMODE_* then SEED_* aliases)."""
    for name in names:
        raw = os.getenv(name)
        if raw is not None and str(raw).strip() != "":
            return str(raw).strip()
    return default


def seed(db: Session) -> None:
    admin_email = env_first(
        "GODMODE_ADMIN_EMAIL", "SEED_ADMIN_EMAIL", default="admin@godmode.local"
    )
    admin_password = env_first(
        "GODMODE_ADMIN_PASSWORD", "SEED_ADMIN_PASSWORD", default="godmode123"
    )
    defaults = [
        (admin_email, "Admin", "admin", admin_password),
        ("operator@godmode.local", "Operator", "operator", "godmode123"),
        ("viewer@godmode.local", "Viewer", "viewer", "godmode123"),
    ]
    for email, name, role, password in defaults:
        email_n = email.lower().strip()
        if db.query(User).filter_by(email=email_n).first():
            continue
        db.add(User(email=email_n, display_name=name, role=role, password_hash=hash_pw(password)))
        try:
            db.flush()
        except IntegrityError:
            db.rollback()

    agents = [
        ("planner", "Atlas", "Break objectives into plans", ["http_fetch"]),
        ("researcher", "Scout", "Gather context", ["http_fetch", "browser_stub"]),
        ("executor", "Forge", "Execute steps with tools", ["http_fetch", "browser_stub", "webhook_inbound"]),
        ("verifier", "Sentinel", "Verify outputs", ["http_fetch"]),
        ("reporter", "Scribe", "Write reports", []),
    ]
    admin = db.query(User).filter_by(role="admin").first()
    for slug, name, prompt, tools in agents:
        if db.query(AgentDefinition).filter_by(slug=slug).first():
            continue
        db.add(AgentDefinition(
            slug=slug,
            name=name,
            role_prompt=prompt,
            tools_allowlist=tools,
            status="active",
            created_by=admin.id if admin else None,
        ))
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            admin = db.query(User).filter_by(role="admin").first()
    db.commit()
