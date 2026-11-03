// Job: GODMODE Frontend. Purpose: Login page for POST /auth/login, with an explicit fixture-mode escape when the API is unreachable.
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "motion/react";
import { api, tokens } from "@/lib/api";
import { enableFixtureSession } from "@/lib/source";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [down, setDown] = useState(false);
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const reduce = useReducedMotion();
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { tokens.set(await api.login(email, password)); router.push("/"); }
    catch (x) { setErr((x as Error).message); setDown((x as { status?: number }).status === 0 || ((x as { status?: number }).status ?? 0) >= 500); setBusy(false); }
  }
  return (
    <div className="login-wrap">
      <motion.div className="login panel" initial={reduce ? false : { opacity: 0, y: 8, scale: 0.99 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}>
        <div className="brand"><span className="mark">A</span>ALLinONE</div>
        <div><h1>Sign in to Command Center</h1><p className="muted" style={{ margin: "4px 0 0" }}>Autonomous workforce operations</p></div>
        <form onSubmit={submit}>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="username" />
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" />
          {err && <p className="err" role="alert">{err}</p>}
          <button type="submit" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
          {down && <button type="button" className="ghost" onClick={() => { enableFixtureSession(); router.push("/"); }}>Continue with fixture data</button>}
        </form>
      </motion.div>
    </div>
  );
}
