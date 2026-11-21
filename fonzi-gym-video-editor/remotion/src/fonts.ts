import { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

export const DISPLAY = "FonziDisplay";
export const BODY = "FonziBody";
// Pop-up cards (Alfonso, 2026-11-17): Montserrat at exact weights. BODY carries the full 100-900 range.
export const MONTSERRAT = BODY;
export const WEIGHT = { regular: 400, bold: 700, extraBold: 800 } as const;

let ready: Promise<void> | null = null;

// Fonts ship with the project (public/fonts, SIL Open Font License) so renders work offline.
const loadOnce = (): Promise<void> => {
  if (!ready) {
    const faces = [
      // Alfonso (2026-11-16): Montserrat everywhere. Headlines = Montserrat Black (the weight range is pinned
      // to 900, so every DISPLAY text renders Black); small text = BODY, the full variable range.
      new FontFace(DISPLAY, `url(${staticFile("fonts/Montserrat.ttf")})`, { weight: "900" }),
      new FontFace(BODY, `url(${staticFile("fonts/Montserrat.ttf")})`, { weight: "100 900" }),
    ];
    ready = Promise.all(faces.map((f) => f.load())).then((loaded) => {
      loaded.forEach((f) => (document.fonts as unknown as { add: (x: FontFace) => void }).add(f));
    });
  }
  return ready;
};

// Call at the top of every composition: holds the frame until the fonts are in.
export const useFonts = () => {
  const [handle] = useState(() => delayRender("Loading fonts", { timeoutInMilliseconds: 60000, retries: 2 }));
  useEffect(() => {
    loadOnce()
      .catch((err) => console.error("Font load failed", err))
      .finally(() => continueRender(handle));
  }, [handle]);
};
