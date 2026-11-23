import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BODY, DISPLAY, MONTSERRAT, WEIGHT, useFonts } from "./fonts";
import { DEFAULT_LOOK, Glow, LookProvider } from "./look";
import { OverlayLegacy } from "./OverlayLegacy";
import type {
  Brand,
  Callout,
  CaptionPage,
  ChecklistPopup,
  ExerciseBarPopup,
  FormTipPopup,
  ListCardItem,
  LowerThird,
  OverlayProps,
  ProgressSegment,
  TimedEvent,
} from "./types";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};
/* Alfonso 2026-11-23 (Director answer 24): every text is pure white in the text look (./look.tsx <Glow>: soft dark
   shadow -> wide white glow -> tight white glow -> sharp white). No gold, no colour, no stroke / outline, no card box,
   no background bar, no panel. Numbers from config.yaml text_look via props.textLook. */

/* ------------------------------------------------------------------ */
/* Title card: words slam in one by one over moving brand stripes      */
/* ------------------------------------------------------------------ */
const TitleCard: React.FC<{
  text: string;
  subtitle?: string;
  brand: Brand;
  frames: number;
  animation?: string;
  offsetY?: number;
  gold?: boolean;
  stagger?: number;
}> = ({ text, subtitle, brand, frames, animation, offsetY = 0, gold = false, stagger = 4 }) => {
  const frame = useCurrentFrame();
  // CapCut library Animation > In for the hook: Flash In / Fade In / Zoom 1 / Focus
  const inFlash = animation === "Flash In" ? interpolate(frame, [0, 2, 6], [0, 0.9, 0], clamp) : 0;
  const inFade = animation === "Fade In" ? interpolate(frame, [0, 8], [0, 1], clamp) : 1;
  const inZoom = animation === "Zoom 1" ? interpolate(frame, [0, 10], [1.25, 1], { ...clamp, easing: Easing.out(Easing.cubic) }) : 1;
  const inBlur = animation === "Focus" ? interpolate(frame, [0, 10], [18, 0], clamp) : 0;
  const { fps, width } = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  // Keep the whole hook block in the left part of the frame so it never
  // covers the lifter's face (usually centre/right of a 9:16 gym shot).
  const TITLE_LEFT = 70;
  const TITLE_INDENT = 36;
  const TITLE_SAFE_RIGHT = Math.min(580, width - 70); // no letter right of this x
  const STRIPE_SAFE_RIGHT = Math.min(560, width - 70); // stripes end here
  const titleW = TITLE_SAFE_RIGHT - TITLE_LEFT;
  const size = Math.max(
    60,
    Math.min(
      250,
      ...words.map((w, i) =>
        Math.floor((titleW - i * TITLE_INDENT) / (Math.max(w.length, 1) * 0.76))
      )
    )
  );
  const exit = interpolate(frame, [frames - 7, frames], [0, 1], {
    ...clamp,
    easing: Easing.in(Easing.cubic),
  });
  const scrim = interpolate(frame, [0, 4, frames - 7, frames], [0, 0.62, 0.62, 0], clamp);
  const stripe = (delay: number) =>
    interpolate(frame - delay, [0, 12], [-120, 0], {
      ...clamp,
      easing: Easing.out(Easing.cubic),
    });

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: brand.darkColor, opacity: scrim }} />
      <AbsoluteFill
        style={{
          opacity: (1 - exit) * inFade,
          transform: `translateY(${-exit * 160}px) scale(${inZoom})`,
          filter: inBlur ? `blur(${inBlur}px)` : undefined,
        }}
      >
        {/* no brand stripes since 2026-11-23 (no bars): the words float in the white glow look */}
        <div
          style={{
            position: "absolute",
            top: 640 + offsetY,
            left: TITLE_LEFT,
            width: titleW,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            transform: "rotate(-7deg)",
            transformOrigin: "left top",
            // nothing of the title may cross the face-safe line, even mid-animation
            clipPath: "inset(-400px 0px -400px -400px)",
            // Flash In lights up the title only, never the whole frame
            filter: inFlash ? `brightness(${1 + 2.5 * inFlash})` : undefined,
          }}
        >
          {words.map((w, i) => {
            const s = spring({
              frame: frame - 2 - i * stagger,
              fps,
              config: { damping: 11, stiffness: 190, mass: 0.6 },
            });
            return (
              <div
                key={i}
                style={{
                  opacity: interpolate(s, [0, 0.3], [0, 1], clamp),
                  transform: `scale(${interpolate(s, [0, 1], [1.6, 1])})`,
                  transformOrigin: "left center",
                  marginLeft: i * TITLE_INDENT,
                }}
              >
                <Glow style={{ fontFamily: DISPLAY, fontSize: size, lineHeight: 1.02, letterSpacing: 2, whiteSpace: "nowrap" }}>
                  {w}
                </Glow>
              </div>
            );
          })}
          {subtitle ? (
            <div
              style={{
                marginTop: 34,
                marginLeft: Math.min(words.length * TITLE_INDENT, 120),
                // wraps inside the face-safe width instead of being clipped mid-word
                maxWidth: titleW - Math.min(words.length * TITLE_INDENT, 120),
                boxSizing: "border-box",
                transform: `translateY(${interpolate(
                  spring({ frame: frame - 6 - words.length * stagger, fps, config: { damping: 14 } }),
                  [0, 1],
                  [70, 0]
                )}px)`,
                opacity: interpolate(frame - 6 - words.length * stagger, [0, 5], [0, 1], clamp),
              }}
            >
              <Glow style={{ whiteSpace: "normal", lineHeight: 1.15, fontFamily: BODY, fontWeight: 800, fontSize: 46,
                textTransform: "uppercase", letterSpacing: 1 }}>
                {subtitle}
              </Glow>
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Lower third: bar grows, panel wipes, name slides, sets chip pops    */
/* ------------------------------------------------------------------ */
const LowerThirdCard: React.FC<{
  item: LowerThird;
  brand: Brand;
  frames: number;
  y: number;
}> = ({ item, brand, frames, y }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = interpolate(frame, [frames - 9, frames], [0, 1], {
    ...clamp,
    easing: Easing.in(Easing.cubic),
  });
  const bar = spring({ frame, fps, config: { damping: 16, stiffness: 160 } });
  const panel = interpolate(frame, [3, 13], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const name = interpolate(frame, [7, 17], [-60, 0], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const chip = spring({
    frame: frame - 15,
    fps,
    config: { damping: 9, stiffness: 200, mass: 0.6 },
  });
  const pad = (n: number) => String(n).padStart(2, "0");

  return (
    <div
      style={{
        position: "absolute",
        left: 56,
        top: y,
        display: "flex",
        alignItems: "stretch",
        transform: `translateX(${-out * 900}px)`,
        opacity: 1 - out,
      }}
    >
      {/* no accent bar, no dark panel since 2026-11-23: the lines float in the white glow look */}
      <div style={{ opacity: Math.min(bar, panel) > 0 ? 1 : 0 }}>
        <Glow
          style={{
            fontFamily: BODY,
            fontWeight: 700,
            fontSize: 28,
            letterSpacing: 5,
            opacity: interpolate(frame, [9, 16], [0, 1], clamp),
          }}
        >
          {`EXERCISE ${pad(item.index)} / ${pad(item.total)}`}
        </Glow>
        <div style={{ display: "flex", alignItems: "center", gap: 24, marginTop: 4 }}>
          <div
            style={{
              transform: `translateX(${name}px)`,
              opacity: interpolate(frame, [7, 13], [0, 1], clamp),
              maxWidth: 820,
            }}
          >
            <Glow
              style={{
                fontFamily: DISPLAY,
                fontSize: 88,
                lineHeight: 1.08,
                letterSpacing: 1.5,
                // long exercise names wrap onto two lines instead of running off the frame
                whiteSpace: item.title.length > 22 ? "normal" : "nowrap",
              }}
            >
              {item.title}
            </Glow>
          </div>
          {item.detail ? (
            <div style={{ transform: `scale(${chip})` }}>
              <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 46, whiteSpace: "nowrap" }}>
                {item.detail}
              </Glow>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

/* Brand-colour wipe that sweeps the frame when a new exercise starts */
const SegmentWipe: React.FC<{ brand: Brand }> = ({ brand }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const x = interpolate(frame, [0, 11], [-1.4, 1.4], {
    ...clamp,
    easing: Easing.inOut(Easing.cubic),
  });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {[0, 1].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: -200,
            bottom: -200,
            width: i === 0 ? 300 : 70,
            left: width / 2 - 150 - i * 240,
            backgroundColor: i === 0 ? brand.textColor : brand.textColor,
            opacity: i === 0 ? 0.92 : 0.8,
            transform: `translateX(${x * width}px) skewX(-18deg)`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Segmented progress bar (top)                                        */
/* ------------------------------------------------------------------ */
const ProgressBar: React.FC<{ segments: ProgressSegment[]; brand: Brand; showLabel?: boolean; top?: number }> = ({
  segments,
  brand,
  showLabel = true,
  top = 118,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (!segments.length) return null;
  const total = segments[segments.length - 1].to - segments[0].from;
  const current = segments.find((s) => t >= s.from && t < s.to) ?? segments[segments.length - 1];
  const appear = interpolate(frame, [0, 10], [0, 1], clamp);
  // Alfonso 2026-11-23: the progress bar is a THIN WHITE LINE in the same glow look (no grey track box, no colour):
  // the done part is solid white 4 px, the part still to come a 2 px white hairline at 35 %; gaps between segments.
  return (
    <div style={{ position: "absolute", top, left: 56, right: 56, opacity: appear }}>
      <Glow style={{ height: 12 }}>
        <div style={{ display: "flex", gap: 10, height: 12, alignItems: "center" }}>
          {segments.map((s, i) => {
            const fill = interpolate(t, [s.from, s.to], [0, 100], clamp);
            return (
              <div key={i} style={{ flex: (s.to - s.from) / total, position: "relative", height: 4 }}>
                <div style={{ position: "absolute", left: 0, right: 0, top: 1, height: 2, backgroundColor: "currentColor",
                  opacity: 0.35 }} />
                <div style={{ position: "absolute", left: 0, top: 0, height: 4, width: `${fill}%`,
                  backgroundColor: "currentColor", borderRadius: 2 }} />
              </div>
            );
          })}
        </div>
      </Glow>
      {showLabel ? (
        <Glow style={{ marginTop: 12, fontFamily: BODY, fontWeight: 800, fontSize: 28, letterSpacing: 3,
          textTransform: "uppercase" }}>
          {current.label}
        </Glow>
      ) : null}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Word-by-word captions: each word pops in as it is said              */
/* ------------------------------------------------------------------ */
const Captions: React.FC<{ pages: CaptionPage[]; brand: Brand; y: number }> = ({
  pages,
  brand,
  y,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const page = pages.find((p) => t >= p.start - 0.02 && t < p.end);
  if (!page) return null;
  const chars = page.words.reduce((n, w) => n + w.text.length + 1, 0);
  const size = chars > 22 ? 78 : chars > 16 ? 92 : 108;
  return (
    <div
      style={{
        position: "absolute",
        left: 50,
        right: 50,
        top: y - size * 0.75,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexWrap: "wrap",
        columnGap: size * 0.34,
      }}
    >
      {page.words.map((w, i) => {
        const startFrame = Math.round(w.start * fps);
        const s = spring({
          frame: frame - startFrame,
          fps,
          config: { damping: 10, stiffness: 260, mass: 0.5 },
        });
        const said = frame >= startFrame;
        const active = t >= w.start && t < w.end + 0.06;
        // pop from the word's own centre and never past full size, so a word never reaches its neighbour
        const scale = Math.min(1, interpolate(s, [0, 1], [0.55, 1])) * (active ? 1.03 : 1);
        // white glow look: no stroke, no colour; a key word is a touch bigger with a brighter glow instead
        return (
          <div
            key={i}
            style={{
              display: "inline-block",
              opacity: said ? 1 : 0,
              transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px) scale(${scale * (w.highlight ? 1.08 : 1)}) rotate(${
                w.highlight && active ? -2 : 0
              }deg)`,
            }}
          >
            <Glow style={{ fontFamily: DISPLAY, fontSize: size, lineHeight: 1.16, letterSpacing: 1.5 }}
              boost={w.highlight ? 0.5 : 0}>
              {w.text}
            </Glow>
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Form-cue callout: ring draws on the body part, label pops           */
/* ------------------------------------------------------------------ */
const CalloutMark: React.FC<{ item: Callout; brand: Brand; frames: number }> = ({
  item,
  brand,
  frames,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const tNow = item.from + frame / fps;
  const tr = item.track && item.track.length > 1 ? item.track : null;
  const tx = tr
    ? interpolate(tNow, tr.map((k) => k.t), tr.map((k) => k.x), { ...clamp, easing: Easing.inOut(Easing.sin) })
    : item.x;
  const ty = tr
    ? interpolate(tNow, tr.map((k) => k.t), tr.map((k) => k.y), { ...clamp, easing: Easing.inOut(Easing.sin) })
    : item.y;
  const ax = item.x * width; // label anchor (static)
  const ay = item.y * height;
  const cx = tx * width; // ring centre (may track)
  const cy = ty * height;
  const r = 78;
  const circ = 2 * Math.PI * r;
  const draw = interpolate(frame, [0, 10], [circ, 0], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const pulse = 1 + 0.05 * Math.sin((frame / fps) * Math.PI * 3);
  const right = item.x < 0.5;
  const lx = right ? Math.min(ax + 150, width - 60) : Math.max(ax - 150, 60);
  const ly = Math.max(ay - 210, 330);
  const line = interpolate(frame, [7, 15], [0, 1], clamp);
  const pop = spring({ frame: frame - 12, fps, config: { damping: 10, stiffness: 220, mass: 0.6 } });
  const out = interpolate(frame, [frames - 6, frames], [1, 0], clamp);
  const sx = cx + (right ? 1 : -1) * r * 0.7;
  const sy = cy - r * 0.7;
  return (
    <AbsoluteFill style={{ opacity: out }}>
      {/* ring + leader line: white in the same glow look (no dark under-stroke, no colour) */}
      <Glow style={{ position: "absolute", left: 0, top: 0, width, height }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={draw}
          transform={`rotate(-90 ${cx} ${cy}) translate(${cx} ${cy}) scale(${pulse}) translate(${-cx} ${-cy})`}
        />
        <line
          x1={sx}
          y1={sy}
          x2={sx + (lx - sx) * line}
          y2={sy + (ly + 40 - sy) * line}
          stroke="currentColor"
          strokeWidth={7}
          strokeLinecap="round"
        />
      </svg>
      </Glow>
      <div
        style={{
          position: "absolute",
          top: ly - 40,
          ...(right ? { left: lx - 20 } : { right: width - lx - 20 }),
          maxWidth: 560,
          transform: `scale(${pop})`,
          transformOrigin: right ? "left bottom" : "right bottom",
        }}
      >
        <Glow style={{ fontFamily: DISPLAY, fontSize: 60, lineHeight: 1.1, letterSpacing: 1 }}>{item.text}</Glow>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Edit accents: punch-in flash + viewfinder, slow-mo / speed badges   */
/* ------------------------------------------------------------------ */
const EventAccent: React.FC<{ ev: TimedEvent; brand: Brand; frames: number }> = ({
  ev,
  brand,
  frames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (ev.kind === "punch_in") {
    const flash = 0; // no unlisted flash: flashes only come from the effects library (effects_plan.json)
    const s = spring({ frame, fps, config: { damping: 12, stiffness: 240, mass: 0.5 } });
    const inset = interpolate(s, [0, 1], [10, 44]);
    const fade = interpolate(frame, [0, 3, frames - 5, frames], [0, 1, 1, 0], clamp);
    const corner = (pos: React.CSSProperties, bt: string, bs: string): React.ReactNode => (
      <div
        style={{
          position: "absolute",
          width: 90,
          height: 90,
          ...pos,
          [bt]: `10px solid ${brand.textColor}`,
          [bs]: `10px solid ${brand.textColor}`,
          filter: "drop-shadow(0 0 6px rgba(255,255,255,0.8)) drop-shadow(0 0 40px rgba(0,0,0,0.35))",
        }}
      />
    );
    return (
      <AbsoluteFill>
        <AbsoluteFill style={{ backgroundColor: "#fff", opacity: flash }} />
        <AbsoluteFill style={{ opacity: fade }}>
          {corner({ top: 250 + inset, left: inset }, "borderTop", "borderLeft")}
          {corner({ top: 250 + inset, right: inset }, "borderTop", "borderRight")}
          {corner({ bottom: 330 + inset, left: inset }, "borderBottom", "borderLeft")}
          {corner({ bottom: 330 + inset, right: inset }, "borderBottom", "borderRight")}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  const slow = ev.kind === "slow_mo";
  if (ev.kind === "cam") {
    // angle change: one-frame flash on the hard cut, then a small camera tag that fades after 1.6s
    const tag = interpolate(frame, [0, 4, 44, 52], [0, 1, 1, 0], clamp);
    return (
      <AbsoluteFill>
        <AbsoluteFill style={{ backgroundColor: "#fff", opacity: interpolate(frame, [0, 4], [0.35, 0], clamp) }} />
        {/* the white flash stays; the tag floats in the white glow look (no box, no border, white dot) */}
        <div style={{ position: "absolute", top: ev.y ?? 232, left: ev.x ?? 56, opacity: tag }}>
          <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 30, letterSpacing: 3, whiteSpace: "nowrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: "currentColor" }} />
              {ev.label ?? "CAM 2"}
            </div>
          </Glow>
        </div>
      </AbsoluteFill>
    );
  }
  const pop = spring({ frame, fps, config: { damping: 11, stiffness: 220, mass: 0.6 } });
  const out = interpolate(frame, [frames - 6, frames], [1, 0], clamp);
  const blink = Math.sin((frame / fps) * Math.PI * 4) > 0 ? 1 : 0.25;
  return (
    <AbsoluteFill style={{ opacity: out }}>
      {slow ? (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.5) 100%)",
            opacity: interpolate(frame, [0, 8], [0, 1], clamp),
          }}
        />
      ) : null}
      <div style={{ position: "absolute", top: ev.y ?? 232, right: 56, transform: `scale(${pop})`, transformOrigin: "right center" }}>
        <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 34, letterSpacing: 3, whiteSpace: "nowrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            {slow ? (
              <div style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: "currentColor", opacity: blink }} />
            ) : (
              <span style={{ display: "inline-block", transform: `translateX(${(frame % 10) - 5}px)` }}>{">>"}</span>
            )}
            {ev.label ?? (slow ? "SLOW-MO" : "FAST")}
          </div>
        </Glow>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* End card: bookmark fills with brand colour, "SAVE THIS" slams in    */
/* ------------------------------------------------------------------ */
const EndCard: React.FC<{
  text: string;
  subtitle?: string;
  brand: Brand;
}> = ({ text, subtitle, brand }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scrim = interpolate(frame, [0, 8], [0, 0.78], clamp);
  const icon = spring({ frame: frame - 3, fps, config: { damping: 8, stiffness: 170, mass: 0.7 } });
  const fill = interpolate(frame, [14, 26], [0, 100], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const ring = interpolate((frame - 26) % 30, [0, 30], [0, 1], clamp);
  const words = text.split(/\s+/).filter(Boolean);
  const bob = Math.sin((frame / fps) * Math.PI * 2) * 8;
  const BM = "M40 20 h160 a16 16 0 0 1 16 16 v236 l-96 -62 l-96 62 v-236 a16 16 0 0 1 16 -16 z";
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: brand.darkColor, opacity: scrim }} />
      <AbsoluteFill style={{ alignItems: "center" }}>
        <div
          style={{
            marginTop: 470,
            width: 240,
            height: 300,
            position: "relative",
            transform: `translateY(${bob}px) scale(${icon})`,
          }}
        >
          {frame > 26 ? (
            <div
              style={{
                position: "absolute",
                left: -60,
                top: -30,
                width: 360,
                height: 360,
                borderRadius: 180,
                border: `8px solid ${brand.textColor}`,
                opacity: 0.7 * (1 - ring),
                transform: `scale(${0.7 + ring * 0.6})`,
              }}
            />
          ) : null}
          <svg width={240} height={300} viewBox="0 0 240 300" style={{ position: "absolute" }}>
            <defs>
              <clipPath id="bmfill">
                <rect x="0" y={300 - fill * 3} width="240" height={fill * 3} />
              </clipPath>
            </defs>
            <path d={BM} fill="none" stroke={brand.textColor} strokeWidth={14} strokeLinejoin="round" />
            <path d={BM} fill={brand.textColor} stroke={brand.textColor} strokeWidth={14} strokeLinejoin="round" clipPath="url(#bmfill)" />
          </svg>
        </div>
        <div style={{ display: "flex", gap: 34, marginTop: 70 }}>
          {words.map((w, i) => {
            const s = spring({
              frame: frame - 10 - i * 5,
              fps,
              config: { damping: 10, stiffness: 200, mass: 0.6 },
            });
            return (
              <div
                key={i}
                style={{
                  opacity: interpolate(s, [0, 0.3], [0, 1], clamp),
                  transform: `scale(${interpolate(s, [0, 1], [2.2, 1])})`,
                }}
              >
                <Glow style={{ fontFamily: DISPLAY, fontSize: Math.min(210, Math.floor(1500 / Math.max(text.length, 6))),
                  lineHeight: 1.05, letterSpacing: 2 }}>
                  {w}
                </Glow>
              </div>
            );
          })}
        </div>
        {subtitle ? (
          <div
            style={{
              marginTop: 26,
              opacity: interpolate(frame, [24, 32], [0, 1], clamp),
              transform: `translateY(${interpolate(frame, [24, 32], [30, 0], clamp)}px)`,
            }}
          >
            <Glow style={{ fontFamily: BODY, fontWeight: 700, fontSize: 48, textTransform: "uppercase", letterSpacing: 2 }}>
              {subtitle}
            </Glow>
          </div>
        ) : null}
        <div
          style={{
            marginTop: 54,
            transform: `scale(${spring({
              frame: frame - 30,
              fps,
              config: { damping: 10, stiffness: 200, mass: 0.6 },
            })})`,
          }}
        >
          <Glow style={{ fontFamily: BODY, fontWeight: 800, fontSize: 44 }}>{brand.handle}</Glow>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* List card: header slides in, then each item ticks in one by one     */
/* ------------------------------------------------------------------ */
const ListCard: React.FC<{ item: ListCardItem; brand: Brand; frames: number }> = ({ item, brand, frames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = interpolate(frame, [frames - 8, frames], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const head = interpolate(frame, [0, 9], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const n = item.items.length;
  // spread the items over the first ~45% of the card so they are all up for most of it
  const step = Math.max(6, Math.floor((frames * 0.45) / Math.max(1, n)));
  if (item.compact) {
    // two-line strip: header pill, then all items in one row (fits below a close-up face)
    return (
      <div style={{ position: "absolute", left: 56, right: 56, top: item.y, opacity: 1 - out, transform: `translateX(${-out * 600}px)` }}>
        <div style={{ display: "inline-block", opacity: head, transform: `translateX(${(1 - head) * -40}px)` }}>
          <Glow style={{ fontFamily: DISPLAY, fontSize: 50, lineHeight: 1.05, letterSpacing: 2 }}>{item.title}</Glow>
        </div>
        <div style={{ display: "flex", flexWrap: "nowrap", gap: 10, marginTop: 8 }}>
          {item.items.map((t, i) => {
            const start = 8 + i * step;
            const s = spring({ frame: frame - start, fps, config: { damping: 11, stiffness: 210, mass: 0.6 } });
            const tick = interpolate(frame, [start + 3, start + 9], [0, 1], clamp);
            return (
              <div key={i} style={{ opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * 30}px)` }}>
                <Glow style={{ fontFamily: DISPLAY, fontSize: 38, lineHeight: 1.05, letterSpacing: 1, whiteSpace: "nowrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 12px 2px 6px" }}>
                    <svg width="28" height="28" viewBox="0 0 30 30">
                      <rect x="2" y="2" width="26" height="26" rx="5" fill="none" stroke="currentColor" strokeWidth="4" />
                      <path d="M8 16 L13 21 L23 9" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round"
                        strokeLinejoin="round" strokeDasharray="28" strokeDashoffset={28 * (1 - tick)} />
                    </svg>
                    <div>{t}</div>
                  </div>
                </Glow>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", left: 56, top: item.y, opacity: 1 - out, transform: `translateX(${-out * 600}px)` }}>
      <div style={{ display: "inline-block", opacity: head, transform: `translateX(${(1 - head) * -40}px)` }}>
        <Glow style={{ fontFamily: DISPLAY, fontSize: 66, lineHeight: 1.05, letterSpacing: 2 }}>{item.title}</Glow>
      </div>
      <div style={{ marginTop: 10 }}>
        {item.items.map((t, i) => {
          const start = 8 + i * step;
          const s = spring({ frame: frame - start, fps, config: { damping: 11, stiffness: 210, mass: 0.6 } });
          const tick = interpolate(frame, [start + 3, start + 9], [0, 1], clamp);
          return (
            <div
              key={i}
              style={{ marginTop: 5, opacity: Math.min(1, s * 1.4), transform: `translateX(${(1 - s) * -80}px)` }}
            >
              <Glow style={{ fontFamily: DISPLAY, fontSize: 54, lineHeight: 1.05, letterSpacing: 1.5 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 8, border: "5px solid currentColor", boxSizing: "border-box",
                    display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <svg width="26" height="26" viewBox="0 0 30 30">
                      <path d="M5 16 L12 23 L26 7" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round"
                        strokeLinejoin="round" strokeDasharray="34" strokeDashoffset={34 * (1 - tick)} />
                    </svg>
                  </div>
                  <div style={{ padding: "2px 0 0" }}>{t}</div>
                </div>
              </Glow>
            </div>
          );
        })}
      </div>
    </div>
  );
};


/* ------------------------------------------------------------------ */
/* Pop-up cards (Alfonso, 2026-11-17): exercise bar, form tip, routine */
/* checklist. Montserrat. Since 2026-11-23 (Director answer 24): NO    */
/* card box, no #333 panel, no gold: white text in the glow look.     */
/* ------------------------------------------------------------------ */

// quick pop-in (spring, ~0.2s) and quick pop-out (last ~0.17s)
const usePop = (frames: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14, stiffness: 320, mass: 0.5 }, durationInFrames: 6 });
  const out = interpolate(frame, [frames - 5, frames], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  return {
    opacity: Math.min(1, interpolate(frame, [0, 4], [0, 1], clamp)) * (1 - out),
    transform: `scale(${interpolate(s, [0, 1], [0.86, 1]) * interpolate(out, [0, 1], [1, 0.92])})`,
  };
};

const ExerciseBar: React.FC<{ item: ExerciseBarPopup; brand: Brand; frames: number }> = ({ item, frames }) => {
  const pop = usePop(frames);
  // long names ("SEATED DUMBBELL SHOULDER PRESS") shrink to fit the text width instead of being cut off
  const inner = 1080 - 2 * 54 - 2 * 44;
  const titleSize = Math.min(58, Math.floor(inner / (Math.max(1, item.title.length) * 0.8)));
  const detailSize = Math.min(38, Math.floor(inner / (Math.max(1, (item.detail || "").length) * 0.57)));
  return (
    <div
      style={{
        position: "absolute",
        left: 98,
        right: 98,
        top: item.y + 22,
        transformOrigin: "50% 100%",
        ...pop,
      }}
    >
      <Glow
        style={{
          fontFamily: MONTSERRAT,
          fontWeight: WEIGHT.extraBold,
          fontSize: titleSize,
          lineHeight: 1.12,
          letterSpacing: 1,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        {item.title}
      </Glow>
      {item.detail ? (
        <Glow
          style={{
            fontFamily: MONTSERRAT,
            fontWeight: WEIGHT.regular,
            fontSize: detailSize,
            lineHeight: 1.3,
            marginTop: 4,
            whiteSpace: "nowrap",
          }}
        >
          {item.detail}
        </Glow>
      ) : null}
    </div>
  );
};

const FormTipCard: React.FC<{ item: FormTipPopup; brand: Brand; frames: number }> = ({ item, frames }) => {
  const pop = usePop(frames);
  return (
    <div
      style={{
        position: "absolute",
        left: 108,
        right: 108,
        top: item.y + 36,
        transformOrigin: "50% 0%",
        ...pop,
      }}
    >
      <Glow style={{ fontFamily: MONTSERRAT, fontWeight: WEIGHT.extraBold, fontSize: 46, lineHeight: 1.1, letterSpacing: 0.5 }}>
        FORM TIP
      </Glow>
      <Glow style={{ fontFamily: MONTSERRAT, fontWeight: WEIGHT.bold, fontSize: 62, lineHeight: 1.2, marginTop: 14, maxWidth: 680 }}>
        {item.cue}
      </Glow>
      {item.cueEs ? (
        <Glow style={{ fontFamily: MONTSERRAT, fontWeight: WEIGHT.regular, fontSize: 36, lineHeight: 1.3, marginTop: 16 }}>
          {item.cueEs}
        </Glow>
      ) : null}
    </div>
  );
};

const RoutineChecklist: React.FC<{ item: ChecklistPopup; brand: Brand; frames: number }> = ({ item, frames }) => {
  const pop = usePop(frames);
  const n = item.items.length;
  const tight = n > 6; // long routines: smaller rows so the list still fits on the left
  const fs = tight ? 30 : 34;
  const pitch = tight ? 52 : 62;
  // all white (no gold / grey): done = white check, current = arrow + bold + a touch bigger, still to come = dot
  return (
    <div
      style={{
        position: "absolute",
        left: 100,
        top: item.y + 40,
        minWidth: 468,
        maxWidth: 668,
        transformOrigin: "0% 50%",
        ...pop,
      }}
    >
      <Glow style={{ fontFamily: MONTSERRAT, fontWeight: WEIGHT.extraBold, fontSize: 38, lineHeight: 1.1, marginBottom: 14,
        whiteSpace: "nowrap" }}>
        TODAY'S ROUTINE
      </Glow>
      {item.items.map((name, i) => {
        const done = i < item.current;
        const cur = i === item.current;
        return (
          <Glow key={i} style={{ height: pitch }}>
            <div style={{ display: "flex", alignItems: "center", height: pitch }}>
              <div style={{ width: 56, flexShrink: 0, display: "flex", alignItems: "center" }}>
                {done ? (
                  <svg width="44" height="36" viewBox="0 0 44 36">
                    <path d="M3 18 L15 30 L41 4" fill="none" stroke="currentColor" strokeWidth="4.5" strokeLinecap="round"
                      strokeLinejoin="round" />
                  </svg>
                ) : (
                  <span
                    style={{
                      fontFamily: MONTSERRAT,
                      fontWeight: cur ? WEIGHT.extraBold : WEIGHT.bold,
                      fontSize: cur ? 34 : 44,
                      lineHeight: 1,
                      paddingLeft: cur ? 0 : 6,
                    }}
                  >
                    {cur ? "→" : "•"}
                  </span>
                )}
              </div>
              <div
                style={{
                  fontFamily: MONTSERRAT,
                  fontWeight: cur ? WEIGHT.extraBold : WEIGHT.regular,
                  fontSize: cur ? fs + 4 : fs,
                  lineHeight: 1.1,
                  whiteSpace: "nowrap",
                }}
              >
                {name}
              </div>
            </div>
          </Glow>
        );
      })}
      <Glow style={{ fontFamily: MONTSERRAT, fontWeight: WEIGHT.bold, fontSize: 32, lineHeight: 1.1, marginTop: 30,
        letterSpacing: 0.5 }}>
        {`${item.current} OF ${n} DONE`}
      </Glow>
    </div>
  );
};

/* ------------------------------------------------------------------ */
export const Overlay: React.FC<OverlayProps> = (p) =>
  // white glow look only when render_final.py passed props.textLook (config text_look.enabled / --text-look white);
  // otherwise the shipped gold look, unchanged
  p.textLook ? <OverlayWhite {...p} /> : <OverlayLegacy {...p} />;

const OverlayWhite: React.FC<OverlayProps> = (p) => {
  useFonts();
  const { fps } = useVideoConfig();
  const fr = (s: number) => Math.max(0, Math.round(s * fps));
  const seq = (from: number, to: number) => ({
    from: fr(from),
    durationInFrames: Math.max(1, fr(to) - fr(from)),
  });
  const end = p.endCard ? p.endCard.from : p.duration;
  const titleEnd = p.title ? p.title.to : 0;
  const tNow = useCurrentFrame() / fps;
  const textHidden = (p.noTextWindows ?? []).some((w) => tNow >= w.from && tNow < w.to);
  const pops = p.popups;
  // the exercise bar carries the same name + sets x reps: no lower-third on top of it
  const lowerThirds = pops?.bars?.length
    ? p.lowerThirds.filter((lt) => !pops.bars.some((b) => lt.from < b.to && b.from < lt.to))
    : p.lowerThirds;
  return (
    <LookProvider value={p.textLook ?? DEFAULT_LOOK}>
    <AbsoluteFill>
     <AbsoluteFill style={{ opacity: textHidden ? 0 : 1 }}>
      {/* accents sit under the text layers */}
      {p.events.map((ev, i) => {
        const s = seq(ev.from, ev.to);
        return (
          <Sequence key={`e${i}`} {...s}>
            <EventAccent ev={ev} brand={p.brand} frames={s.durationInFrames} />
          </Sequence>
        );
      })}
      {/* no built-in wipe: transitions come only from the effects library (effects_plan.json) */}
      {p.callouts.map((c, i) => {
        const s = seq(c.from, c.to);
        return (
          <Sequence key={`c${i}`} {...s}>
            <CalloutMark item={c} brand={p.brand} frames={s.durationInFrames} />
          </Sequence>
        );
      })}
      {lowerThirds.map((lt, i) => {
        const s = seq(lt.from, lt.to);
        return (
          <Sequence key={`l${i}`} {...s}>
            <LowerThirdCard item={lt} brand={p.brand} frames={s.durationInFrames} y={p.layout.lowerThirdY} />
          </Sequence>
        );
      })}
      {(p.lists ?? []).map((li, i) => {
        const s = seq(li.from, li.to);
        return (
          <Sequence key={`li${i}`} {...s}>
            <ListCard item={li} brand={p.brand} frames={s.durationInFrames} />
          </Sequence>
        );
      })}
      <Sequence from={fr(titleEnd)} durationInFrames={Math.max(1, fr(end) - fr(titleEnd))}>
        <Captions
          pages={p.captions.map((c) => ({
            start: c.start - titleEnd,
            end: c.end - titleEnd,
            words: c.words.map((w) => ({ ...w, start: w.start - titleEnd, end: w.end - titleEnd })),
          }))}
          brand={p.brand}
          y={p.layout.captionY}
        />
      </Sequence>
      {/* pop-up cards sit over the captions' layer but stay separate from them */}
      {(pops?.bars ?? []).map((b, i) => {
        const s = seq(b.from, b.to);
        return (
          <Sequence key={`pb${i}`} {...s}>
            <ExerciseBar item={b} brand={p.brand} frames={s.durationInFrames} />
          </Sequence>
        );
      })}
      {(pops?.checklists ?? []).map((c, i) => {
        const s = seq(c.from, c.to);
        return (
          <Sequence key={`pc${i}`} {...s}>
            <RoutineChecklist item={c} brand={p.brand} frames={s.durationInFrames} />
          </Sequence>
        );
      })}
      {pops?.formTip ? (
        <Sequence {...seq(pops.formTip.from, pops.formTip.to)}>
          <FormTipCard item={pops.formTip} brand={p.brand} frames={seq(pops.formTip.from, pops.formTip.to).durationInFrames} />
        </Sequence>
      ) : null}
      {/* style "fonzi_intro": the intro card is baked into the picture after the render (finish_fx.py ->
          style_fx.py intro); Remotion draws no hook TitleCard for it */}
      {p.title && p.title.style !== "fonzi_intro" ? (
        <Sequence {...seq(p.title.from, p.title.to)}>
          <TitleCard
            text={p.title.text}
            subtitle={p.title.subtitle}
            brand={p.brand}
            frames={seq(p.title.from, p.title.to).durationInFrames}
            animation={p.title.animation}
            offsetY={p.layout.titleOffsetY ?? 0}
            gold={p.title.gold}
            stagger={p.title.stagger}
          />
        </Sequence>
      ) : null}
     </AbsoluteFill>
      <Sequence from={0} durationInFrames={Math.max(1, fr(end))}>
        <ProgressBar segments={p.progress} brand={p.brand} showLabel={p.progressLabels !== false && !textHidden} top={p.layout.progressY ?? 118} />
      </Sequence>
      {p.endCard && p.endCard.style !== "logo_drip" ? (
        <Sequence {...seq(p.endCard.from, p.endCard.to)}>
          <EndCard text={p.endCard.text} subtitle={p.endCard.subtitle} brand={p.brand} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
    </LookProvider>
  );
};
