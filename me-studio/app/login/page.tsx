"use client";

import { useState } from "react";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ password }),
    }).catch(() => null);
    if (res?.ok) {
      window.location.href = "/";
      return;
    }
    const body = await res?.json().catch(() => null);
    setError(body?.error ?? "Couldn't connect. Check your internet and try again.");
    setBusy(false);
  }

  return (
    <main className="page no-tabs" style={{ alignContent: "center", minHeight: "100dvh" }}>
      <div style={{ display: "grid", gap: 8 }}>
        <span className="eyebrow">Me Studio</span>
        <h1>Realistic photos of you, made by AI</h1>
        <p className="muted">This is your private copy. Enter your password to open it.</p>
      </div>
      <form onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="notice error" role="alert">{error}</p>}
        <button className="btn primary block" disabled={busy || !password}>
          {busy ? "Opening…" : "Open"}
        </button>
      </form>
    </main>
  );
}
