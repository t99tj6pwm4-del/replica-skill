import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { BODY, DISPLAY, useFonts } from "./fonts";
import { DEFAULT_LOOK, Glow, LookProvider } from "./look";
import { CarouselSlideLegacy } from "./CarouselLegacy";
import type { CarouselProps } from "./types";

const pad = (n: number) => String(n).padStart(2, "0");

// One still per slide: a cover, then one slide per exercise with sets x reps.
// Since 2026-11-23 (Director answer 24): every text white in the glow look, no chip box, no accent bar.
export const CarouselSlide: React.FC<CarouselProps> = (p) =>
  p.textLook ? <CarouselWhite {...p} /> : <CarouselSlideLegacy {...p} />;

const CarouselWhite: React.FC<CarouselProps> = ({ brand, slide, textLook }) => {
  useFonts();
  const cover = slide.kind === "cover";
  const words = slide.title.split(/\s+/).filter(Boolean);
  const longest = Math.max(...words.map((w) => w.length), 1);
  const size = Math.min(cover ? 230 : 190, Math.floor(940 / (longest * 0.47)));
  return (
    <LookProvider value={textLook ?? DEFAULT_LOOK}>
    <AbsoluteFill style={{ backgroundColor: brand.darkColor }}>
      {slide.image ? (
        <Img
          src={staticFile(slide.image)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      ) : null}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(11,11,15,0.55) 0%, rgba(11,11,15,0.15) 35%, rgba(11,11,15,0.92) 78%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 64,
          left: 64,
          right: 64,
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 34, letterSpacing: 3 }}>{brand.handle}</Glow>
        <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 34, letterSpacing: 3 }}>
          {cover ? "SWIPE >>" : `${pad(slide.index)} / ${pad(slide.total)}`}
        </Glow>
      </div>
      <div style={{ position: "absolute", left: 64, right: 64, bottom: 90 }}>
        {words.map((w, i) => (
          <Glow key={i} style={{ fontFamily: DISPLAY, fontSize: size, lineHeight: 1.04, letterSpacing: 2 }}>
            {w}
          </Glow>
        ))}
        {slide.detail ? (
          <Glow style={{ marginTop: 30, fontFamily: BODY, fontWeight: 800, fontSize: 64 }}>{slide.detail}</Glow>
        ) : null}
        {slide.cue ? (
          <Glow style={{ marginTop: 28, fontFamily: BODY, fontWeight: 700, fontSize: 46, lineHeight: 1.25 }}>
            {slide.cue}
          </Glow>
        ) : null}
      </div>
    </AbsoluteFill>
    </LookProvider>
  );
};
