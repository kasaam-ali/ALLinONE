// Job: GODMODE Frontend. Purpose: Task detail with Run/StageEvent/Artifact/Approval placeholders via /api/v1.
"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Approval, Artifact, Report, Run, StageEvent, Task } from "@/lib/types";

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const task = useApi<Task>(() => api.task(id), [id]);
  const approvals = useApi<Approval[]>(() => api.approvals(), [id]);
  const reports = useApi<Report[]>(() => api.reports(), [id]);
  const runId = task.data?.latest_run_id;
  const run = useApi<Run | null>(() => (runId != null ? api.run(runId) : Promise.resolve(null)), [runId]);
  const events = useApi<StageEvent[]>(() => (runId != null ? api.runEvents(runId) : Promise.resolve([])), [runId]);
  const artifacts = useApi<Artifact[]>(() => (runId != null ? api.runArtifacts(runId) : Promise.resolve([])), [runId]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function decide(aid: string | number, decision: "approve" | "reject") {
    setBusy(true); setErr("");
    try {
      await api.decide(aid, decision);
      task.reload(); approvals.reload(); run.reload(); events.reload(); artifacts.reload(); reports.reload();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Decision failed");
    } finally { setBusy(false); }
  }

  if (task.error) return <p className="err">{task.error}</p>;
  if (!task.data) return <p className="muted">Loading task...</p>;
  const t = task.data;
  const relatedApprovals = (approvals.data || []).filter((a) => a.task_id == t.id || (runId != null && a.run_id == runId));
  const report = (reports.data || []).find((r) => r.task_id == t.id);

  return (
    <>
      <h1>#{t.id} {t.title || "Task"} <span className={`badge ${t.status}`}>{t.status}</span></h1>
      {err && <p className="err">{err}</p>}
      <div className="card"><h2>Objective</h2><p>{t.prompt || t.title || "No description."}</p></div>

      <div className="card"><h2>Run</h2>
        {run.error && <p className="err">{run.error}</p>}
        {!runId && <p className="muted">No Run linked yet (latest_run_id missing).</p>}
        {run.data && <p>Run #{run.data.id} <span className={`badge ${run.data.status}`}>{run.data.status}</span> stage: {run.data.stage || "-"}</p>}
      </div>

      <div className="card"><h2>Stage events</h2>
        {events.error && <p className="err">{events.error}</p>}
        <table><thead><tr><th>Stage</th><th>Status</th><th>Message</th><th>When</th></tr></thead>
          <tbody>{(events.data || []).map((e) => (
            <tr key={e.id}><td>{e.stage}</td><td><span className={`badge ${e.status || ""}`}>{e.status}</span></td><td className="muted">{e.message}</td><td className="muted">{e.created_at}</td></tr>
          ))}</tbody></table>
        {(events.data || []).length === 0 && <p className="muted">No StageEvent rows yet (plan/research/execute/verify/report placeholders).</p>}
      </div>

      <div className="card"><h2>Artifacts</h2>
        {(artifacts.data || []).length === 0 && <p className="muted">No Artifact rows yet.</p>}
        <ul>{(artifacts.data || []).map((a) => <li key={a.id}>{a.kind || "artifact"} {a.name || `#${a.id}`}</li>)}</ul>
      </div>

      <div className="card"><h2>Approvals</h2>
        {relatedApprovals.map((a) => (
          <div key={a.id} style={{ marginBottom: 12 }}>
            <p>#{a.id} gate <span className="badge pending">{a.gate}</span> <span className={`badge ${a.status}`}>{a.status}</span></p>
            {a.status === "pending" && (
              <div className="row">
                <button disabled={busy} onClick={() => decide(a.id, "approve")}>Approve</button>
                <button className="bad" disabled={busy} onClick={() => decide(a.id, "reject")}>Reject</button>
              </div>
            )}
          </div>
        ))}
        {relatedApprovals.length === 0 && <p className="muted">No Approval records for this task/run (gates: after_plan, before_publish).</p>}
      </div>

      {report && <div className="card"><h2>Report</h2><pre>{(report as Report & { body?: string }).body || report.title || JSON.stringify(report, null, 2)}</pre></div>}
    </>
  );
}
