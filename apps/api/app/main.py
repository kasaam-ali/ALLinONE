"""Job: GODMODE Backend. Purpose: FastAPI /api/v1 surface per Architect canonical contract."""
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from .db import Base, engine, get_db, SessionLocal
from .models import (
    User, AgentDefinition, Task, Run, StageEvent, Artifact, Approval,
    AuditLog, MemoryItem, Report,
)
from .security import (
    hash_pw, check_pw, make_token, make_refresh_token, decode_token,
    current_user, require,
)
from .seed import seed
from . import orchestrator, queue
from .tools.webhook_inbound import router as integrations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="GODMODE API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(integrations_router)

api = APIRouter(prefix="/api/v1")


def audit(db: Session, user_id, action: str, entity_type: str = "", entity_id=None, before=None, after=None):
    db.add(AuditLog(
        actor_user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
    ))


# ---------- schemas ----------
class LoginIn(BaseModel):
    email: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TaskCreateIn(BaseModel):
    title: str
    description: str = ""
    priority: int = 0


class DecideIn(BaseModel):
    decision: str  # approve|reject
    note: str | None = None


class AgentIn(BaseModel):
    slug: str
    name: str
    role_prompt: str = ""
    tools_allowlist: list[str] = Field(default_factory=list)
    status: str = "active"


class MemoryIn(BaseModel):
    scope: str = "global"
    scope_id: str | None = None
    key: str
    content: str
    importance: int = 0


def user_out(u: User):
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "role": u.role,
        "is_active": u.is_active,
    }


def task_out(t: Task):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "priority": t.priority,
        "status": t.status,
        "created_by": t.created_by,
        "parent_task_id": t.parent_task_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def run_out(r: Run):
    return {
        "id": r.id,
        "task_id": r.task_id,
        "status": r.status,
        "current_stage": r.current_stage,
        "mock_llm": r.mock_llm,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "error_summary": r.error_summary,
    }


def agent_out(a: AgentDefinition):
    return {
        "id": a.id,
        "slug": a.slug,
        "name": a.name,
        "role_prompt": a.role_prompt,
        "tools_allowlist": a.tools_allowlist or [],
        "status": a.status,
        "version": a.version,
    }


# ---------- health ----------
def _health():
    return {"status": "ok", "mock_llm": orchestrator.MOCK}


def _ready(db: Session):
    db.execute(text("SELECT 1"))
    redis_ok = queue.ping_redis()
    require_redis = os.getenv("GODMODE_REQUIRE_REDIS", "0") == "1"
    body = {"status": "ready" if (redis_ok or not require_redis) else "not_ready", "db": True, "redis": redis_ok}
    if require_redis and not redis_ok:
        raise HTTPException(503, body)
    return body


@app.get("/health")
@api.get("/health")
def health():
    return _health()


@app.get("/ready")
@api.get("/ready")
def ready(db: Session = Depends(get_db)):
    return _ready(db)


# ---------- auth ----------
@api.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if not user or not check_pw(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "User inactive")
    audit(db, user.id, "auth.login", "user", user.id)
    db.commit()
    return {
        "access_token": make_token(user),
        "refresh_token": make_refresh_token(user),
        "token_type": "bearer",
        "user": user_out(user),
    }


@api.post("/auth/refresh")
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    data = decode_token(body.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(401, "Refresh token required")
    user = db.get(User, int(data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    # DB role is source of truth on refresh (ADR-004)
    return {
        "access_token": make_token(user),
        "refresh_token": make_refresh_token(user),
        "token_type": "bearer",
        "user": user_out(user),
    }


@api.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


# ---------- users (admin) ----------
@api.get("/users")
def list_users(db: Session = Depends(get_db), user=Depends(require("admin"))):
    return [user_out(u) for u in db.query(User).order_by(User.id)]


# ---------- agents ----------
@api.get("/agents")
def list_agents(db: Session = Depends(get_db), user=Depends(require("read"))):
    return [agent_out(a) for a in db.query(AgentDefinition).order_by(AgentDefinition.id)]


@api.post("/agents", status_code=201)
def create_agent(body: AgentIn, db: Session = Depends(get_db), user=Depends(require("admin"))):
    if db.query(AgentDefinition).filter_by(slug=body.slug).first():
        raise HTTPException(409, "slug exists")
    agent = AgentDefinition(
        slug=body.slug,
        name=body.name,
        role_prompt=body.role_prompt,
        tools_allowlist=body.tools_allowlist,
        status=body.status,
        created_by=user.id,
    )
    db.add(agent)
    db.flush()
    audit(db, user.id, "agent.create", "agent", agent.id, after=agent_out(agent))
    db.commit()
    db.refresh(agent)
    return agent_out(agent)


@api.get("/agents/{agent_id}")
def get_agent(agent_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    agent = db.get(AgentDefinition, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent_out(agent)


@api.post("/agents/{agent_id}/disable")
def disable_agent(agent_id: int, db: Session = Depends(get_db), user=Depends(require("admin"))):
    agent = db.get(AgentDefinition, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.status = "disabled"
    audit(db, user.id, "agent.disable", "agent", agent.id)
    db.commit()
    return agent_out(agent)


# ---------- tasks + runs ----------
@api.post("/tasks", status_code=201)
def create_task(body: TaskCreateIn, db: Session = Depends(get_db), user=Depends(require("write"))):
    if not body.title.strip():
        raise HTTPException(422, "title required")
    task = Task(
        title=body.title.strip(),
        description=body.description,
        priority=body.priority,
        status="draft",
        created_by=user.id,
    )
    db.add(task)
    db.flush()
    audit(db, user.id, "task.create", "task", task.id, after=task_out(task))
    db.commit()
    db.refresh(task)
    return task_out(task)


@api.get("/tasks")
def list_tasks(db: Session = Depends(get_db), user=Depends(require("read"))):
    return [task_out(t) for t in db.query(Task).order_by(Task.id.desc())]


@api.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {**task_out(task), "runs": [run_out(r) for r in task.runs]}


@api.post("/tasks/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db), user=Depends(require("write"))):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status in ("succeeded", "cancelled"):
        raise HTTPException(409, f"cannot start task in status {task.status}")
    mock = os.getenv("GODMODE_MOCK_LLM", "1") == "1"
    now = datetime.now(timezone.utc)
    run = Run(
        task_id=task.id,
        status="queued",
        current_stage="plan",
        mock_llm=mock,
        started_at=now,
    )
    db.add(run)
    db.flush()
    db.add(StageEvent(run_id=run.id, stage="plan", status="started"))
    task.status = "queued"
    audit(db, user.id, "task.start", "run", run.id, after=run_out(run))
    orchestrator.enqueue_run(run.id)
    queue.enqueue("task.start", {"task_id": task.id, "run_id": run.id})
    db.commit()
    db.refresh(run)
    return run_out(run)


@api.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {
        **run_out(run),
        "stage_events": [
            {
                "id": e.id,
                "stage": e.stage,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in run.stage_events
        ],
        "artifacts": [
            {"id": a.id, "stage": a.stage, "kind": a.kind, "mime": a.mime}
            for a in run.artifacts
        ],
    }


@api.get("/runs/{run_id}/events")
def run_events(run_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return [
        {"id": e.id, "stage": e.stage, "status": e.status}
        for e in run.stage_events
    ]


@api.get("/runs/{run_id}/artifacts")
def run_artifacts(run_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return [
        {"id": a.id, "stage": a.stage, "kind": a.kind, "body_text": a.body_text, "mime": a.mime}
        for a in run.artifacts
    ]


@api.post("/runs/{run_id}/cancel")
def cancel_run(run_id: int, db: Session = Depends(get_db), user=Depends(require("write"))):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status in ("succeeded", "failed", "cancelled"):
        raise HTTPException(409, f"already {run.status}")
    run.status = "cancelled"
    run.finished_at = datetime.now(timezone.utc)
    task = db.get(Task, run.task_id)
    if task:
        task.status = "cancelled"
    for approval in run.approvals:
        if approval.status == "pending":
            approval.status = "rejected"
            approval.decision_note = "cancelled"
            approval.decided_at = datetime.now(timezone.utc)
    audit(db, user.id, "run.cancel", "run", run.id)
    db.commit()
    return run_out(run)


# ---------- approvals ----------
@api.get("/approvals")
def list_approvals(status: str = "pending", db: Session = Depends(get_db), user=Depends(require("read"))):
    q = db.query(Approval)
    if status != "all":
        q = q.filter_by(status=status)
    rows = q.order_by(Approval.id.desc()).all()
    return [
        {
            "id": a.id,
            "run_id": a.run_id,
            "gate": a.gate,
            "status": a.status,
            "decision_note": a.decision_note,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


@api.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: int, body: DecideIn, db: Session = Depends(get_db), user=Depends(require("approve"))):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(404, "Approval not found")
    if approval.status != "pending":
        raise HTTPException(409, f"Already {approval.status}")
    decision = body.decision.strip().lower()
    if decision not in ("approve", "reject"):
        raise HTTPException(422, "decision must be approve or reject")
    if approval.gate not in ("after_plan", "before_publish"):
        raise HTTPException(500, "invalid gate")
    approval.status = "approved" if decision == "approve" else "rejected"
    approval.decision_note = body.note
    approval.decided_by = user.id
    approval.decided_at = datetime.now(timezone.utc)
    run = approval.run
    if decision == "reject":
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        task = db.get(Task, run.task_id)
        if task:
            task.status = "failed"
    else:
        # resume stub: leave Agentic AI to advance stages; mark running
        run.status = "running"
        task = db.get(Task, run.task_id)
        if task:
            task.status = "running"
    audit(db, user.id, f"approval.{approval.status}", "approval", approval.id)
    db.commit()
    return {
        "id": approval.id,
        "run_id": approval.run_id,
        "gate": approval.gate,
        "status": approval.status,
        "decision_note": approval.decision_note,
    }


# ---------- memory ----------
@api.get("/memory")
def list_memory(db: Session = Depends(get_db), user=Depends(require("read"))):
    rows = db.query(MemoryItem).order_by(MemoryItem.id.desc()).limit(100).all()
    return [
        {
            "id": m.id,
            "scope": m.scope,
            "scope_id": m.scope_id,
            "key": m.key,
            "content": m.content,
            "importance": m.importance,
        }
        for m in rows
    ]


@api.post("/memory", status_code=201)
def create_memory(body: MemoryIn, db: Session = Depends(get_db), user=Depends(require("write"))):
    item = MemoryItem(
        scope=body.scope,
        scope_id=body.scope_id,
        key=body.key,
        content=body.content,
        importance=body.importance,
    )
    db.add(item)
    db.flush()
    audit(db, user.id, "memory.create", "memory", item.id)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "scope": item.scope, "key": item.key, "content": item.content}


@api.get("/memory/{memory_id}")
def get_memory(memory_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    item = db.get(MemoryItem, memory_id)
    if not item:
        raise HTTPException(404, "Memory not found")
    return {
        "id": item.id,
        "scope": item.scope,
        "scope_id": item.scope_id,
        "key": item.key,
        "content": item.content,
        "importance": item.importance,
    }


# ---------- reports ----------
@api.get("/reports")
def list_reports(db: Session = Depends(get_db), user=Depends(require("read"))):
    rows = db.query(Report).order_by(Report.id.desc()).all()
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "run_id": r.run_id,
            "title": r.title,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@api.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), user=Depends(require("read"))):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return {
        "id": report.id,
        "task_id": report.task_id,
        "run_id": report.run_id,
        "title": report.title,
        "body_md": report.body_md,
        "status": report.status,
    }


@api.post("/reports/{report_id}/publish")
def publish_report(report_id: int, db: Session = Depends(get_db), user=Depends(require("write"))):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    report.status = "published"
    report.published_by = user.id
    report.published_at = datetime.now(timezone.utc)
    audit(db, user.id, "report.publish", "report", report.id)
    db.commit()
    return {"id": report.id, "status": report.status}


# ---------- dashboard + audit ----------
@api.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db), user=Depends(require("read"))):
    running = db.query(Run).filter(Run.status.in_(("running", "queued"))).count()
    awaiting = db.query(Run).filter_by(status="awaiting_approval").count()
    failed_24h = db.query(Run).filter_by(status="failed").count()
    agents_by_status = dict(db.query(AgentDefinition.status, func.count()).group_by(AgentDefinition.status).all())
    return {
        "running": running,
        "awaiting_approval": awaiting,
        "failed_24h": failed_24h,
        "agents_by_status": agents_by_status,
    }


@api.get("/audit")
def audit_logs(limit: int = 200, db: Session = Depends(get_db), user=Depends(require("write"))):
    # admin/operator (write covers operator+; viewers blocked)
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


app.include_router(api)
