// Job: GODMODE Frontend. Purpose: App shell with sidebar nav, animated active pill, Live/Fixture chip, page transitions, and auth guard.
"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { tokens } from "@/lib/api";
import { clearFixtureSession, forcedFixtures } from "@/lib/source";

export const NAV: [string, string][] = [
  ["/", "Dashboard"],
  ["/tasks", "Tasks"],
  ["/workforce", "Workforce"],
  ["/activity", "Activity"],
  ["/reports", "Reports"],
];

export function FixtureBadge({ on }: { on: boolean }) {
  return on ? <span className="chip fixture" title="API unreachable or fixtures forced. Data is local fixture data.">Fixture</span>
    : <span className="chip live">Live</span>;
}

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [fixture, setFixture] = useState(false);
  useEffect(() => {
    if (path !== "/login" && !tokens.access() && !forcedFixtures()) router.replace("/login");
    else setReady(true);
  }, [path, router]);
  useEffect(() => {
    setFixture(forcedFixtures());
    const onFix = () => setFixture(true);
    const onLive = () => { if (!forcedFixtures()) setFixture(false); };
    window.addEventListener("gm:fixture", onFix);
    window.addEventListener("gm:live", onLive);
    return () => { window.removeEventListener("gm:fixture", onFix); window.removeEventListener("gm:live", onLive); };
  }, []);
  if (path === "/login") return <>{children}</>;
  if (!ready) return null;
  const active = (h: string) => path === h || (h !== "/" && path.startsWith(h));
  const crumb = NAV.find(([h]) => active(h))?.[1] ?? "";
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><span className="mark">A</span>ALLinONE</div>
        <nav className="nav" aria-label="Primary">
          {NAV.map(([h, l]) => (
            <Link key={h} href={h} className={active(h) ? "active" : ""} aria-current={active(h) ? "page" : undefined}>
              {active(h) && <motion.span layoutId="nav-pill" className="pill" transition={{ type: "spring", stiffness: 500, damping: 40 }} />}
              {l}
            </Link>
          ))}
        </nav>
        <div className="foot">
          <button className="ghost sm" onClick={() => { tokens.clear(); clearFixtureSession(); router.push("/login"); }}>Sign out</button>
        </div>
      </aside>
      <main className="main">
        <header className="top"><span className="crumb">Command Center</span><span className="muted">/</span><span>{crumb}</span><span className="spacer" /><FixtureBadge on={fixture} /></header>
        <AnimatePresence mode="wait"><div key={path}>{children}</div></AnimatePresence>
      </main>
    </div>
  );
}
