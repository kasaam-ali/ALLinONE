// Job: GODMODE Frontend. Purpose: Vitest UI smoke tests for login, nav, and error state.
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn() }), usePathname: () => "/login" }));
import Login from "@/app/login/page";
import { ErrorBox } from "@/components/State";
import { NAV } from "@/app/Shell";

describe("ui", () => {
  it("renders the login form", () => {
    render(<Login />);
    expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/email/i)).toBeTruthy();
  });
  it("shell nav lists all sections", () => {
    const labels = NAV.map((n) => n[1]).join("|");
    for (const l of ["Dashboard", "Tasks", "Workforce", "Activity", "Reports"]) expect(labels).toContain(l);
  });
  it("shows an error state", () => {
    render(<ErrorBox message="API unreachable" />);
    expect(screen.getByRole("alert").textContent).toMatch(/API unreachable/);
  });
});

describe("fixtures", () => {
  it("falls back to fixtures when the API is unreachable and flags it", async () => {
    const { liveOr } = await import("@/lib/source");
    const seen = vi.fn(); window.addEventListener("gm:fixture", seen);
    const v = await liveOr(() => Promise.reject(Object.assign(new Error("x"), { status: 0 })), () => 42);
    expect(v).toBe(42); expect(seen).toHaveBeenCalled();
  });
  it("surfaces auth errors instead of faking data", async () => {
    const { liveOr } = await import("@/lib/source");
    await expect(liveOr(() => Promise.reject(Object.assign(new Error("401"), { status: 401 })), () => 1)).rejects.toThrow("401");
  });
  it("uses canonical workforce slugs", async () => {
    const { fx } = await import("@/lib/fixtures");
    expect(fx.agents.map((a) => a.slug)).toEqual(["planner", "researcher", "executor", "verifier", "reporter"]);
  });
});
