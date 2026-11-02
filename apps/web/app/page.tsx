// Job: GODMODE Frontend. Purpose: Command Center dashboard using GET /dashboard/summary plus tasks and pending approvals.
"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Approval, DashboardSummary, Task } from "@/lib/types";

export default function Dashboard() {
  const sum = useApi<DashboardSummary>(() => api.dashboard(), []);
  const tasks = useApi<Task[]>(() => api.tasks(), []);
  const approvals = useApi<Approval[]>(() => api.approvals("pending"), []);
  const s = sum.data;
  return (
    <>
      <h1>Command Center</h1>
      {sum.error && <p className="err">{sum.error}</p>}
      <div className="grid">
        <div className="card stat"><b>{s?.running ?? "-"}</b><span>Running</span></div>
        <div className="card stat"><b>{s?.awaiting_approval ?? "-"}</b><span>Awaiting approval</span></div>
        <div className="card stat"><b>{s?.failed_24h ?? "-"}</b><span>Failed (24h)</span></div>
        <div className="card stat"><b>{s ? Object.values(s.agents_by_status || {}).reduce((a, b) => a + b, 0) : "-"}</b><span>Agents</span></div>
      </div>
      {s?.agents_by_status && (
        <div className="card"><h2>Agents by status</h2>
          <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
            {Object.entries(s.agents_by_status).map(([k, v]) => (
              <span key={k} className={`badge ${k}`}>{k}: {v}</span>
            ))}
          </div>
        </div>
      )}
      {!!approvals.data?.length && (
        <div className="card"><h2>Awaiting approval</h2>
          {approvals.data.map((a) => (
            <p key={a.id}>
              <Link href={a.task_id != null ? `/tasks/${a.task_id}` : "/tasks"}>Approval #{a.id}</Link>{" "}
              <span className="badge pending">{a.gate}</span>
            </p>
          ))}
        </div>
      )}
      <div className="card"><h2>Recent tasks</h2>
        {tasks.error && <p className="err">{tasks.error}</p>}
        <table><thead><tr><th>#</th><th>Title</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>{tasks.data?.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td><Link href={`/tasks/${t.id}`}>{t.title || t.prompt || `Task ${t.id}`}</Link></td>
              <td><span className={`badge ${t.status}`}>{t.status}</span></td>
              <td className="muted">{t.created_at ? new Date(t.created_at).toLocaleString() : "-"}</td>
            </tr>
          ))}</tbody></table>
        {tasks.data?.length === 0 && <p className="muted">No tasks yet. API empty or unreachable.</p>}
        {tasks.loading && <p className="muted">Loading tasks...</p>}
      </div>
    </>
  );
}
