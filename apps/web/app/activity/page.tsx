// Job: GODMODE Frontend. Purpose: Activity and audit feed for GET /audit.
"use client";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { fmt } from "@/components/State";

export default function Activity() {
  const r = useApi(() => api.audit({ limit: 200 }));
  return (
    <>
      <h1>Activity / Audit</h1>
      <div className="card">
        <Resource r={r} empty="No audit entries yet.">
          {(rows) => (
            <table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Detail</th></tr></thead>
              <tbody>{rows.map((l) => (
                <tr key={l.id}><td className="muted">{fmt(l.created_at)}</td><td>{l.actor ?? "-"}</td><td>{l.action}</td><td>{l.entity_type} {l.entity_id ?? ""}</td><td className="muted">{l.detail ? JSON.stringify(l.detail) : ""}</td></tr>
              ))}</tbody></table>
          )}
        </Resource>
      </div>
    </>
  );
}
