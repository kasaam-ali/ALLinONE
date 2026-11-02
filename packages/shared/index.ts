// Shared TypeScript types mirroring the GODMODE API response shapes.
export type Role = "admin" | "operator" | "viewer";
export type TaskStatus = "queued" | "running" | "awaiting_approval" | "completed" | "rejected" | "failed";
export interface User { id: number; email: string; name: string; role: Role }
export interface Agent { id: number; name: string; role: string; description: string; tools: string[]; status: string }
export interface Step { id: number; position: number; phase: string; agent_name: string; description: string; status: string; output: string }
export interface Plan { id: number; summary: string; steps: Step[] }
export interface Approval { id: number; gate: string; status: "pending" | "approved" | "rejected"; reason: string; decided_at: string | null }
export interface Task { id: number; title: string; prompt: string; status: TaskStatus; requires_approval: boolean; created_at: string; plans?: Plan[]; approvals?: Approval[] }
