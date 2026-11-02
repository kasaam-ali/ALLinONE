// Job: GODMODE Frontend. Purpose: Vitest coverage for the API client path contract.
import { afterEach, describe, expect, it, vi } from "vitest";
import { api, paths, tokens } from "@/lib/api";

const ok = (body: unknown) => new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
afterEach(() => { vi.restoreAllMocks(); tokens.clear(); });

describe("api client", () => {
  it("uses the canonical /api/v1 paths", () => {
    expect(paths).toMatchObject({ agents: "/agents", memory: "/memory", dashboard: "/dashboard/summary", me: "/auth/me", integrations: "/integrations" });
  });
  it("logs in and stores the token, then sends it", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(ok({ access_token: "abc" })).mockResolvedValueOnce(ok({ id: 1, email: "a@b.c", role: "admin" }));
    tokens.set(await api.login("a@b.c", "pw"));
    await api.me();
    expect(f.mock.calls[0][0]).toBe("/api/v1/auth/login");
    expect((f.mock.calls[1][1]!.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });
  it("posts approval decisions to /approvals/{id}/decide", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(ok({}));
    await api.decide(7, "approve", "ok");
    expect(f.mock.calls[0][0]).toBe("/api/v1/approvals/7/decide");
    expect(JSON.parse(f.mock.calls[0][1]!.body as string)).toEqual({ decision: "approve", note: "ok" });
  });
  it("lists integrations via GET /integrations (empty list)", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(ok([]));
    await expect(api.integrations()).resolves.toEqual([]);
    expect(f.mock.calls[0][0]).toBe("/api/v1/integrations");
  });
  it("reports an unreachable API clearly", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fetch failed"));
    await expect(api.dashboard()).rejects.toThrow(/unreachable/);
  });
});

  it("creates a task via POST /tasks", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(ok({ id: 9, title: "n", status: "draft" }));
    await api.createTask({ title: "n", description: "d" });
    expect(f.mock.calls[0][0]).toBe("/api/v1/tasks");
    expect(f.mock.calls[0][1]!.method).toBe("POST");
    expect(JSON.parse(f.mock.calls[0][1]!.body as string)).toEqual({ title: "n", description: "d" });
  });

  it("starts a task via POST /tasks/{id}/start", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValue(ok({ id: 1, task_id: 9, status: "queued" }));
    await api.startTask(9);
    expect(f.mock.calls[0][0]).toBe("/api/v1/tasks/9/start");
  });

