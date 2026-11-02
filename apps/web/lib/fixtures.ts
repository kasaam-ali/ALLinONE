// Job: GODMODE Frontend. Purpose: Fixture data in live /api/v1 DTO shapes, used only when the API is unreachable or fixtures are forced.
import type { Agent, Approval, Artifact, AuditEntry, DashboardSummary, Report, Run, StageEvent, Task } from "./types";

const ago = (m: number) => new Date(Date.now() - m * 60000).toISOString();

export const fx = {
  agents: [
    { id: 1, slug: "planner", name: "Atlas", role_prompt: "Break objectives into plans", tools_allowlist: ["http_fetch"], status: "active", version: 1 },
    { id: 2, slug: "researcher", name: "Scout", role_prompt: "Gather context", tools_allowlist: ["http_fetch", "browser_stub"], status: "active", version: 1 },
    { id: 3, slug: "executor", name: "Forge", role_prompt: "Execute steps with tools", tools_allowlist: ["http_fetch", "browser_stub", "webhook_inbound"], status: "active", version: 1 },
    { id: 4, slug: "verifier", name: "Sentinel", role_prompt: "Verify outputs", tools_allowlist: ["http_fetch"], status: "active", version: 1 },
    { id: 5, slug: "reporter", name: "Scribe", role_prompt: "Write reports", tools_allowlist: [], status: "active", version: 1 },
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
  dashboard: {
    tasks_total: 4,
    tasks_by_status: { awaiting_approval: 1, running: 1, completed: 1, failed: 1 },
    runs_by_status: { awaiting_approval: 1, running: 1, completed: 1 },
    pending_approvals: 1,
    agents_active: 5,
    reports_total: 1,
    recent_audit: [],
  } as DashboardSummary,
  audit: [
    { id: 1, actor_user_id: 1, actor: "planner", action: "run.stage", entity_type: "run", entity_id: 501, created_at: ago(13) },
    { id: 2, actor_user_id: null, actor: "system", action: "approval.opened", entity_type: "approval", entity_id: 9001, created_at: ago(12) },
    { id: 3, actor_user_id: 1, actor: "admin@godmode.local", action: "approval.decide", entity_type: "approval", entity_id: 9002, created_at: ago(300), after_json: { decision: "approve" } },
  ] as AuditEntry[],
  reports: [{ id: 1, task_id: 103, title: "Weekly ops report", status: "published", created_at: ago(290) }] as Report[],
};
