// Job: ALLinONE Frontend. Purpose: Tasks list for GET /tasks plus create form for POST /tasks.
"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, ErrorBox, fmt } from "@/components/State";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Page, Row, StaggerBody } from "@/components/Motion";

export default function Tasks() {
  const r = useApi(() => data.tasks());
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [createdId, setCreatedId] = useState<string | number | null>(null);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setErr(""); setCreatedId(null); setBusy(true);
    try {
      const t = await data.createTask({ title: title.trim(), description: description.trim() });
      setTitle(""); setDescription("");
      setCreatedId(t.id);
      r.reload();
    } catch (x) {
      setErr((x as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page>
      <div className="head"><h1>Tasks</h1>{r.data && <span className="sub">{r.data.length}</span>}</div>
      <div className="panel pad">
        <h2>New task</h2>
        <form className="stack" onSubmit={onCreate}>
          <label className="field"><span>Title</span>
            <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="What should the workforce do?" maxLength={255} />
          </label>
          <label className="field"><span>Description</span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional context for plan and research stages" rows={3} />
          </label>
          {err && <ErrorBox message={err} />}
          {createdId != null && (
            <p className="muted">Created task #{createdId}. <button type="button" className="ghost sm" onClick={() => router.push(`/tasks/${createdId}`)}>Open and start run</button></p>
          )}
          <div className="row"><button type="submit" disabled={busy || !title.trim()}>{busy ? "Creating..." : "Create task"}</button></div>
        </form>
      </div>
      <div className="panel">
        <Resource r={r} empty="No tasks yet. Create one above, then open it and Start run to hit after_plan and before_publish gates.">
          {(rows) => (
            <table><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Created</th></tr></thead>
              <StaggerBody>{rows.map((x) => (
                <Row key={x.id}><td className="id">{x.id}</td><td><Link href={`/tasks/${x.id}`}>{x.title || "Untitled"}</Link></td><td><Badge value={x.status} /></td><td className="muted">{fmt(x.created_at)}</td></Row>
              ))}</StaggerBody></table>
          )}
        </Resource>
      </div>
    </Page>
  );
}
