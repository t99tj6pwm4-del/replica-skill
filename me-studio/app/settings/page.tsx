"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import TabBar from "@/components/TabBar";
import { deleteAllPhotos, listPhotos, loadPersona, savePersona, type Persona } from "@/lib/store";

type Confirm = null | "redo" | "photos" | "everything";

export default function SettingsPage() {
  const router = useRouter();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [photoCount, setPhotoCount] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<Confirm>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setPersona(loadPersona());
    listPhotos().then((p) => setPhotoCount(p.length)).catch(() => setPhotoCount(0));
  }, []);

  async function run(action: Exclude<Confirm, null>) {
    setConfirm(null);
    if (action === "photos" || action === "everything") {
      await deleteAllPhotos().catch(() => undefined);
      setPhotoCount(0);
      setMsg("All photos deleted from this device.");
    }
    if (action === "redo" || action === "everything") {
      savePersona(null);
      router.replace("/setup");
    }
  }

  async function signOut() {
    await fetch("/api/logout", { method: "POST" }).catch(() => undefined);
    window.location.href = "/login";
  }

  const confirmText: Record<Exclude<Confirm, null>, { title: string; body: string; button: string }> = {
    redo: {
      title: "Set up your face again?",
      body: "You'll pick new selfies and pay for training again (about $3.60). Your photos stay.",
      button: "Pick new selfies",
    },
    photos: {
      title: `Delete ${photoCount ?? "all"} photos?`,
      body: "They're removed from this device. Photos you saved to your phone stay there.",
      button: "Delete photos",
    },
    everything: {
      title: "Delete everything?",
      body: "Removes your photos and your face setup from this device. You'd start from scratch.",
      button: "Delete everything",
    },
  };

  return (
    <>
      <main className="page">
        <h1>Settings</h1>

        <section className="card">
          <h2>Your face</h2>
          <p className="muted small">
            {!persona
              ? "Not set up yet."
              : persona.state === "ready"
                ? `Learned from ${persona.selfieCount} selfies on ${new Date(persona.readyAt ?? persona.startedAt).toLocaleDateString()}.`
                : persona.state === "training"
                  ? "Still learning."
                  : "The last setup didn't finish."}
          </p>
          <button className="btn ghost block" onClick={() => setConfirm("redo")}>
            Set up with new selfies
          </button>
        </section>

        <section className="card">
          <h2>Photos</h2>
          <p className="muted small">
            {photoCount === null ? "Counting…" : `${photoCount} photo${photoCount === 1 ? "" : "s"} on this device.`}
          </p>
          <button className="btn danger block" onClick={() => setConfirm("photos")} disabled={!photoCount}>
            Delete all photos
          </button>
        </section>

        {confirm && (
          <section className="card" role="alertdialog" aria-labelledby="confirm-title" style={{ border: "1px solid var(--line)" }}>
            <h2 id="confirm-title">{confirmText[confirm].title}</h2>
            <p className="muted small">{confirmText[confirm].body}</p>
            <div className="row">
              <button className="btn ghost" onClick={() => setConfirm(null)}>Cancel</button>
              <button className={`btn ${confirm === "redo" ? "primary" : "danger"}`} onClick={() => run(confirm)}>
                {confirmText[confirm].button}
              </button>
            </div>
          </section>
        )}
        {msg && <p className="notice ok" role="status">{msg}</p>}

        <section className="card">
          <h2>Privacy</h2>
          <p className="muted small">
            Your photos and face setup are stored in this browser only. Your selfies are sent to fal, the AI service,
            for training and are deleted there after a day. Add this site to your Home Screen so iPhone doesn&apos;t
            clear its storage.
          </p>
          <button className="btn danger block" onClick={() => setConfirm("everything")}>
            Delete everything
          </button>
        </section>

        <button className="btn ghost block" onClick={signOut}>Sign out</button>
      </main>
      <TabBar />
    </>
  );
}
