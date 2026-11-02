// Job: GODMODE Frontend. Purpose: Fixture data in Architect DTO shapes, used only when /api/v1 is unreachable or fixtures are forced.
import type { Agent, Approval, Artifact, AuditEntry, DashboardSummary, Report, Run, StageEvent, Task } from "./types";

const ago = (m: number) => new Date(Date.now() - m * 60000).toISOString();

export const fx = {
  agents: [
    { id: 1, name: "Planner", role: "planner", description: "Breaks objectives into staged plans", status: "idle" },
    { id: 2, name: "Researcher", role: "researcher", description: "Gathers sources via browser and API tools", status: "running" },
    { id: 3, name: "Executor", role: "executor", description: "Performs tool calls against connected systems", status: "running" },
    { id: 4, name: "Verifier", role: "verifier", description: "Checks outputs against acceptance criteria", status: "idle" },
    { id: 5, name: "Reporter", role: "reporter", description: "Writes the final report and artifacts", status: "paused" },
  ] as Agent[],
  tasks: [
    { id: 101, title: "Competitor pricing scan, Q4", prompt: "Collect public pricing for 5 competitors and summarize deltas.", status: "awaiting_approval", created_at: ago(14), latest_run_id: 501 },
    { id: 102, title: "Draft vendor outreach list", prompt: "Find 20 logistics vendors in Karachi with contact pages.", status: "running", created_at: ago(42), latest_run_id: 502 },
    { id: 103, title: "Weekly ops report", prompt: "Summarize last week's completed runs.", status: "completed", created_at: ago(380), latest_run_id: 503 },
    { id: 104, title: "CRM duplicate cleanup", prompt: "Identify duplicate leads.", status: "failed", created_at: ago(900), latest_run_id: null },
  ] as Task[],
  run: (id: string | number): Run => ({ id, task_id: 101, status: "awaiting_approval", stage: "plan", started_at: ago(14) }),
  events: (id: string | number): StageEvent[] => [
    { id: 1, run_id: id, stage: "plan", status: "completed", message: "Plan drafted with 4 steps", created_at: ago(13) },
    { id: 2, run_id: id, stage: "plan", status: "awaiting_approval", message: "Gate after_plan opened", created_at: ago(12) },
  ],
  artifacts: (id: string | number): Artifact[] => [{ id: 1, run_id: id, kind: "plan", name: "plan.md", created_at: ago(12) }],
  approvals: [
    { id: 9001, run_id: 501, task_id: 101, gate: "after_plan", status: "pending", created_at: ago(12) },
    { id: 9002, run_id: 503, task_id: 103, gate: "before_publish", status: "approved", created_at: ago(300) },
  ] as Approval[],
  dashboard: { running: 2, awaiting_approval: 1, failed_24h: 1, agents_by_status: { running: 2, idle: 2, paused: 1 } } as DashboardSummary,
  audit: [
    { id: 1, actor: "planner", action: "run.stage", entity_type: "run", entity_id: 501, created_at: ago(13) },
    { id: 2, actor: "system", action: "approval.opened", entity_type: "approval", entity_id: 9001, created_at: ago(12) },
    { id: 3, actor: "admin@godmode.local", action: "approval.decide", entity_type: "approval", entity_id: 9002, created_at: ago(300), detail: { decision: "approve" } },
  ] as AuditEntry[],
  reports: [{ id: 1, task_id: 103, title: "Weekly ops report", status: "published", created_at: ago(290) }] as Report[],
};
