// Job: GODMODE Frontend. Purpose: Command Center dashboard page calling GET /dashboard/summary.
"use client";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";

export default function Dashboard() {
  const r = useApi(() => api.dashboard());
  return (
    <>
      <h1>Dashboard</h1>
      <Resource r={r} empty="No summary returned by the API.">
        {(s) => (
          <>
            <div className="grid">
              {([["Running", s.running], ["Awaiting approval", s.awaiting_approval], ["Failed (24h)", s.failed_24h]] as const).map(([l, v]) => (
                <div className="card stat" key={l}><b>{v ?? "-"}</b><span>{l}</span></div>
              ))}
            </div>
            <div className="card"><h2>Agents by status</h2>
              {Object.keys(s.agents_by_status || {}).length === 0 ? <p className="muted">No agents reported.</p> : (
                <table><thead><tr><th>Status</th><th>Agents</th></tr></thead>
                  <tbody>{Object.entries(s.agents_by_status).map(([k, v]) => <tr key={k}><td><span className={`badge ${k}`}>{k}</span></td><td>{v}</td></tr>)}</tbody></table>
              )}
            </div>
          </>
        )}
      </Resource>
    </>
  );
}
