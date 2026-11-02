// Job: GODMODE Frontend. Purpose: Reports list page for GET /reports.
"use client";
import Link from "next/link";
import { Badge, fmt } from "@/components/State";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Page, Row, StaggerBody } from "@/components/Motion";

export default function Reports() {
  const r = useApi(() => data.reports());
  return (
    <Page>
      <div className="head"><h1>Reports</h1>{r.data && <span className="sub">{r.data.length}</span>}</div>
      <div className="panel">
        <Resource r={r} empty="No reports yet. Reports publish after the before_publish gate.">
          {(rows) => (
            <table><thead><tr><th>Title</th><th>Task</th><th>Status</th><th>Created</th></tr></thead>
              <StaggerBody>{rows.map((x) => (
                <Row key={x.id}><td>{x.title || `Report ${x.id}`}</td><td>{x.task_id != null ? <Link href={`/tasks/${x.task_id}`}>{x.task_id}</Link> : "-"}</td><td>{x.status && <Badge value={x.status} />}</td><td className="muted">{fmt(x.created_at)}</td></Row>
              ))}</StaggerBody></table>
          )}
        </Resource>
      </div>
    </Page>
  );
}
