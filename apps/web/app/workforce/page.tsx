// Job: GODMODE Frontend. Purpose: Workforce page for GET /agents.
"use client";
import { Badge } from "@/components/State";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Page, Row, StaggerBody } from "@/components/Motion";

export default function Workforce() {
  const r = useApi(() => data.agents());
  return (
    <Page>
      <div className="head"><h1>Workforce</h1>{r.data && <span className="sub">{r.data.length}</span>}</div>
      <div className="panel">
        <Resource r={r} empty="No agents registered.">
          {(rows) => (
            <table><thead><tr><th>Name</th><th>Role</th><th>Description</th><th>Status</th></tr></thead>
              <StaggerBody>{rows.map((x) => (
                <Row key={x.id}><td>{x.name}</td><td className="mono">{x.role}</td><td className="muted">{x.description}</td><td><Badge value={x.status} /></td></Row>
              ))}</StaggerBody></table>
          )}
        </Resource>
      </div>
    </Page>
  );
}
