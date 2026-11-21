import React from "react";
import { Composition } from "remotion";
import { Overlay } from "./Overlay";
import { CarouselSlide } from "./Carousel";
import type { CarouselProps, OverlayProps } from "./types";

const brand = {
  name: "Fonzi Stays Fit",
  handle: "@fonzi.stays.fit",
  color: "#FFD60A",
  textColor: "#FFFFFF",
  darkColor: "#0B0B0F",
};

// Preview data only. Real renders pass --props=output/work/overlay_props.json
const demo: OverlayProps = {
  fps: 30,
  width: 1080,
  height: 1920,
  duration: 12,
  brand,
  layout: { captionY: 1400, lowerThirdY: 1090 },
  title: { from: 0, to: 2, text: "FRIDAY FORM FIX", subtitle: "2 lifts. 2 fixes." },
  lowerThirds: [
    { from: 2.3, to: 6.5, title: "BENCH PRESS", detail: "4 x 10", index: 1, total: 2 },
  ],
  progress: [
    { from: 0, to: 2, label: "Hook" },
    { from: 2, to: 9.5, label: "Bench Press" },
    { from: 9.5, to: 12, label: "Save" },
  ],
  captions: [
    {
      start: 2.4,
      end: 3.6,
      words: [
        { text: "KEEP", start: 2.4, end: 2.7 },
        { text: "YOUR", start: 2.7, end: 3.0 },
        { text: "ELBOWS", start: 3.0, end: 3.6, highlight: true },
      ],
    },
  ],
  callouts: [{ from: 4, to: 6.5, text: "ELBOWS TUCKED", x: 0.4, y: 0.45 }],
  events: [
    { from: 5, to: 6.5, kind: "punch_in" },
    { from: 7, to: 9, kind: "slow_mo", label: "SLOW-MO 0.5x" },
  ],
  endCard: { from: 9.5, to: 12, text: "SAVE THIS", subtitle: "for your next gym day" },
};

const demoSlide: CarouselProps = {
  brand,
  slide: { kind: "exercise", title: "BENCH PRESS", detail: "4 x 10", cue: "Elbows tucked", index: 1, total: 2 },
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Overlay"
        component={Overlay as unknown as React.FC<Record<string, unknown>>}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={360}
        defaultProps={demo as unknown as Record<string, unknown>}
        calculateMetadata={({ props }) => {
          const p = props as unknown as OverlayProps;
          return {
            durationInFrames: Math.max(1, Math.round(p.duration * p.fps)),
            fps: p.fps,
            width: p.width,
            height: p.height,
          };
        }}
      />
      <Composition
        id="CarouselSlide"
        component={CarouselSlide as unknown as React.FC<Record<string, unknown>>}
        width={1080}
        height={1350}
        fps={30}
        durationInFrames={1}
        defaultProps={demoSlide as unknown as Record<string, unknown>}
      />
    </>
  );
};
