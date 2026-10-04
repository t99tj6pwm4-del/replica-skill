"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { loadPersona, savePersona, type Persona } from "@/lib/store";

const TYPICAL_MS = 10 * 60 * 1000;
const POLL_MS = 15_000;

export default function TrainingPage() {
  const router = useRouter();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [netError, setNetError] = useState("");

  const check = useCallback(async (p: Persona) => {
    const res = await fetch(`/api/persona/${encodeURIComponent(p.jobId)}`).catch(() => null);
    const body = await res?.json().catch(() => null);
    if (!res?.ok || !body?.state) {
      setNetError(body?.error ?? "Can't reach the server right now. Still trying.");
      return;
    }
    setNetError("");
    if (body.state === "ready") {
      const next: Persona = { ...p, state: "ready", loraUrl: body.loraUrl, readyAt: Date.now() };
      savePersona(next);
      setPersona(next);
    } else if (body.state === "failed") {
      const next: Persona = { ...p, state: "failed", error: body.error };
      savePersona(next);
      setPersona(next);
    }
  }, []);

  useEffect(() => {
    const p = loadPersona();
    if (!p) {
      router.replace("/setup");
      return;
    }
    setPersona(p);
    if (p.state !== "training") return;
    check(p);
    const poll = setInterval(() => check(p), POLL_MS);
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => {
      clearInterval(poll);
      clearInterval(tick);
    };
  }, [router, check]);

  if (!persona) return <main className="page no-tabs" aria-busy="true" />;

  if (persona.state === "ready") {
    return (
      <main className="page no-tabs">
        <span className="eyebrow">Step 2 of 2</span>
        <h1>It knows your face now</h1>
        <p className="muted">Describe any scene and it will make photos of you in it.</p>
        <Link className="btn primary block" href="/create">
          Make my first photo
        </Link>
      </main>
    );
  }

  if (persona.state === "failed") {
    return (
      <main className="page no-tabs">
        <h1>Training didn&apos;t work</h1>
        <p className="notice error" role="alert">{persona.error ?? "Something went wrong."}</p>
        <p className="muted">
          This usually means the AI service ran out of balance, or the photos were hard to read. Check your fal
          account, then try again.
        </p>
        <button
          className="btn primary block"
          onClick={() => {
            savePersona(null);
            router.replace("/setup");
          }}
        >
          Choose photos again
        </button>
      </main>
    );
  }

  const elapsed = now - persona.startedAt;
  const pct = Math.min(95, Math.round((elapsed / TYPICAL_MS) * 100));
  const mins = Math.floor(elapsed / 60000);

  return (
    <main className="page no-tabs">
      <span className="eyebrow">Step 2 of 2</span>
      <h1>Learning your face</h1>
      <p className="muted">
        Using your {persona.selfieCount} photos. This usually takes about 10 minutes. You can close the app and come
        back; it keeps going.
      </p>
      <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Training progress estimate">
        <span style={{ width: `${pct}%` }} />
      </div>
      <p className="muted small">
        {mins < 1 ? "Just started" : `${mins} min so far`}
        {elapsed > TYPICAL_MS * 2 ? ". Taking longer than usual, but still going." : ""}
      </p>
      {netError && <p className="notice small">{netError}</p>}
    </main>
  );
}
