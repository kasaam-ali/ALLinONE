// Login page: POST /auth/login with email and password, stores tokens, then opens the dashboard.
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, tokens } from "@/lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { tokens.set(await api.login(email, password)); router.push("/"); }
    catch (x) { setErr((x as Error).message); setBusy(false); }
  }
  return (
    <div className="login card">
      <div className="brand">GOD<span>MODE</span></div>
      <h1>Sign in</h1>
      <form onSubmit={submit}>
        <p><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="username" /></p>
        <p><input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" /></p>
        {err && <p className="err" role="alert">{err}</p>}
        <button type="submit" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
      </form>
    </div>
  );
}
