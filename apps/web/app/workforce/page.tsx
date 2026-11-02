// Job: GODMODE Frontend. Purpose: Workforce list backed by GET/POST/PATCH /api/v1/agents.
"use client";
import { useState } from "react";
import { api, request, paths } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Agent } from "@/lib/types";

export default function Workforce() {
  const { data, reload, error, loading } = useApi<Agent[]>(() => api.agents(), []);
  const [f, setF] = useState({ name: "", role: "research", description: "" });
  const [err, setErr] = useState("");
  const run = (p: Promise<unknown>) => p.then(() => reload()).catch((e: Error) => setErr(e.message));
  return (
    <>
      <h1>Workforce</h1>
      {error && <p className="err">{error}</p>}
      {loading && <p className="muted">Loading agents...</p>}
      <div className="card"><h2>Add agent</h2>
        <div className="row">
          <input placeholder="Name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
          <select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>
            {["planner", "research", "execute", "verify", "report"].map((r) => <option key={r}>{r}</option>)}
          </select>
          <input placeholder="Description" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} />
          <button disabled={!f.name} onClick={() => run(request(paths.agents, { method: "POST", body: JSON.stringify({ ...f, tools: ["mock"] }) })).then(() => setF({ ...f, name: "", description: "" }))}>Add</button>
        </div>
        {err && <p className="err">{err}</p>}
      </div>
      <div className="card">
        <table><thead><tr><th>Name</th><th>Role</th><th>Description</th><th>Status</th><th></th></tr></thead>
          <tbody>{data?.map((a) => (
            <tr key={a.id}><td>{a.name}</td><td>{a.role}</td><td className="muted">{a.description}</td><td><span className={`badge ${a.status}`}>{a.status}</span></td>
              <td className="row">
                <button className="ghost" onClick={() => run(request(`${paths.agents}/${a.id}`, { method: "PATCH", body: JSON.stringify({ status: a.status === "active" ? "disabled" : "active" }) }))}>{a.status === "active" ? "Disable" : "Activate"}</button>
                <button className="bad" onClick={() => run(request(`${paths.agents}/${a.id}/disable`, { method: "POST", body: "{}" }))}>Disable endpoint</button>
              </td></tr>
          ))}</tbody></table>
        {data?.length === 0 && <p className="muted">No agents. API empty or unreachable.</p>}
      </div>
    </>
  );
}
