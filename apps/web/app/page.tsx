// Job: GODMODE Frontend. Purpose: Command Center dashboard with animated KPI strip from GET /dashboard/summary, agents, and pending gates.
"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { data } from "@/lib/data";
import { useApi } from "@/lib/useApi";
import { Resource } from "@/components/Resource";
import { Badge, fmt } from "@/components/State";
import { Page, Row, StaggerBody, Ticker } from "@/components/Motion";

export default function Dashboard() {
  const r = useApi(() => data.dashboard());
  const approvals = useApi(() => data.approvals());
  const reduce = useReducedMotion();
  return (
    <Page>
      <div className="head"><h1>Dashboard</h1><span className="sub">Live workforce state</span></div>
      <Resource r={r} empty="Dashboard summary returned no data.">
        {(s) => {
          const agents = Object.values(s.agents_by_status || {}).reduce((a, b) => a + b, 0);
          const max = Math.max(1, s.running, s.awaiting_approval, s.failed_24h, agents);
          const kpis = [["Running", s.running, "ok"], ["Awaiting approval", s.awaiting_approval, "warn"], ["Failed (24h)", s.failed_24h, "bad"], ["Agents", agents, ""]] as const;
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
                        <Row key={a.id}><td className="mono">{a.gate}</td><td>{a.task_id != null ? <Link href={`/tasks/${a.task_id}`}>Task {a.task_id}</Link> : "-"}</td><td className="muted">{fmt(a.created_at)}</td></Row>
                      ))}</StaggerBody></table>
                  )}
                </div>
                <div className="panel"><h2>Agents by status</h2>
                  {Object.keys(s.agents_by_status || {}).length === 0 ? <p className="muted" style={{ padding: "0 14px 12px" }}>No agents reported.</p> : (
                    <table><thead><tr><th>Status</th><th style={{ textAlign: "right" }}>Agents</th></tr></thead>
                      <StaggerBody>{Object.entries(s.agents_by_status).map(([k, v]) => <Row key={k}><td><Badge value={k} /></td><td className="num" style={{ textAlign: "right" }}>{v}</td></Row>)}</StaggerBody></table>
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
