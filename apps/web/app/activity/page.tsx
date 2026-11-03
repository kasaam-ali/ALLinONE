// Job: ALLinONE Frontend. Purpose: Activity and audit feed for GET /audit.
"use client";
import { fmt } from "@/components/State";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Page, Row, StaggerBody } from "@/components/Motion";

export default function Activity() {
  const r = useApi(() => data.audit());
  return (
    <Page>
      <div className="head"><h1>Activity</h1>{r.data && <span className="sub">{r.data.length}</span>}</div>
      <div className="panel">
        <Resource r={r} empty="No audit entries yet.">
          {(rows) => (
            <table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Detail</th></tr></thead>
              <StaggerBody>{rows.map((x) => {
                const actor = x.actor ?? (x.actor_user_id != null ? `user ${x.actor_user_id}` : "-");
                const detail = x.after_json ?? x.detail;
                return (
                  <Row key={x.id}>
                    <td className="muted">{fmt(x.created_at)}</td>
                    <td>{actor}</td>
                    <td className="mono">{x.action}</td>
                    <td>{x.entity_type} {x.entity_id ?? ""}</td>
                    <td className="mono">{detail ? JSON.stringify(detail) : ""}</td>
                  </Row>
                );
              })}</StaggerBody></table>
          )}
        </Resource>
      </div>
    </Page>
  );
}
