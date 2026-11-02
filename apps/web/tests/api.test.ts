// API client tests: verify contract paths and error handling with a mocked fetch.
import { afterEach, describe, expect, it, vi } from "vitest";
import { api, paths, tokens } from "@/lib/api";

const ok = (body: unknown) => new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
afterEach(() => { vi.restoreAllMocks(); tokens.clear(); });

describe("api client", () => {
  it("uses the canonical /api/v1 paths", () => {
    expect(paths).toMatchObject({ agents: "/agents", memory: "/memory", dashboard: "/dashboard/summary", me: "/auth/me" });
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
  it("reports an unreachable API clearly", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fetch failed"));
    await expect(api.dashboard()).rejects.toThrow(/unreachable/);
  });
});
