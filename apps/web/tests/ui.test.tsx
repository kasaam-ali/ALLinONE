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
