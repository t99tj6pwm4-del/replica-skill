import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { BODY, DISPLAY, loadFonts } from "./fonts";
import type { CarouselProps } from "./types";

loadFonts();

const pad = (n: number) => String(n).padStart(2, "0");

// One still per slide: a cover, then one slide per exercise with sets x reps.
export const CarouselSlide: React.FC<CarouselProps> = ({ brand, slide }) => {
  const cover = slide.kind === "cover";
  const words = slide.title.split(/\s+/).filter(Boolean);
  const longest = Math.max(...words.map((w) => w.length), 1);
  const size = Math.min(cover ? 230 : 190, Math.floor(940 / (longest * 0.47)));
  return (
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
          fontFamily: BODY,
          fontWeight: 800,
          fontSize: 34,
          letterSpacing: 3,
          color: brand.textColor,
        }}
      >
        <span>{brand.handle}</span>
        <span style={{ color: brand.color }}>
          {cover ? "SWIPE >>" : `${pad(slide.index)} / ${pad(slide.total)}`}
        </span>
      </div>
      <div style={{ position: "absolute", left: 64, right: 64, bottom: 90 }}>
        <div style={{ width: 150, height: 16, backgroundColor: brand.color, marginBottom: 26 }} />
        {words.map((w, i) => (
          <div
            key={i}
            style={{
              fontFamily: DISPLAY,
              fontSize: size,
              lineHeight: 1.04,
              letterSpacing: 2,
              color: cover && i === words.length - 1 ? brand.color : brand.textColor,
            }}
          >
            {w}
          </div>
        ))}
        {slide.detail ? (
          <div
            style={{
              display: "inline-block",
              marginTop: 30,
              padding: "12px 30px",
              borderRadius: 12,
              backgroundColor: brand.color,
              color: brand.darkColor,
              fontFamily: BODY,
              fontWeight: 800,
              fontSize: 64,
            }}
          >
            {slide.detail}
          </div>
        ) : null}
        {slide.cue ? (
          <div
            style={{
              marginTop: 28,
              fontFamily: BODY,
              fontWeight: 700,
              fontSize: 46,
              lineHeight: 1.25,
              color: brand.textColor,
            }}
          >
            {slide.cue}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
