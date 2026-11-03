// Job: ALLinONE Frontend. Purpose: Command Center dashboard with animated KPI strip from GET /dashboard/summary, agents, and pending gates.
"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, fmt } from "@/components/State";
import { Page, Row, StaggerBody, Ticker } from "@/components/Motion";

function count(map: Record<string, number> | undefined, keys: string[]) {
  if (!map) return 0;
  return keys.reduce((n, k) => n + (map[k] ?? 0), 0);
}

export default function Dashboard() {
  const r = useApi(() => data.dashboard());
  const approvals = useApi(() => data.approvals());
  const reduce = useReducedMotion();
  return (
    <Page>
      <div className="head"><h1>Dashboard</h1><span className="sub">Live workforce state</span></div>
      <Resource r={r} empty="Dashboard summary returned no data.">
        {(s) => {
          const running = count(s.runs_by_status, ["running"]) || count(s.tasks_by_status, ["running"]);
          const awaiting = s.pending_approvals ?? count(s.tasks_by_status, ["awaiting_approval"]);
          const failed = count(s.runs_by_status, ["failed"]) || count(s.tasks_by_status, ["failed"]);
          const agents = s.agents_active ?? 0;
          const statusMap = Object.keys(s.runs_by_status || {}).length ? s.runs_by_status : s.tasks_by_status;
          const max = Math.max(1, running, awaiting, failed, agents);
          const kpis = [["Running", running, "ok"], ["Awaiting approval", awaiting, "warn"], ["Failed", failed, "bad"], ["Agents active", agents, ""]] as const;
          return (
            <>
              <div className="kpis">
                {kpis.map(([l, v, tone], i) => (
                  <motion.div key={l} className={`kpi ${tone}`}
                    initial={reduce ? false : { opacity: 0, rotateX: -12, y: 6 }} animate={{ opacity: 1, rotateX: 0, y: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                    whileHover={reduce ? undefined : { rotateX: 3, rotateY: -3 }}>
                    <span className="label">{l}</span>
                    <span className="value"><Ticker value={v ?? 0} /></span>
                    <div className="bar"><motion.span initial={reduce ? false : { scaleX: 0 }} animate={{ scaleX: (v ?? 0) / max }} transition={{ duration: 0.8, delay: 0.1 + i * 0.05 }} /></div>
                  </motion.div>
                ))}
              </div>
              <div className="split">
                <div className="panel"><h2>Pending approval gates</h2>
                  {(approvals.data || []).filter((a) => a.status === "pending").length === 0 ? <p className="muted" style={{ padding: "0 14px 12px" }}>No gates waiting on a decision.</p> : (
                    <table><thead><tr><th>Gate</th><th>Task</th><th>Opened</th></tr></thead>
                      <StaggerBody>{(approvals.data || []).filter((a) => a.status === "pending").map((a) => (
                        <Row key={a.id}><td className="mono">{a.gate}</td><td>{a.task_id != null ? <Link href={`/tasks/${a.task_id}`}>Decide on task {a.task_id}</Link> : "-"}</td><td className="muted">{fmt(a.created_at)}</td></Row>
                      ))}</StaggerBody></table>
                  )}
                </div>
                <div className="panel"><h2>Runs by status</h2>
                  {Object.keys(statusMap || {}).length === 0 && !agents ? <p className="muted" style={{ padding: "0 14px 12px" }}>No run status yet. {agents ? `${agents} agents active.` : ""}</p> : (
                    <table><thead><tr><th>Status</th><th style={{ textAlign: "right" }}>Count</th></tr></thead>
                      <StaggerBody>
                        {Object.entries(statusMap || {}).map(([k, v]) => <Row key={k}><td><Badge value={k} /></td><td className="num" style={{ textAlign: "right" }}>{v}</td></Row>)}
                        {agents > 0 && !Object.keys(statusMap || {}).length ? <Row key="agents"><td><Badge value="active" /></td><td className="num" style={{ textAlign: "right" }}>{agents}</td></Row> : null}
                      </StaggerBody></table>
                  )}
                </div>
              </div>
            </>
          );
        }}
      </Resource>
    </Page>
  );
}
