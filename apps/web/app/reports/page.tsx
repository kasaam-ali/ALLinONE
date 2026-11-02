// Job: GODMODE Frontend. Purpose: Reports list page backed by GET /api/v1/reports.
"use client";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Report } from "@/lib/types";

export default function Reports() {
  const { data, error, loading } = useApi<Report[]>(() => api.reports(), []);
  return (
    <>
      <h1>Reports</h1>
      {error && <p className="err">{error}</p>}
      {loading && <p className="muted">Loading...</p>}
      {data?.map((r) => (
        <div className="card" key={r.id}>
          <h2>{r.task_id != null ? <Link href={`/tasks/${r.task_id}`}>{r.title || `Report ${r.id}`}</Link> : (r.title || `Report ${r.id}`)}</h2>
          <p className="muted">status: {r.status || "-"}</p>
          <pre>{(r as Report & { body?: string; body_md?: string }).body_md || (r as Report & { body?: string }).body || ""}</pre>
        </div>
      ))}
      {data?.length === 0 && <p className="muted">No reports yet.</p>}
    </>
  );
}
