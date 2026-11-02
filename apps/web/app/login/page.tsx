// Job: GODMODE Frontend. Purpose: Login page that exchanges email/password for JWT tokens via /api/v1/auth/login.
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, tokens } from "@/lib/api";

export default function Login() {
  const [email, setEmail] = useState("admin@godmode.local");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const r = await api.login(email, password);
      tokens.set(r);
      router.push("/");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Login failed");
    }
  }
  return (
    <div className="login card">
      <div className="brand">GOD<span>MODE</span></div>
      <h1>Sign in</h1>
      <form onSubmit={submit}>
        <p><input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" /></p>
        <p><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" /></p>
        {err && <p className="err">{err}</p>}
        <button type="submit">Sign in</button>
      </form>
    </div>
  );
}
