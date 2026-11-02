// Job: GODMODE Frontend. Purpose: Tasks list page backed by GET /api/v1/tasks.
"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Task } from "@/lib/types";

export default function TasksPage() {
  const { data, error, loading } = useApi<Task[]>(() => api.tasks(), []);
  return (
    <>
      <h1>Tasks</h1>
      {error && <p className="err">{error}</p>}
      {loading && <p className="muted">Loading...</p>}
      <div className="card">
        <table><thead><tr><th>#</th><th>Title</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>{data?.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td><Link href={`/tasks/${t.id}`}>{t.title || t.prompt || `Task ${t.id}`}</Link></td>
              <td><span className={`badge ${t.status}`}>{t.status}</span></td>
              <td className="muted">{t.created_at ? new Date(t.created_at).toLocaleString() : "-"}</td>
            </tr>
          ))}</tbody></table>
        {data?.length === 0 && <p className="muted">No tasks.</p>}
      </div>
    </>
  );
}
