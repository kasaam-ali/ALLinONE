// Job: GODMODE Frontend. Purpose: Task detail with Run, StageEvent, Artifact, and Approval actions.
"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, ErrorBox, fmt } from "@/components/State";
import type { ApprovalDecision } from "@/lib/types";

function RunPanel({ runId }: { runId: string | number }) {
  const run = useApi(() => api.run(runId), [runId]);
  const events = useApi(() => api.runEvents(runId), [runId]);
  const artifacts = useApi(() => api.runArtifacts(runId), [runId]);
  return (
    <>
      <div className="card"><h2>Latest run</h2>
        <Resource r={run}>{(r) => <p>Run {r.id} <Badge value={r.status} /> {r.stage && <span className="muted">stage: {r.stage}</span>}</p>}</Resource>
      </div>
      <div className="card"><h2>Plan and stage events</h2>
        <Resource r={events} empty="No stage events yet.">
          {(rows) => (
            <table><thead><tr><th>Time</th><th>Stage</th><th>Status</th><th>Message</th></tr></thead>
              <tbody>{rows.map((e) => <tr key={e.id}><td className="muted">{fmt(e.created_at)}</td><td>{e.stage}</td><td>{e.status && <Badge value={e.status} />}</td><td>{e.message}</td></tr>)}</tbody></table>
          )}
        </Resource>
      </div>
      <div className="card"><h2>Artifacts</h2>
        <Resource r={artifacts} empty="No artifacts yet.">
          {(rows) => <ul>{rows.map((a) => <li key={a.id}>{a.name || a.kind || `Artifact ${a.id}`} <span className="muted">{fmt(a.created_at)}</span></li>)}</ul>}
        </Resource>
      </div>
    </>
  );
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const task = useApi(() => api.task(id), [id]);
  const approvals = useApi(() => api.approvals(), []);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  async function decide(aid: string | number, d: ApprovalDecision) {
    setBusy(true); setErr("");
    try { await api.decide(aid, d); approvals.reload(); task.reload(); }
    catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }
  return (
    <Resource r={task} empty="Task not found.">
      {(t) => {
        const mine = (approvals.data || []).filter((a) => String(a.task_id) === String(t.id));
        return (
          <>
            <h1>{t.title || `Task ${t.id}`} <Badge value={t.status} /></h1>
            {t.prompt && <div className="card"><h2>Objective</h2><p>{t.prompt}</p></div>}
            {t.latest_run_id != null
              ? <RunPanel runId={t.latest_run_id} />
              : <div className="card placeholder"><h2>Run</h2><p>No run started yet. Plan, stage events, and artifacts appear here once a run exists.</p></div>}
            <div className="card"><h2>Approvals (after_plan, before_publish)</h2>
              {err && <ErrorBox message={err} />}
              {approvals.error ? <ErrorBox message={approvals.error} onRetry={approvals.reload} /> : mine.length === 0 ? <p className="muted">No approvals for this task.</p> : (
                <table><thead><tr><th>Gate</th><th>Status</th><th>Created</th><th /></tr></thead>
                  <tbody>{mine.map((a) => (
                    <tr key={a.id}><td>{a.gate}</td><td><Badge value={a.status} /></td><td className="muted">{fmt(a.created_at)}</td>
                      <td>{a.status === "pending" && <div className="row">
                        <button disabled={busy} onClick={() => decide(a.id, "approve")}>Approve</button>
                        <button className="bad" disabled={busy} onClick={() => decide(a.id, "reject")}>Reject</button>
                      </div>}</td></tr>
                  ))}</tbody></table>
              )}
            </div>
          </>
        );
      }}
    </Resource>
  );
}
