"use client";

import { useEffect, useState } from "react";
import type { Photo } from "@/lib/store";
import { saveOrShare } from "@/lib/share";

type Props = {
  photo: Photo;
  onClose: () => void;
  onDelete?: (id: string) => void;
};

export default function PhotoViewer({ photo, onClose, onDelete }: Props) {
  const [msg, setMsg] = useState("");
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function share() {
    const r = await saveOrShare(photo.dataUrl, `me-studio-${photo.createdAt}`);
    setMsg(r === "downloaded" ? "Downloaded." : "");
  }

  return (
    <div className="viewer" role="dialog" aria-modal="true" aria-label="Photo">
      <div className="row between">
        <button className="btn small ghost" onClick={onClose} autoFocus>
          Close
        </button>
        {onDelete &&
          (confirming ? (
            <div className="row">
              <button className="btn small ghost" onClick={() => setConfirming(false)}>Keep</button>
              <button className="btn small danger" onClick={() => onDelete(photo.id)}>Delete photo</button>
            </div>
          ) : (
            <button className="btn small danger" onClick={() => setConfirming(true)}>Delete</button>
          ))}
      </div>
      <div className="stage">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={photo.dataUrl} alt={`AI photo: ${photo.prompt}`} />
      </div>
      <div style={{ display: "grid", gap: 10 }}>
        <p className="caption">{photo.prompt}</p>
        <button className="btn primary block" onClick={share}>
          Save or share
        </button>
        {msg && <p className="caption" role="status">{msg}</p>}
      </div>
    </div>
  );
}
