"""Job: GODMODE Backend. Purpose: FastAPI entrypoint exposing the canonical /api/v1 contract."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal
from .models import (User, AgentDefinition, Task, Run, StageEvent, Artifact, Approval,
                     AuditLog, MemoryItem, Report)
from .security import check_pw, make_token, make_refresh_token, decode_token, current_user, require
from .seed import seed
from . import orchestrator
from .tools import validate_allowlist
from .tools.webhook_inbound import router as integrations_router


@asynccontextmanager
async def lifespan(_app):
    Base.metadata.create_all(engine)  # infra/migrations/001_init.sql is canonical for Postgres
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="GODMODE API", version="0.2.0", lifespan=lifespan)
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3010").split(",")
            if o.strip() and o.strip() != "*"]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
api = APIRouter(prefix="/api/v1")
api.include_router(integrations_router)


def now():
    return datetime.now(timezone.utc)


def iso(d):
    return d.isoformat() if d else None


def audit(db, actor, action, entity_type="", entity_id=None, before=None, after=None):
    db.add(AuditLog(actor_user_id=actor.id if actor else None, action=action, entity_type=entity_type,
                    entity_id=entity_id, before_json=before, after_json=after))


def get_or_404(db, model, oid):
    obj = db.get(model, oid)
    if not obj:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj


# ---------- schemas ----------
class LoginIn(BaseModel):
    email: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class AgentIn(BaseModel):
    slug: str
    name: str
    role_prompt: str = ""
    tools_allowlist: list[str] = []
    model_config_json: dict = {}

    @field_validator("tools_allowlist")
    @classmethod
    def _v(cls, v):
        return validate_allowlist(v)


class AgentPatch(BaseModel):
    name: str | None = None
    role_prompt: str | None = None
    tools_allowlist: list[str] | None = None
    status: Literal["active", "disabled"] | None = None

    @field_validator("tools_allowlist")
    @classmethod
    def _v(cls, v):
        return validate_allowlist(v) if v is not None else v


class TaskIn(BaseModel):
    title: str
    description: str = ""
    priority: int = 0


class DecideIn(BaseModel):
    decision: Literal["approve", "reject"]
    note: str | None = None


class MemoryIn(BaseModel):
    key: str
    content: str = ""
    scope: str = "global"
    scope_id: str | None = None
    importance: int = 0


class MemoryPatch(BaseModel):
    content: str | None = None
    importance: int | None = None


# ---------- serializers ----------
def user_out(u):
    return {"id": u.id, "email": u.email, "display_name": u.display_name, "role": u.role}


def agent_out(a):
    return {"id": a.id, "slug": a.slug, "name": a.name, "role_prompt": a.role_prompt,
            "tools_allowlist": a.tools_allowlist, "status": a.status, "version": a.version}


def task_out(t):
    latest = max(t.runs, key=lambda r: r.id) if t.runs else None
    return {"id": t.id, "title": t.title, "description": t.description, "priority": t.priority,
            "status": t.status, "latest_run_id": latest.id if latest else None,
            "created_at": iso(t.created_at), "updated_at": iso(t.updated_at)}


def run_out(r):
    return {"id": r.id, "task_id": r.task_id, "status": r.status, "current_stage": r.current_stage,
            "mock_llm": r.mock_llm, "started_at": iso(r.started_at), "finished_at": iso(r.finished_at),
            "error_summary": r.error_summary,
            "pending_approvals": [approval_out(a) for a in r.approvals if a.status == "pending"]}


def event_out(e):
    return {"id": e.id, "run_id": e.run_id, "stage": e.stage, "status": e.status,
            "agent_definition_id": e.agent_definition_id, "output_ref": e.output_ref,
            "created_at": iso(e.created_at)}


def artifact_out(a):
    return {"id": a.id, "run_id": a.run_id, "stage": a.stage, "kind": a.kind, "body_text": a.body_text,
            "mime": a.mime, "created_at": iso(a.created_at)}


def approval_out(a):
    return {"id": a.id, "run_id": a.run_id, "gate": a.gate, "status": a.status,
            "decision_note": a.decision_note, "decided_by": a.decided_by,
            "decided_at": iso(a.decided_at), "created_at": iso(a.created_at)}


def memory_out(m):
    return {"id": m.id, "scope": m.scope, "scope_id": m.scope_id, "key": m.key, "content": m.content,
            "importance": m.importance, "created_at": iso(m.created_at)}


def report_out(r):
    return {"id": r.id, "run_id": r.run_id, "task_id": r.task_id, "title": r.title, "body_md": r.body_md,
            "status": r.status, "published_at": iso(r.published_at)}


# ---------- health ----------
@api.get("/health")
def health():
    return {"status": "ok", "mock_llm": orchestrator.MOCK}


@api.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"db not ready: {exc}") from exc
    from .security import SECRET
    jwt_ok = len(SECRET or "") >= 32
    body = {
        "status": "ready" if jwt_ok else "degraded",
        "db": "ok",
        "jwt_secret_ok": jwt_ok,
        "mock_llm": orchestrator.MOCK,
    }
    if not jwt_ok:
        # Enforce JWT_SECRET length for production-ish readiness without breaking local mock demos
        # unless GODMODE_REQUIRE_JWT_SECRET=1
        if os.getenv("GODMODE_REQUIRE_JWT_SECRET", "0") == "1":
            raise HTTPException(503, body)
    return body


# ---------- auth ----------
@api.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if not u or not u.is_active or not check_pw(body.password, u.password_hash):
        raise HTTPException(401, "Invalid credentials")
    audit(db, u, "auth.login", "user", u.id)
    db.commit()
    return {"access_token": make_token(u), "refresh_token": make_refresh_token(u),
            "token_type": "bearer", "user": user_out(u)}


@api.post("/auth/refresh")
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    data = decode_token(body.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(401, "Refresh token required")
    u = db.get(User, int(data["sub"]))
    if not u or not u.is_active:
        raise HTTPException(401, "User not found")
    # DB role is source of truth on refresh (ADR-004)
    return {
        "access_token": make_token(u),
        "refresh_token": make_refresh_token(u),
        "token_type": "bearer",
        "user": user_out(u),
    }


@api.get("/auth/me")
def me(u: User = Depends(current_user)):
    return user_out(u)


# ---------- agents ----------
@api.get("/agents")
def list_agents(db: Session = Depends(get_db), _=Depends(require("read"))):
    return [agent_out(a) for a in db.query(AgentDefinition).order_by(AgentDefinition.id)]


@api.post("/agents", status_code=201)
def create_agent(body: AgentIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    if db.query(AgentDefinition).filter_by(slug=body.slug).first():
        raise HTTPException(409, "slug exists")
    a = AgentDefinition(**body.model_dump(), created_by=u.id)
    db.add(a)
    db.flush()
    audit(db, u, "agent.create", "agent_definition", a.id, after=agent_out(a))
    db.commit()
    return agent_out(a)


@api.get("/agents/{aid}")
def get_agent(aid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    return agent_out(get_or_404(db, AgentDefinition, aid))


@api.patch("/agents/{aid}")
def patch_agent(aid: int, body: AgentPatch, db: Session = Depends(get_db), u=Depends(require("write"))):
    a = get_or_404(db, AgentDefinition, aid)
    before = agent_out(a)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(a, k, v)
    a.version += 1
    audit(db, u, "agent.update", "agent_definition", a.id, before=before, after=agent_out(a))
    db.commit()
    return agent_out(a)


@api.post("/agents/{aid}/disable")
def disable_agent(aid: int, db: Session = Depends(get_db), u=Depends(require("admin"))):
    a = get_or_404(db, AgentDefinition, aid)
    a.status = "disabled"
    audit(db, u, "agent.disable", "agent_definition", a.id)
    db.commit()
    return agent_out(a)


# ---------- tasks ----------
@api.get("/tasks")
def list_tasks(status: str | None = None, db: Session = Depends(get_db), _=Depends(require("read"))):
    q = db.query(Task)
    if status:
        q = q.filter_by(status=status)
    return [task_out(t) for t in q.order_by(Task.created_at.desc(), Task.id.desc())]


@api.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    t = Task(**body.model_dump(), created_by=u.id, status="draft", assigned_orchestrator="langgraph")
    db.add(t)
    db.flush()
    audit(db, u, "task.create", "task", t.id)
    db.commit()
    return task_out(t)


@api.get("/tasks/{tid}")
def get_task(tid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    t = get_or_404(db, Task, tid)
    return {**task_out(t), "runs": [run_out(r) for r in t.runs]}


@api.post("/tasks/{tid}/start", status_code=201)
def start_task(tid: int, db: Session = Depends(get_db), u=Depends(require("approve"))):
    t = get_or_404(db, Task, tid)
    if any(r.status in ("queued", "running", "awaiting_approval") for r in t.runs):
        raise HTTPException(409, "Task already has an active run")
    r = Run(task_id=t.id, status="queued", mock_llm=orchestrator.MOCK)
    t.status = "queued"
    db.add(r)
    db.flush()
    audit(db, u, "run.start", "run", r.id)
    db.commit()
    orchestrator.start_run(db, r)
    return run_out(r)


# ---------- runs ----------
@api.get("/runs/{rid}")
def get_run(rid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    return run_out(get_or_404(db, Run, rid))


@api.get("/runs/{rid}/events")
def run_events(rid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    r = get_or_404(db, Run, rid)
    return [event_out(e) for e in sorted(r.stage_events, key=lambda e: e.id)]


@api.get("/runs/{rid}/artifacts")
def run_artifacts(rid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    r = get_or_404(db, Run, rid)
    return [artifact_out(a) for a in sorted(r.artifacts, key=lambda a: a.id)]


@api.post("/runs/{rid}/cancel")
def cancel_run(rid: int, db: Session = Depends(get_db), u=Depends(require("approve"))):
    r = get_or_404(db, Run, rid)
    if r.status in ("succeeded", "failed", "cancelled"):
        raise HTTPException(409, f"Run already {r.status}")
    r.status = "cancelled"
    r.task.status = "cancelled"
    r.finished_at = now()
    for a in r.approvals:
        if a.status == "pending":
            a.status = "cancelled"
    audit(db, u, "run.cancel", "run", r.id)
    db.commit()
    return run_out(r)


# ---------- approvals ----------
@api.get("/approvals")
def list_approvals(status: str | None = None, db: Session = Depends(get_db), _=Depends(require("read"))):
    q = db.query(Approval)
    if status:
        q = q.filter_by(status=status)
    return [approval_out(a) for a in q.order_by(Approval.id.desc())]


@api.post("/approvals/{aid}/decide")
def decide(aid: int, body: DecideIn, db: Session = Depends(get_db), u=Depends(require("approve"))):
    a = get_or_404(db, Approval, aid)
    if a.status != "pending":
        raise HTTPException(409, f"Approval already {a.status}")
    a.status = "approved" if body.decision == "approve" else "rejected"
    a.decided_by = u.id
    a.decision_note = body.note
    a.decided_at = now()
    audit(db, u, f"approval.{a.status}", "approval", a.id, after={"gate": a.gate, "note": body.note})
    db.commit()
    run = orchestrator.resume_after_gate(db, a)
    return {"approval": approval_out(a), "run": run_out(run)}


# ---------- memory ----------
@api.get("/memory")
def list_memory(scope: str | None = None, db: Session = Depends(get_db), _=Depends(require("read"))):
    q = db.query(MemoryItem)
    if scope:
        q = q.filter_by(scope=scope)
    return [memory_out(m) for m in q.order_by(MemoryItem.id)]


@api.post("/memory", status_code=201)
def create_memory(body: MemoryIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    m = MemoryItem(**body.model_dump())
    db.add(m)
    db.flush()
    audit(db, u, "memory.create", "memory_item", m.id)
    db.commit()
    return memory_out(m)


@api.get("/memory/{mid}")
def get_memory(mid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    return memory_out(get_or_404(db, MemoryItem, mid))


@api.patch("/memory/{mid}")
def patch_memory(mid: int, body: MemoryPatch, db: Session = Depends(get_db), u=Depends(require("write"))):
    m = get_or_404(db, MemoryItem, mid)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(m, k, v)
    audit(db, u, "memory.update", "memory_item", m.id)
    db.commit()
    return memory_out(m)


@api.delete("/memory/{mid}", status_code=204)
def delete_memory(mid: int, db: Session = Depends(get_db), u=Depends(require("write"))):
    m = get_or_404(db, MemoryItem, mid)
    db.delete(m)
    audit(db, u, "memory.delete", "memory_item", mid)
    db.commit()


# ---------- reports ----------
@api.get("/reports")
def list_reports(db: Session = Depends(get_db), _=Depends(require("read"))):
    return [report_out(r) for r in db.query(Report).order_by(Report.id.desc())]


@api.get("/reports/{rid}")
def get_report(rid: int, db: Session = Depends(get_db), _=Depends(require("read"))):
    return report_out(get_or_404(db, Report, rid))


@api.post("/reports/{rid}/publish")
def publish_report(rid: int, db: Session = Depends(get_db), u=Depends(require("approve"))):
    r = get_or_404(db, Report, rid)
    if r.run_id:
        gate = db.query(Approval).filter_by(run_id=r.run_id, gate="before_publish", status="approved").first()
        if not gate:
            raise HTTPException(409, "before_publish gate not approved")
    r.status = "published"
    r.published_by = u.id
    r.published_at = now()
    audit(db, u, "report.publish", "report", r.id)
    db.commit()
    return report_out(r)


# ---------- dashboard + audit ----------
@api.get("/dashboard/summary")
def dashboard(db: Session = Depends(get_db), _=Depends(require("read"))):
    tasks_by_status = dict(db.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
    runs_by_status = dict(db.query(Run.status, func.count(Run.id)).group_by(Run.status).all())
    return {
        "tasks_total": sum(tasks_by_status.values()),
        "tasks_by_status": tasks_by_status,
        "runs_by_status": runs_by_status,
        "pending_approvals": db.query(Approval).filter_by(status="pending").count(),
        "agents_active": db.query(AgentDefinition).filter_by(status="active").count(),
        "reports_total": db.query(Report).count(),
        "recent_audit": [audit_out(a) for a in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10)],
    }


def audit_out(a):
    return {"id": a.id, "actor_user_id": a.actor_user_id, "action": a.action, "entity_type": a.entity_type,
            "entity_id": a.entity_id, "after_json": a.after_json, "created_at": iso(a.created_at)}


@api.get("/audit")
def list_audit(entity_type: str | None = None, limit: int = 100, db: Session = Depends(get_db),
               _=Depends(require("read"))):
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter_by(entity_type=entity_type)
    return [audit_out(a) for a in q.order_by(AuditLog.id.desc()).limit(min(limit, 500))]




@app.get("/health")
def health_root():
    return health()


@app.get("/ready")
def ready_root(db: Session = Depends(get_db)):
    return ready(db)

app.include_router(api)
