// Job: GODMODE Frontend. Purpose: Tasks list for GET /tasks with staggered rows.
"use client";
import Link from "next/link";
import { Badge, fmt } from "@/components/State";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Page, Row, StaggerBody } from "@/components/Motion";

export default function Tasks() {
  const r = useApi(() => data.tasks());
  return (
    <Page>
      <div className="head"><h1>Tasks</h1>{r.data && <span className="sub">{r.data.length}</span>}</div>
      <div className="panel">
        <Resource r={r} empty="No tasks yet. Tasks appear after POST /tasks.">
          {(rows) => (
            <table><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Created</th></tr></thead>
              <StaggerBody>{rows.map((x) => (
                <Row key={x.id}><td className="id">{x.id}</td><td><Link href={`/tasks/${x.id}`}>{x.title || x.prompt || "Untitled"}</Link></td><td><Badge value={x.status} /></td><td className="muted">{fmt(x.created_at)}</td></Row>
              ))}</StaggerBody></table>
          )}
        </Resource>
      </div>
    </Page>
  );
}
