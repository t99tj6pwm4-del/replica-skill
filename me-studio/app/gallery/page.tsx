"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TabBar from "@/components/TabBar";
import PhotoViewer from "@/components/PhotoViewer";
import { deletePhoto, listPhotos, type Photo } from "@/lib/store";

export default function GalleryPage() {
  const [photos, setPhotos] = useState<Photo[] | null>(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState<Photo | null>(null);

  useEffect(() => {
    listPhotos()
      .then(setPhotos)
      .catch(() => {
        setPhotos([]);
        setError("Couldn't open your gallery on this device.");
      });
  }, []);

  async function remove(id: string) {
    await deletePhoto(id).catch(() => setError("Couldn't delete that photo. Try again."));
    setPhotos((prev) => prev?.filter((p) => p.id !== id) ?? null);
    setOpen(null);
  }

  return (
    <>
      <main className="page">
        <div className="row between">
          <h1>Gallery</h1>
          {photos && photos.length > 0 && <span className="muted small counter">{photos.length} photos</span>}
        </div>
        {error && <p className="notice error" role="alert">{error}</p>}
        {photos === null ? (
          <div className="grid">
            {Array.from({ length: 6 }, (_, i) => <div key={i} className="tile skeleton" />)}
          </div>
        ) : photos.length === 0 ? (
          <div className="empty">
            <h2>No photos yet</h2>
            <p className="muted">Photos you make show up here.</p>
            <Link className="btn primary" href="/create">Make one</Link>
          </div>
        ) : (
          <>
            <div className="grid">
              {photos.map((p) => (
                <button key={p.id} className="tile" onClick={() => setOpen(p)} aria-label={`Open: ${p.prompt}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={p.dataUrl} alt="" loading="lazy" />
                </button>
              ))}
            </div>
            <p className="muted small">
              These are kept in this browser only. Save the ones you love to your phone so you don&apos;t lose them.
            </p>
          </>
        )}
      </main>
      {open && <PhotoViewer photo={open} onClose={() => setOpen(null)} onDelete={remove} />}
      <TabBar />
    </>
  );
}
