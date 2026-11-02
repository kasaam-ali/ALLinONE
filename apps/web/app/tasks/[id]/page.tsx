// Job: GODMODE Frontend. Purpose: Task detail with Start run, StageEvent timeline, Artifacts, and animated approval gate decisions.
"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, ErrorBox, fmt } from "@/components/State";
import { Page } from "@/components/Motion";
import type { Approval, ApprovalDecision } from "@/lib/types";

function RunPanel({ runId }: { runId: string | number }) {
  const run = useApi(() => data.run(runId), [runId]);
  const events = useApi(() => data.runEvents(runId), [runId]);
  const artifacts = useApi(() => data.runArtifacts(runId), [runId]);
  return (
    <div className="split">
      <div className="panel"><h2>Run <Resource r={run}>{(r) => {
        const stage = r.current_stage || r.stage;
        return <><span className="mono">#{r.id}</span> <Badge value={r.status} /> {stage && <span className="muted">stage {stage}</span>}</>;
      }}</Resource></h2>
        <Resource r={events} empty="Run started. Stage events appear as plan, research, execute, verify, and report complete.">
          {(rows) => <ul className="timeline">{rows.map((e) => <li key={e.id}><span className="muted">{fmt(e.created_at)}</span><span className="mono">{e.stage}</span><span>{e.message}</span>{e.status && <Badge value={e.status} />}</li>)}</ul>}
        </Resource>
      </div>
      <div className="panel"><h2>Artifacts</h2>
        <Resource r={artifacts} empty="No artifacts yet. Plan and report files land here after stages finish.">
          {(rows) => <ul className="timeline">{rows.map((a) => <li key={a.id} style={{ gridTemplateColumns: "1fr auto" }}><span className="mono">{a.name || a.kind || `artifact ${a.id}`}</span><span className="muted">{fmt(a.created_at)}</span></li>)}</ul>}
        </Resource>
      </div>
    </div>
  );
}

function Gate({ a, onDecide }: { a: Approval; onDecide: (id: Approval["id"], d: ApprovalDecision) => Promise<void> }) {
  const [busy, setBusy] = useState<ApprovalDecision | null>(null);
  const reduce = useReducedMotion();
  const pending = a.status === "pending";
  return (
    <motion.div className="gate" layout={!reduce}
      animate={reduce ? undefined : a.status === "approved" ? { backgroundColor: ["rgba(63,185,80,0.12)", "rgba(63,185,80,0)"] } : a.status === "rejected" ? { backgroundColor: ["rgba(242,85,90,0.12)", "rgba(242,85,90,0)"], x: [0, -3, 3, 0] } : undefined}
      transition={{ duration: 0.6 }}>
      <span className="name">{a.gate}</span>
      <AnimatePresence mode="wait"><motion.span key={a.status} initial={reduce ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}><Badge value={a.status} /></motion.span></AnimatePresence>
      <span className="muted">{fmt(a.created_at)}</span>
      {pending && <div className="actions">
        <motion.button whileTap={reduce ? undefined : { scale: 0.96 }} disabled={!!busy} onClick={async () => { setBusy("approve"); await onDecide(a.id, "approve"); setBusy(null); }}>{busy === "approve" ? "Approving..." : "Approve"}</motion.button>
        <motion.button whileTap={reduce ? undefined : { scale: 0.96 }} className="bad" disabled={!!busy} onClick={async () => { setBusy("reject"); await onDecide(a.id, "reject"); setBusy(null); }}>{busy === "reject" ? "Rejecting..." : "Reject"}</motion.button>
      </div>}
    </motion.div>
  );
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const task = useApi(() => data.task(id), [id]);
  const approvals = useApi(() => data.approvals(), []);
  const [err, setErr] = useState("");
  const [starting, setStarting] = useState(false);
  async function decide(aid: string | number, d: ApprovalDecision) {
    setErr("");
    try { await data.decide(aid, d); approvals.reload(); task.reload(); }
    catch (e) { setErr((e as Error).message); }
  }
  async function start() {
    setErr(""); setStarting(true);
    try { await data.startTask(id); task.reload(); approvals.reload(); }
    catch (e) { setErr((e as Error).message); }
    finally { setStarting(false); }
  }
  return (
    <Page>
      <Resource r={task} empty="Task not found.">
        {(t) => {
          const mine = (approvals.data || []).filter((a) => String(a.task_id) === String(t.id));
          const pending = mine.filter((a) => a.status === "pending");
          const active = ["queued", "running", "awaiting_approval"].includes(String(t.status));
          const canStart = !active && (t.latest_run_id == null || ["draft", "failed", "rejected", "succeeded", "completed", "cancelled"].includes(String(t.status)));
          const gateEmpty = mine.length === 0
            ? (t.latest_run_id == null
              ? "No gates yet. Start a run to open after_plan, then before_publish before the report ships."
              : "Run is active. Waiting for after_plan or before_publish to open.")
            : null;
          return (
            <>
              <div className="head"><span className="mono">#{t.id}</span><h1>{t.title || `Task ${t.id}`}</h1><Badge value={t.status} />
                {canStart && <button className="sm" disabled={starting} onClick={start}>{starting ? "Starting..." : "Start run"}</button>}
              </div>
              {(t.description || t.prompt) && <div className="panel pad"><h2>Objective</h2><div>{t.description || t.prompt}</div></div>}
              <div className="panel"><h2>Approval gates (after_plan → before_publish)</h2>
                {err && <ErrorBox message={err} />}
                {approvals.error ? <ErrorBox message={approvals.error} onRetry={approvals.reload} />
                  : gateEmpty ? <p className="muted" style={{ padding: "0 14px 12px" }}>{gateEmpty}</p>
                  : <>
                      {pending.length > 0 && <p className="muted" style={{ padding: "0 14px 8px" }}>{pending.length} gate{pending.length > 1 ? "s" : ""} waiting on a decision.</p>}
                      {mine.map((a) => <Gate key={a.id} a={a} onDecide={decide} />)}
                    </>}
              </div>
              {t.latest_run_id != null ? <RunPanel runId={t.latest_run_id} /> : <div className="panel pad muted">Draft task. Start run to create a Run, open after_plan, then before_publish.</div>}
            </>
          );
        }}
      </Resource>
    </Page>
  );
}
