// Job: ALLinONE Frontend. Purpose: Page-facing data functions combining the /api/v1 client with fixture fallback.
import { api } from "./api";
import { fx } from "./fixtures";
import { forcedFixtures, liveOr } from "./source";
import type { Approval, ApprovalDecision, Run, Task, TaskCreate } from "./types";

export const data = {
  dashboard: () => liveOr(api.dashboard, () => fx.dashboard),
  agents: () => liveOr(api.agents, () => fx.agents),
  tasks: () => liveOr(api.tasks, () => fx.tasks),
  task: (id: string) => liveOr(() => api.task(id), () => fx.tasks.find((t) => String(t.id) === id) ?? fx.tasks[0]),
  run: (id: string | number) => liveOr(() => api.run(id), () => fx.run(id)),
  runEvents: (id: string | number) => liveOr(() => api.runEvents(id), () => fx.events(id)),
  runArtifacts: (id: string | number) => liveOr(() => api.runArtifacts(id), () => fx.artifacts(id)),
  approvals: () => liveOr(() => api.approvals(), () => fx.approvals),
  audit: () => liveOr(() => api.audit({ limit: 200 }), () => fx.audit),
  integrations: () => liveOr(api.integrations, () => [] as unknown[]),
  reports: () => liveOr(api.reports, () => fx.reports),
  createTask: async (body: TaskCreate): Promise<Task> => {
    if (forcedFixtures()) {
      const t: Task = {
        id: Date.now(),
        title: body.title,
        description: body.description || "",
        priority: body.priority ?? 0,
        status: "draft",
        latest_run_id: null,
        created_at: new Date().toISOString(),
      };
      fx.tasks.unshift(t);
      return t;
    }
    return api.createTask(body);
  },
  startTask: async (id: string | number): Promise<Run> => {
    if (forcedFixtures()) {
      const t = fx.tasks.find((x) => String(x.id) === String(id));
      if (t) { t.status = "awaiting_approval"; t.latest_run_id = 501; }
      return fx.run(501);
    }
    return api.startTask(id);
  },
  decide: async (id: string | number, d: ApprovalDecision): Promise<Approval> => {
    if (forcedFixtures()) {
      const a = fx.approvals.find((x) => x.id === id)!;
      a.status = d === "approve" ? "approved" : "rejected";
      return a;
    }
    return api.decide(id, d);
  },
};
