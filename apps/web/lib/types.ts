// Domain types: frontend view of the /api/v1 contract (Task, Run, StageEvent, Artifact, Approval).
export type Role = "viewer" | "operator" | "admin";
export type Gate = "after_plan" | "before_publish";
export type ApprovalDecision = "approve" | "reject";

export interface User { id: string | number; email: string; name?: string; role: Role }
export interface LoginResponse { access_token: string; refresh_token?: string; token_type?: string; user?: User }
export interface Agent { id: string | number; name: string; role?: string; description?: string; status: string; tools?: unknown }
export interface Task { id: string | number; title?: string; prompt?: string; status: string; created_at?: string; latest_run_id?: string | number | null; [k: string]: unknown }
export interface Run { id: string | number; task_id: string | number; status: string; stage?: string; started_at?: string; finished_at?: string }
export interface StageEvent { id: string | number; run_id: string | number; stage: string; status?: string; message?: string; created_at?: string }
export interface Artifact { id: string | number; run_id: string | number; kind?: string; name?: string; created_at?: string }
export interface Approval { id: string | number; run_id?: string | number; task_id?: string | number; gate: Gate; status: string; created_at?: string }
export interface Report { id: string | number; task_id?: string | number; title?: string; status?: string; created_at?: string }
export interface AuditEntry { id: string | number; actor?: string; action: string; entity_type?: string; entity_id?: string | number; created_at?: string; detail?: unknown }
export interface DashboardSummary { running: number; awaiting_approval: number; failed_24h: number; agents_by_status: Record<string, number> }
