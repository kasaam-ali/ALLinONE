// Job: GODMODE Frontend. Purpose: App shell with sidebar nav and auth guard for signed-in Command Center pages.
"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { tokens } from "@/lib/api";

export const NAV: [string, string][] = [
  ["/", "Dashboard"],
  ["/tasks", "Tasks"],
  ["/workforce", "Workforce"],
  ["/activity", "Activity"],
  ["/reports", "Reports"],
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (path !== "/login" && !tokens.access()) router.replace("/login");
    else setReady(true);
  }, [path, router]);
  if (path === "/login") return <>{children}</>;
  if (!ready) return null;
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">GOD<span>MODE</span></div>
        <nav className="nav">
          {NAV.map(([h, l]) => (
            <Link key={h} href={h} className={path === h || (h !== "/" && path.startsWith(h)) ? "active" : ""}>{l}</Link>
          ))}
          <a href="#" onClick={(e) => { e.preventDefault(); tokens.clear(); router.push("/login"); }}>Sign out</a>
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
