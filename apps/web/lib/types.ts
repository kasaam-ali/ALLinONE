// Job: ALLinONE Frontend. Purpose: Frontend TypeScript types aligned to live /api/v1 Backend DTOs.
export type Role = "viewer" | "operator" | "admin";
export type Gate = "after_plan" | "before_publish";
export type ApprovalDecision = "approve" | "reject";

export interface User {
  id: string | number;
  email: string;
  display_name?: string;
  name?: string;
  role: Role;
}
export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  user?: User;
}
export interface Agent {
  id: string | number;
  slug: string;
  name: string;
  role_prompt?: string;
  tools_allowlist?: string[];
  status: string;
  version?: number;
}
export interface TaskCreate {
  title: string;
  description?: string;
  priority?: number;
}
export interface Task {
  id: string | number;
  title?: string;
  description?: string;
  prompt?: string;
  priority?: number;
  status: string;
  created_at?: string;
  updated_at?: string;
  latest_run_id?: string | number | null;
  [k: string]: unknown;
}
export interface Run {
  id: string | number;
  task_id: string | number;
  status: string;
  current_stage?: string;
  stage?: string;
  started_at?: string;
  finished_at?: string;
  error_summary?: string | null;
  mock_llm?: boolean;
}
export interface StageEvent {
  id: string | number;
  run_id: string | number;
  stage: string;
  status?: string;
  message?: string;
  created_at?: string;
}
export interface Artifact {
  id: string | number;
  run_id: string | number;
  kind?: string;
  name?: string;
  created_at?: string;
}
export interface Approval {
  id: string | number;
  run_id?: string | number;
  task_id?: string | number;
  gate: Gate;
  status: string;
  created_at?: string;
}
export interface Report {
  id: string | number;
  task_id?: string | number;
  title?: string;
  status?: string;
  created_at?: string;
}
export interface AuditEntry {
  id: string | number;
  actor_user_id?: string | number | null;
  actor?: string;
  action: string;
  entity_type?: string;
  entity_id?: string | number;
  after_json?: unknown;
  created_at?: string;
  detail?: unknown;
}
export interface DashboardSummary {
  tasks_total: number;
  tasks_by_status: Record<string, number>;
  runs_by_status: Record<string, number>;
  pending_approvals: number;
  agents_active: number;
  reports_total: number;
  recent_audit?: AuditEntry[];
}
