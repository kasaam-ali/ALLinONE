// Job: GODMODE Frontend. Purpose: Tasks list page for GET /tasks.
"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, fmt } from "@/components/State";

export default function Tasks() {
  const r = useApi(() => api.tasks());
  return (
    <>
      <h1>Tasks</h1>
      <div className="card">
        <Resource r={r} empty="No tasks yet.">
          {(rows) => (
            <table><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>{rows.map((t) => (
                <tr key={t.id}><td>{t.id}</td><td><Link href={`/tasks/${t.id}`}>{t.title || t.prompt || "Untitled"}</Link></td><td><Badge value={t.status} /></td><td className="muted">{fmt(t.created_at)}</td></tr>
              ))}</tbody></table>
          )}
        </Resource>
      </div>
    </>
  );
}
