"""Purpose: Unit tests for memory_hooks used by the LangGraph orchestrator."""
import os
from pathlib import Path

# Keep env aligned with suite; do not rebind DATABASE_URL after app import elsewhere.
os.environ.setdefault("GODMODE_MOCK_LLM", "1")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-bytes-long!!")
os.environ.setdefault("GODMODE_REQUIRE_JWT_SECRET", "0")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.memory_hooks import format_context, load_context, memory_key, upsert_stage_memory
from app.models import MemoryItem  # noqa: F401 - register metadata


def _session(tmp_path):
    db_path = Path(tmp_path) / "mem.db"
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)()


def test_memory_hooks_upsert_and_load(tmp_path):
    db = _session(tmp_path)
    try:
        m = upsert_stage_memory(
            db, task_id=9001, run_id=42, stage="plan", content="plan summary"
        )
        db.commit()
        assert m.key == memory_key(42, "plan")
        assert m.scope == "task" and m.scope_id == "9001"
        again = upsert_stage_memory(
            db, task_id=9001, run_id=42, stage="plan", content="plan summary v2"
        )
        db.commit()
        assert again.id == m.id
        assert again.content.startswith("plan summary v2")
        items = load_context(db, 9001)
        assert any(i.key == memory_key(42, "plan") for i in items)
        blurb = format_context(items)
        assert "Memory context:" in blurb and "plan summary v2" in blurb
    finally:
        db.close()


def test_format_context_empty():
    assert format_context([]) == ""
