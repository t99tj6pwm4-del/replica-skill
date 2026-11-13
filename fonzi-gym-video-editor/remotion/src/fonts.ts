import { continueRender, delayRender, staticFile } from "remotion";

export const DISPLAY = "FonziDisplay";
export const BODY = "FonziBody";

let started = false;

// Fonts ship with the project (public/fonts, SIL Open Font License) so renders work offline.
export const loadFonts = () => {
  if (started || typeof document === "undefined") return;
  started = true;
  const handle = delayRender("Loading fonts");
  const faces = [
    new FontFace(DISPLAY, `url(${staticFile("fonts/Anton-Regular.ttf")})`),
    new FontFace(BODY, `url(${staticFile("fonts/Montserrat.ttf")})`, {
      weight: "100 900",
    }),
  ];
  Promise.all(faces.map((f) => f.load()))
    .then((loaded) => {
      loaded.forEach((f) => (document.fonts as unknown as { add: (x: FontFace) => void }).add(f));
      continueRender(handle);
    })
    .catch((err) => {
      console.error("Font load failed", err);
      continueRender(handle);
    });
};
