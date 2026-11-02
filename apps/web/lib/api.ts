// Job: GODMODE Frontend. Purpose: Typed /api/v1 client, tokens, and contract path helpers.
import type { Agent, Approval, ApprovalDecision, Artifact, AuditEntry, DashboardSummary, LoginResponse, Report, Run, StageEvent, Task, User } from "./types";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1").replace(/\/$/, "");
const ACCESS = "gm_access_token";
const REFRESH = "gm_refresh_token";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

const store = () => (typeof window === "undefined" ? null : window.localStorage);
export const tokens = {
  access: () => store()?.getItem(ACCESS) ?? null,
  refresh: () => store()?.getItem(REFRESH) ?? null,
  set(r: LoginResponse) {
    store()?.setItem(ACCESS, r.access_token);
    if (r.refresh_token) store()?.setItem(REFRESH, r.refresh_token);
  },
  clear() { store()?.removeItem(ACCESS); store()?.removeItem(REFRESH); },
};

async function raw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(init.headers as Record<string, string>) };
  const t = tokens.access();
  if (t) headers.Authorization = `Bearer ${t}`;
  try {
    return await fetch(API_BASE + path, { ...init, headers });
  } catch {
    throw new ApiError(0, "API unreachable. Check that the backend is running.");
  }
}

async function tryRefresh(): Promise<boolean> {
  const rt = tokens.refresh();
  if (!rt) return false;
  const r = await raw("/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token: rt }) }).catch(() => null);
  if (!r || !r.ok) return false;
  tokens.set(await r.json());
  return true;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let r = await raw(path, init);
  if (r.status === 401 && !path.startsWith("/auth/") && (await tryRefresh())) r = await raw(path, init);
  if (r.status === 401 && !path.startsWith("/auth/login")) {
    tokens.clear();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") window.location.href = "/login";
  }
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    const detail = typeof body?.detail === "string" ? body.detail : r.statusText;
    throw new ApiError(r.status, `${r.status} ${detail || "Request failed"}`);
  }
  return (r.status === 204 ? undefined : await r.json()) as T;
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });
const q = (p: Record<string, string | number | undefined>) => {
  const s = new URLSearchParams(Object.entries(p).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])).toString();
  return s ? `?${s}` : "";
};

export const paths = {
  login: "/auth/login", refresh: "/auth/refresh", me: "/auth/me",
  health: "/health", ready: "/ready",
  agents: "/agents", tasks: "/tasks", runs: "/runs", approvals: "/approvals",
  dashboard: "/dashboard/summary", audit: "/audit", reports: "/reports", memory: "/memory",
} as const;

export const api = {
  login: (email: string, password: string) => request<LoginResponse>(paths.login, post({ email, password })),
  me: () => request<User>(paths.me),
  health: () => request<unknown>(paths.health),
  ready: () => request<unknown>(paths.ready),
  dashboard: () => request<DashboardSummary>(paths.dashboard),
  agents: () => request<Agent[]>(paths.agents),
  tasks: () => request<Task[]>(paths.tasks),
  task: (id: string) => request<Task>(`${paths.tasks}/${id}`),
  run: (id: string | number) => request<Run>(`${paths.runs}/${id}`),
  runEvents: (id: string | number) => request<StageEvent[]>(`${paths.runs}/${id}/events`),
  runArtifacts: (id: string | number) => request<Artifact[]>(`${paths.runs}/${id}/artifacts`),
  approvals: (status?: string) => request<Approval[]>(paths.approvals + q({ status })),
  decide: (id: string | number, decision: ApprovalDecision, note?: string) => request<Approval>(`${paths.approvals}/${id}/decide`, post({ decision, note })),
  audit: (f: { entity_type?: string; entity_id?: string; limit?: number } = {}) => request<AuditEntry[]>(paths.audit + q(f)),
  reports: () => request<Report[]>(paths.reports),
  memory: () => request<unknown[]>(paths.memory),
};
