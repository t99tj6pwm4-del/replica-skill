"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TabBar from "@/components/TabBar";
import PhotoViewer from "@/components/PhotoViewer";
import { addPhotos, loadPersona, newId, type Persona, type Photo } from "@/lib/store";

const IDEAS: { label: string; prompt: string }[] = [
  { label: "Work headshot", prompt: "professional headshot, navy blazer, soft studio light, plain grey background" },
  { label: "Dating profile", prompt: "candid smiling photo at an outdoor café, golden hour, shallow depth of field" },
  { label: "Casual iPhone", prompt: "casual iPhone selfie at the beach, natural light, slightly windy hair" },
  { label: "Hiking", prompt: "hiking on a mountain ridge, backpack, wide landscape behind, overcast light" },
  { label: "Cinematic", prompt: "cinematic film still, neon-lit city street at night, rain, 35mm film grain" },
  { label: "Black and white", prompt: "black and white portrait, dramatic window light, high contrast" },
];

const SHAPES = [
  { id: "portrait_4_3", label: "Tall" },
  { id: "square_hd", label: "Square" },
  { id: "landscape_4_3", label: "Wide" },
] as const;

export default function CreatePage() {
  const [persona, setPersona] = useState<Persona | null | undefined>(undefined);
  const [prompt, setPrompt] = useState("");
  const [shape, setShape] = useState<(typeof SHAPES)[number]["id"]>("portrait_4_3");
  const [count, setCount] = useState<1 | 2 | 4>(2);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState<Photo[]>([]);
  const [open, setOpen] = useState<Photo | null>(null);

  useEffect(() => setPersona(loadPersona()), []);

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    if (!persona?.loraUrl || !prompt.trim()) return;
    setBusy(true);
    setError("");
    setResults([]);
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt, loraUrl: persona.loraUrl, count, shape }),
    }).catch(() => null);
    const body = await res?.json().catch(() => null);
    if (!res?.ok || !Array.isArray(body?.images)) {
      setError(body?.error ?? "Couldn't connect. Check your internet and try again.");
      setBusy(false);
      return;
    }
    const now = Date.now();
    const photos: Photo[] = body.images.map((dataUrl: string, i: number) => ({
      id: newId(),
      prompt: prompt.trim(),
      createdAt: now + i,
      dataUrl,
    }));
    setResults(photos);
    setBusy(false);
    addPhotos(photos).catch(() => setError("Made the photos, but couldn't save them to the gallery. Save them now."));
  }

  if (persona === undefined) return <main className="page" aria-busy="true" />;

  if (!persona || persona.state !== "ready") {
    return (
      <main className="page no-tabs">
        <h1>Set up your face first</h1>
        <p className="muted">It needs to learn what you look like before it can make photos of you.</p>
        <Link className="btn primary block" href={persona ? "/training" : "/setup"}>
          {persona ? "Check on training" : "Get started"}
        </Link>
      </main>
    );
  }

  return (
    <>
      <main className="page">
        <h1>Make a photo of you</h1>
        <form onSubmit={generate} style={{ display: "grid", gap: 14 }}>
          <div className="field">
            <label htmlFor="prompt">Describe the scene</label>
            <textarea
              id="prompt"
              className="input"
              placeholder="e.g. laughing at a rooftop party in New York, warm string lights"
              value={prompt}
              maxLength={500}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
          <div className="chips" role="group" aria-label="Ideas">
            {IDEAS.map((idea) => (
              <button
                type="button"
                key={idea.label}
                className="chip"
                aria-pressed={prompt === idea.prompt}
                onClick={() => setPrompt(idea.prompt)}
              >
                {idea.label}
              </button>
            ))}
          </div>
          <div className="row between">
            <div className="seg" role="group" aria-label="Shape">
              {SHAPES.map((s) => (
                <button type="button" key={s.id} aria-pressed={shape === s.id} onClick={() => setShape(s.id)}>
                  {s.label}
                </button>
              ))}
            </div>
            <div className="seg" role="group" aria-label="How many">
              {([1, 2, 4] as const).map((n) => (
                <button type="button" key={n} aria-pressed={count === n} onClick={() => setCount(n)}>
                  {n}
                </button>
              ))}
            </div>
          </div>
          <button className="btn primary block" disabled={busy || !prompt.trim()}>
            {busy ? "Making your photos…" : `Make ${count} photo${count > 1 ? "s" : ""}`}
          </button>
          <p className="muted small" style={{ textAlign: "center" }}>
            About 3¢ per photo on your fal account.
          </p>
        </form>

        {error && <p className="notice error" role="alert">{error}</p>}

        {(busy || results.length > 0) && (
          <section style={{ display: "grid", gap: 10 }} aria-live="polite">
            <h2>{busy ? "Working on it…" : "Here you go"}</h2>
            <div className="grid two">
              {busy
                ? Array.from({ length: count }, (_, i) => <div key={i} className="tile skeleton" />)
                : results.map((p, i) => (
                    <button key={p.id} className="tile" onClick={() => setOpen(p)} aria-label={`Open photo ${i + 1}`}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={p.dataUrl} alt={`AI photo: ${p.prompt}`} />
                    </button>
                  ))}
            </div>
            {!busy && <p className="muted small">Saved to your gallery. Tap a photo to save it to your phone.</p>}
          </section>
        )}
      </main>
      {open && <PhotoViewer photo={open} onClose={() => setOpen(null)} />}
      <TabBar />
    </>
  );
}
