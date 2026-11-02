// Job: GODMODE Frontend. Purpose: Workforce page for /agents list and mutations.
"use client";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge } from "@/components/State";

export default function Workforce() {
  const r = useApi(() => api.agents());
  return (
    <>
      <h1>Workforce</h1>
      <div className="card">
        <Resource r={r} empty="No agents registered.">
          {(rows) => (
            <table><thead><tr><th>Name</th><th>Role</th><th>Description</th><th>Status</th></tr></thead>
              <tbody>{rows.map((a) => <tr key={a.id}><td>{a.name}</td><td>{a.role}</td><td className="muted">{a.description}</td><td><Badge value={a.status} /></td></tr>)}</tbody></table>
          )}
        </Resource>
      </div>
    </>
  );
}
