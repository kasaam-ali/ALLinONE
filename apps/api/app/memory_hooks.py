"""Job: GODMODE Agentic AI. Purpose: Persist and load scoped MemoryItem rows for runs.

MVP memory (ADR-007): text store only, no embeddings. Scopes used here: global + task.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import MemoryItem

STAGE_IMPORTANCE = {
    "plan": 2,
    "research": 3,
    "execute": 3,
    "verify": 4,
    "report": 5,
}


def _now():
    return datetime.now(timezone.utc)


def memory_key(run_id: int, stage: str) -> str:
    return f"run:{run_id}:stage:{stage}"


def load_context(db: Session, task_id: int, *, limit: int = 20) -> list[MemoryItem]:
    """Return global + task-scoped memory for a task, newest first, capped."""
    tid = str(task_id)
    rows = (
        db.query(MemoryItem)
        .filter(
            ((MemoryItem.scope == "global") & (MemoryItem.scope_id.is_(None)))
            | ((MemoryItem.scope == "task") & (MemoryItem.scope_id == tid))
        )
        .order_by(MemoryItem.importance.desc(), MemoryItem.id.desc())
        .limit(limit)
        .all()
    )
    # Drop expired
    now = _now()
    return [m for m in rows if m.expires_at is None or m.expires_at > now]


def format_context(items: list[MemoryItem]) -> str:
    if not items:
        return ""
    lines = [f"- [{m.scope}] {m.key}: {m.content[:240]}" for m in items]
    return "Memory context:\n" + "\n".join(lines)


def upsert_stage_memory(
    db: Session,
    *,
    task_id: int,
    run_id: int,
    stage: str,
    content: str,
) -> MemoryItem:
    """Write or refresh task-scoped memory for a completed stage. Returns the row."""
    key = memory_key(run_id, stage)
    tid = str(task_id)
    row = (
        db.query(MemoryItem)
        .filter_by(scope="task", scope_id=tid, key=key)
        .first()
    )
    body = (content or "")[:4000]
    importance = STAGE_IMPORTANCE.get(stage, 1)
    if row:
        row.content = body
        row.importance = importance
    else:
        row = MemoryItem(
            scope="task",
            scope_id=tid,
            key=key,
            content=body,
            importance=importance,
        )
        db.add(row)
    db.flush()
    return row
