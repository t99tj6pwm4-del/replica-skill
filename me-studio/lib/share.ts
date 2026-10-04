"use client";

function dataUrlToFile(dataUrl: string, name: string): File {
  const [head, b64] = dataUrl.split(",");
  const type = head.match(/data:([^;]+)/)?.[1] ?? "image/jpeg";
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const ext = type === "image/svg+xml" ? "svg" : type.split("/")[1] ?? "jpg";
  return new File([bytes], `${name}.${ext}`, { type });
}

// On iPhone this opens the share sheet, which has "Save Image" for Photos.
// Elsewhere it falls back to a download.
export async function saveOrShare(dataUrl: string, name: string): Promise<"shared" | "downloaded" | "cancelled"> {
  const file = dataUrlToFile(dataUrl, name);
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file] });
      return "shared";
    } catch (err) {
      if ((err as DOMException)?.name === "AbortError") return "cancelled";
    }
  }
  const url = URL.createObjectURL(file);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
  return "downloaded";
}
