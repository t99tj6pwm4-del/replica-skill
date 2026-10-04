"use client";

import JSZip from "jszip";

export const MIN_SELFIES = 12;
export const MAX_SELFIES = 20;
const MAX_SIDE = 1024;
const BUDGET_BYTES = 4_200_000;

async function shrink(file: File, maxSide: number, quality: number): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, w, h);
  bitmap.close();
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("Couldn't read a photo."))), "image/jpeg", quality),
  );
}

// Shrinks the selfies and zips them, stepping quality down until the zip
// fits in one upload.
export async function zipSelfies(files: File[], onProgress?: (done: number) => void): Promise<Blob> {
  for (const [side, quality] of [
    [MAX_SIDE, 0.85],
    [896, 0.8],
    [768, 0.75],
  ] as const) {
    const zip = new JSZip();
    let i = 0;
    for (const f of files) {
      zip.file(`selfie-${String(i + 1).padStart(2, "0")}.jpg`, await shrink(f, side, quality));
      onProgress?.(++i);
    }
    const blob = await zip.generateAsync({ type: "blob", compression: "STORE" });
    if (blob.size <= BUDGET_BYTES) return blob;
  }
  throw new Error("These photos are too big to send even after shrinking. Try fewer photos.");
}
