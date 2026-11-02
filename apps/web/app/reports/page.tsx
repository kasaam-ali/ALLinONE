// Job: GODMODE Frontend. Purpose: Reports list page for GET /reports.
"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, fmt } from "@/components/State";

export default function Reports() {
  const r = useApi(() => api.reports());
  return (
    <>
      <h1>Reports</h1>
      <div className="card">
        <Resource r={r} empty="No reports yet.">
          {(rows) => (
            <table><thead><tr><th>Title</th><th>Task</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>{rows.map((x) => (
                <tr key={x.id}><td>{x.title || `Report ${x.id}`}</td><td>{x.task_id != null ? <Link href={`/tasks/${x.task_id}`}>{x.task_id}</Link> : "-"}</td><td>{x.status && <Badge value={x.status} />}</td><td className="muted">{fmt(x.created_at)}</td></tr>
              ))}</tbody></table>
          )}
        </Resource>
      </div>
    </>
  );
}
