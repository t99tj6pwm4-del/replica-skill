import React, { createContext, useContext } from "react";

/* THE text look (Alfonso, 2026-11-23, Director answer 24). Replaces gold everywhere.
   Pure white text, no colour, no stroke / outline, no box / background bar. Under the sharp text, bottom to top:
   dark shadow (black, blur 40, 35 %) -> wide glow (white, blur 22, 45 %) -> tight glow (white, blur 6, 80 %).
   The numbers come from config.yaml `text_look:` via props.textLook (render_final.py injects them); the defaults
   below are the same numbers, used only for the Remotion Studio demo. CSS blur(N) = gaussian sigma N px, the same
   as PIL GaussianBlur(N) in scripts/text_look.py. */
export type LookLayer = { name: string; color: string; blur: number; opacity: number };
export type TextLook = { color: string; layers: LookLayer[] };

export const DEFAULT_LOOK: TextLook = {
  color: "#FFFFFF",
  layers: [
    { name: "shadow", color: "#000000", blur: 40, opacity: 0.35 },
    { name: "wide_glow", color: "#FFFFFF", blur: 22, opacity: 0.45 },
    { name: "tight_glow", color: "#FFFFFF", blur: 6, opacity: 0.8 },
  ],
};

const LookCtx = createContext<TextLook>(DEFAULT_LOOK);
export const LookProvider = LookCtx.Provider;
export const useLook = () => useContext(LookCtx);

/** Text (or an SVG drawn with currentColor) in the look: the children are drawn once per layer, stacked.
 *  Put every typography style on `style` (the copies inherit it), never a colour on the children
 *  (use `currentColor` / inherit). `dim` = 0..1 opacity of the whole stack (e.g. a "not yet" checklist row). */
export const Glow: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
  boost?: number; // > 0 brightens the two glows (e.g. a beat pulse)
}> = ({ children, style, boost = 0 }) => {
  const look = useLook();
  return (
    <div style={{ position: "relative", ...style, color: look.color }}>
      {look.layers.map((l) => (
        <div
          key={l.name}
          aria-hidden
          style={{
            position: "absolute",
            inset: 0,
            color: l.color,
            filter: `blur(${l.blur}px)`,
            opacity: Math.min(1, l.name === "shadow" ? l.opacity : l.opacity * (1 + boost)),
            pointerEvents: "none",
          }}
        >
          {children}
        </div>
      ))}
      <div style={{ position: "relative", color: look.color }}>{children}</div>
    </div>
  );
};
