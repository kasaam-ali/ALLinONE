# FastAPI entrypoint: HTTP routes for health, auth, workforce, tasks, approvals, audit, reports, memories.
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import os
from .db import Base, engine, get_db, SessionLocal
from .models import User, Agent, Task, Plan, Step, Approval, AuditLog, Memory, Report, Run, StageEvent
from .security import hash_pw, check_pw, make_token, current_user, require
from .seed import seed
from . import orchestrator, queue
from .tools import validate_allowlist
from .tools.webhook_inbound import router as integrations_router

app = FastAPI(title="GODMODE API", version="0.1.0")
app.include_router(integrations_router)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip() and o.strip() != "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)  # idempotent; infra/migrations/001_init.sql is canonical for Postgres
    with SessionLocal() as db:
        seed(db)

def audit(db, actor, action, entity="", entity_id=None, **detail):
    db.add(AuditLog(actor=actor, action=action, entity=entity, entity_id=entity_id, detail=detail))

# ---------- schemas ----------
class RegisterIn(BaseModel):
    email: str; password: str; name: str = ""
class LoginIn(BaseModel):
    email: str; password: str
class AgentIn(BaseModel):
    name: str; role: str; description: str = ""; tools_allowlist: list[str] = []; status: str = "active"
    @field_validator("tools_allowlist")
    @classmethod
    def _v(cls, v): return validate_allowlist(v)
class TaskIn(BaseModel):
    prompt: str; title: str | None = None; requires_approval: bool = True
class DecisionIn(BaseModel):
    reason: str = ""

def user_out(u): return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}
def agent_out(a): return {"id": a.id, "name": a.name, "role": a.role, "description": a.description, "tools_allowlist": a.tools_allowlist, "status": a.status}
def task_out(t, full=False):
    d = {"id": t.id, "title": t.title, "prompt": t.prompt, "status": t.status, "requires_approval": bool(t.requires_approval),
         "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat() if t.updated_at else None}
    if full:
        d["plans"] = [{"id": p.id, "summary": p.summary, "steps": [{"id": s.id, "position": s.position, "phase": s.phase, "agent_name": s.agent_name,
                       "description": s.description, "status": s.status, "output": s.output} for s in p.steps]} for p in t.plans]
        d["approvals"] = [{"id": a.id, "gate": a.gate, "status": a.status, "reason": a.reason, "decided_at": a.decided_at.isoformat() if a.decided_at else None} for a in t.approvals]
    return d

# ---------- health ----------
@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "mock_llm": orchestrator.MOCK}

# ---------- auth ----------
@app.post("/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    u = User(email=body.email.lower(), name=body.name, password_hash=hash_pw(body.password), role="operator")
    db.add(u); db.flush(); audit(db, u.email, "user.register", "user", u.id); db.commit()
    return {"access_token": make_token(u), "token_type": "bearer", "user": user_out(u)}

@app.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=body.email.lower()).first()
    if not u or not check_pw(body.password, u.password_hash):
        raise HTTPException(401, "Invalid credentials")
    audit(db, u.email, "user.login", "user", u.id); db.commit()
    return {"access_token": make_token(u), "token_type": "bearer", "user": user_out(u)}

@app.get("/auth/me")
def me(u: User = Depends(current_user)): return user_out(u)

# ---------- workforce ----------
@app.get("/workforce")
def list_agents(db: Session = Depends(get_db), u=Depends(require("read"))):
    return [agent_out(a) for a in db.query(Agent).order_by(Agent.id)]

@app.post("/workforce", status_code=201)
def create_agent(body: AgentIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    a = Agent(**body.model_dump()); db.add(a); db.flush(); audit(db, u.email, "agent.create", "agent", a.id, name=a.name); db.commit()
    return agent_out(a)

@app.put("/workforce/{aid}")
def update_agent(aid: int, body: AgentIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    a = db.get(Agent, aid)
    if not a: raise HTTPException(404, "Agent not found")
    for k, v in body.model_dump().items(): setattr(a, k, v)
    audit(db, u.email, "agent.update", "agent", a.id); db.commit(); return agent_out(a)

@app.delete("/workforce/{aid}", status_code=204)
def delete_agent(aid: int, db: Session = Depends(get_db), u=Depends(require("write"))):
    a = db.get(Agent, aid)
    if not a: raise HTTPException(404, "Agent not found")
    db.delete(a); audit(db, u.email, "agent.delete", "agent", aid); db.commit()

# ---------- tasks ----------
def _agents(db): return [agent_out(a) for a in db.query(Agent).filter_by(status="active")]

def _stage(db, run, stage, status, **detail):
    if run is None:
        return
    db.add(StageEvent(run_id=run.id, stage=stage, status=status, detail=detail or {}))
    run.current_stage = stage

def _latest_run(db, task_id):
    return db.query(Run).filter_by(task_id=task_id).order_by(Run.id.desc()).first()



def _finish(db, t, plan, state, run=None):
    outs = state.get("outputs", {})
    for s in plan.steps:
        s.status = "done"; s.output = outs.get(s.phase, s.output)
    db.add(Report(task_id=t.id, title=f"Report: {t.title}", body=state.get("report", "")))
    db.add(Memory(scope="task", key=f"task:{t.id}:summary", content=state.get("report", "")[:2000], task_id=t.id))
    t.status = "completed"
    if run is not None:
        _stage(db, run, "report", "succeeded", headline=(state.get("report") or "")[:120])
        run.status = "succeeded"
        run.finished_at = datetime.now(timezone.utc)
        queue.release_run_lock(run.id)

def _apply_outputs(plan, state, upto_phases=None):
    outs = state.get("outputs", {})
    for s in plan.steps:
        if upto_phases is not None and s.phase not in upto_phases:
            continue
        if s.phase in outs:
            s.status = "done"; s.output = outs[s.phase]

@app.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db), u=Depends(require("write"))):
    if not body.prompt.strip(): raise HTTPException(422, "Prompt required")
    t = Task(title=body.title or body.prompt.strip()[:80], prompt=body.prompt, requires_approval=int(body.requires_approval), created_by=u.id, status="running")
    db.add(t); db.flush(); audit(db, u.email, "task.create", "task", t.id, prompt=body.prompt[:200])
    run = Run(task_id=t.id, status="running", current_stage="plan", mock_llm=int(orchestrator.MOCK), started_at=datetime.now(timezone.utc))
    db.add(run); db.flush()
    queue.try_run_lock(run.id)
    agents = _agents(db)
    _stage(db, run, "plan", "started")
    state = orchestrator.run_planning(body.prompt, agents, body.requires_approval)
    _stage(db, run, "plan", "succeeded", summary=(state.get("outputs") or {}).get("plan", "")[:200])
    plan = Plan(task_id=t.id, summary=state["outputs"].get("plan", "")); db.add(plan); db.flush()
    for i, s in enumerate(state["plan"]):
        db.add(Step(plan_id=plan.id, position=i, phase=s["phase"], agent_name=s["agent"], description=s["description"],
                    status="done" if s["phase"] == "plan" else "pending", output=state["outputs"].get("plan", "") if s["phase"] == "plan" else ""))
    db.flush(); db.refresh(plan)
    if state.get("paused"):
        gate = state.get("pause_gate") or "after_plan"
        t.status = "awaiting_approval"; run.status = "awaiting_approval"
        db.add(Approval(task_id=t.id, run_id=run.id, gate=gate, status="pending"))
        audit(db, "orchestrator", "task.paused_for_approval", "task", t.id, gate=gate, run_id=run.id)
    else:
        for ph in ("research", "execute", "verify"):
            if ph in (state.get("outputs") or {}):
                _stage(db, run, ph, "succeeded")
        _finish(db, t, plan, state if not body.requires_approval else orchestrator.run_full(body.prompt, agents), run=run)
        audit(db, "orchestrator", "task.completed", "task", t.id, run_id=run.id)
    queue.enqueue("task.created", {"task_id": t.id, "run_id": run.id})
    db.commit(); db.refresh(t)
    return task_out(t, full=True)

@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db), u=Depends(require("read"))):
    return [task_out(t) for t in db.query(Task).order_by(Task.id.desc())]

@app.get("/tasks/{tid}")
def get_task(tid: int, db: Session = Depends(get_db), u=Depends(require("read"))):
    t = db.get(Task, tid)
    if not t: raise HTTPException(404, "Task not found")
    return task_out(t, full=True)

@app.get("/approvals")
def list_approvals(status: str = "pending", db: Session = Depends(get_db), u=Depends(require("read"))):
    q = db.query(Approval)
    if status != "all": q = q.filter_by(status=status)
    return [{"id": a.id, "task_id": a.task_id, "task_title": a.task.title, "gate": a.gate, "status": a.status, "created_at": a.created_at.isoformat()} for a in q.order_by(Approval.id.desc())]

def _decide(aid, approve, body, db, u):
    a = db.get(Approval, aid)
    if not a: raise HTTPException(404, "Approval not found")
    if a.status != "pending": raise HTTPException(409, f"Already {a.status}")
    a.status = "approved" if approve else "rejected"; a.reason = body.reason; a.decided_by = u.id; a.decided_at = datetime.now(timezone.utc)
    t = a.task
    audit(db, u.email, f"approval.{a.status}", "task", t.id, reason=body.reason, gate=a.gate)
    run = db.get(Run, a.run_id) if a.run_id else _latest_run(db, t.id)
    if not approve:
        t.status = "rejected"
        for s in t.plans[-1].steps:
            if s.status == "pending": s.status = "skipped"
        if run is not None:
            run.status = "failed"; run.error_summary = body.reason or "rejected"; run.finished_at = datetime.now(timezone.utc)
            queue.release_run_lock(run.id)
        db.commit(); db.refresh(t)
        return task_out(t, full=True)

    agents = _agents(db)
    plan = t.plans[-1]
    if a.gate == "after_plan":
        if run is not None:
            run.status = "running"
        state = orchestrator.continue_after_plan(t.prompt, agents)
        _apply_outputs(plan, state, upto_phases={"plan", "research", "execute", "verify"})
        for ph in ("research", "execute", "verify"):
            if ph in (state.get("outputs") or {}):
                _stage(db, run, ph, "succeeded")
        if state.get("paused"):
            gate = state.get("pause_gate") or "before_publish"
            t.status = "awaiting_approval"
            if run is not None:
                run.status = "awaiting_approval"
            db.add(Approval(task_id=t.id, run_id=(run.id if run else None), gate=gate, status="pending"))
            audit(db, "orchestrator", "task.paused_for_approval", "task", t.id, gate=gate)
        else:
            _finish(db, t, plan, state, run=run); audit(db, "orchestrator", "task.completed", "task", t.id)
    elif a.gate == "before_publish":
        prior_outputs = {s.phase: s.output for s in plan.steps if s.output}
        state = orchestrator.continue_after_publish(t.prompt, agents, {"outputs": prior_outputs, "plan": [
            {"phase": s.phase, "description": s.description, "agent": s.agent_name} for s in plan.steps
        ]})
        _finish(db, t, plan, state, run=run); audit(db, "orchestrator", "task.completed", "task", t.id)
    else:
        state = orchestrator.run_full(t.prompt, agents)
        _finish(db, t, plan, state, run=run); audit(db, "orchestrator", "task.completed", "task", t.id)
    db.commit(); db.refresh(t)
    return task_out(t, full=True)

@app.post("/approvals/{aid}/approve")
def approve(aid: int, body: DecisionIn = DecisionIn(), db: Session = Depends(get_db), u=Depends(require("approve"))):
    return _decide(aid, True, body, db, u)

@app.post("/approvals/{aid}/reject")
def reject(aid: int, body: DecisionIn = DecisionIn(), db: Session = Depends(get_db), u=Depends(require("approve"))):
    return _decide(aid, False, body, db, u)

# ---------- audit / reports / memory ----------
@app.get("/audit")
def audit_logs(limit: int = 200, db: Session = Depends(get_db), u=Depends(require("read"))):
    return [{"id": l.id, "actor": l.actor, "action": l.action, "entity": l.entity, "entity_id": l.entity_id, "detail": l.detail, "created_at": l.created_at.isoformat()}
            for l in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit)]

@app.get("/reports")
def reports(db: Session = Depends(get_db), u=Depends(require("read"))):
    return [{"id": r.id, "task_id": r.task_id, "title": r.title, "body": r.body, "created_at": r.created_at.isoformat()} for r in db.query(Report).order_by(Report.id.desc())]

@app.get("/reports/summary")
def summary(db: Session = Depends(get_db), u=Depends(require("read"))):
    by = dict(db.query(Task.status, func.count()).group_by(Task.status).all())
    return {"tasks_total": sum(by.values()), "tasks_by_status": by, "agents": db.query(Agent).count(),
            "pending_approvals": db.query(Approval).filter_by(status="pending").count(), "reports": db.query(Report).count()}

@app.get("/memories")
def memories(db: Session = Depends(get_db), u=Depends(require("read"))):
    return [{"id": m.id, "scope": m.scope, "key": m.key, "content": m.content, "task_id": m.task_id} for m in db.query(Memory).order_by(Memory.id.desc()).limit(100)]
