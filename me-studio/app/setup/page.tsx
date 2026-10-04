"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { MAX_SELFIES, MIN_SELFIES, zipSelfies } from "@/lib/selfies";
import { savePersona } from "@/lib/store";

type Picked = { file: File; url: string };

export default function SetupPage() {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [picked, setPicked] = useState<Picked[]>([]);
  const [phase, setPhase] = useState<"pick" | "preparing" | "sending">("pick");
  const [prepared, setPrepared] = useState(0);
  const [error, setError] = useState("");

  const pickedRef = useRef(picked);
  pickedRef.current = picked;
  useEffect(() => () => pickedRef.current.forEach((p) => URL.revokeObjectURL(p.url)), []);

  const count = picked.length;
  const ready = count >= MIN_SELFIES && count <= MAX_SELFIES;
  const hint = useMemo(() => {
    if (count === 0) return `Pick ${MIN_SELFIES} to ${MAX_SELFIES} photos of yourself.`;
    if (count < MIN_SELFIES) return `Add ${MIN_SELFIES - count} more.`;
    if (count > MAX_SELFIES) return `Remove ${count - MAX_SELFIES}. ${MAX_SELFIES} is the most it uses.`;
    return "Good to go.";
  }, [count]);

  function add(files: FileList | null) {
    if (!files) return;
    const images = Array.from(files).filter((f) => f.type.startsWith("image/"));
    setPicked((prev) => [...prev, ...images.map((file) => ({ file, url: URL.createObjectURL(file) }))]);
    setError("");
    if (input.current) input.current.value = "";
  }

  function remove(i: number) {
    setPicked((prev) => {
      URL.revokeObjectURL(prev[i].url);
      return prev.filter((_, j) => j !== i);
    });
  }

  async function start() {
    setError("");
    try {
      setPhase("preparing");
      setPrepared(0);
      const zip = await zipSelfies(picked.map((p) => p.file), setPrepared);
      setPhase("sending");
      const form = new FormData();
      form.append("selfies", zip, "selfies.zip");
      const res = await fetch("/api/persona", { method: "POST", body: form });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body.jobId) throw new Error(body.error ?? "Couldn't start. Try again.");
      savePersona({ state: "training", jobId: body.jobId, selfieCount: count, startedAt: Date.now() });
      router.replace("/training");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't start. Try again.");
      setPhase("pick");
    }
  }

  const busy = phase !== "pick";

  return (
    <main className="page no-tabs">
      <div style={{ display: "grid", gap: 8 }}>
        <span className="eyebrow">Step 1 of 2</span>
        <h1>Teach it your face</h1>
        <p className="muted">
          Pick {MIN_SELFIES} to {MAX_SELFIES} recent photos where your face is clear. You only do this once.
        </p>
      </div>

      <div className="card">
        <h2>What works best</h2>
        <ul className="muted small" style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 4 }}>
          <li>Just you in the photo, no one else</li>
          <li>A mix of angles, places and lighting</li>
          <li>Some close-ups and some from the waist up</li>
          <li>No sunglasses, hats or heavy filters</li>
        </ul>
      </div>

      <input
        ref={input}
        id="selfies"
        type="file"
        accept="image/*"
        multiple
        hidden
        onChange={(e) => add(e.target.files)}
      />

      <div className="row between">
        <span className={`counter ${ready ? "good" : ""}`} aria-live="polite">
          {count} / {MAX_SELFIES} photos
        </span>
        <button className="btn small ghost" onClick={() => input.current?.click()} disabled={busy}>
          {count === 0 ? "Choose photos" : "Add more"}
        </button>
      </div>
      <p className="muted small">{hint}</p>

      {count > 0 ? (
        <div className="grid">
          {picked.map((p, i) => (
            <div className="tile" key={p.url}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.url} alt={`Selfie ${i + 1}`} />
              {!busy && (
                <button className="remove" onClick={() => remove(i)} aria-label={`Remove selfie ${i + 1}`}>
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <button className="card empty" onClick={() => input.current?.click()} style={{ border: "1px dashed var(--line)", cursor: "pointer" }}>
          <h2>No photos yet</h2>
          <p className="muted small">Tap to choose from your photo library.</p>
        </button>
      )}

      {error && <p className="notice error" role="alert">{error}</p>}

      <div style={{ display: "grid", gap: 8 }}>
        <button className="btn primary block" onClick={start} disabled={!ready || busy}>
          {phase === "preparing"
            ? `Preparing ${prepared} of ${count}…`
            : phase === "sending"
              ? "Sending…"
              : "Start learning my face"}
        </button>
        <p className="muted small" style={{ textAlign: "center" }}>
          Costs about $3.60 on your fal account. Takes around 10 minutes.
        </p>
      </div>
    </main>
  );
}
