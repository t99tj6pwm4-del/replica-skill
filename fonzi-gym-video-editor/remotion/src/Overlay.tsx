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
import { BODY, DISPLAY, useFonts } from "./fonts";
import type {
  Brand,
  Callout,
  CaptionPage,
  LowerThird,
  OverlayProps,
  ProgressSegment,
  TimedEvent,
} from "./types";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};
const SHADOW = "0 6px 24px rgba(0,0,0,0.55)";

/* ------------------------------------------------------------------ */
/* Title card: words slam in one by one over moving brand stripes      */
/* ------------------------------------------------------------------ */
const TitleCard: React.FC<{
  text: string;
  subtitle?: string;
  brand: Brand;
  frames: number;
  animation?: string;
}> = ({ text, subtitle, brand, frames, animation }) => {
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
        Math.floor((titleW - i * TITLE_INDENT) / (Math.max(w.length, 1) * 0.56))
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
        {/* diagonal brand stripes */}
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: -200,
              width: STRIPE_SAFE_RIGHT + 200,
              top: 560 + i * 46,
              height: i === 0 ? 22 : 8,
              backgroundColor: brand.color,
              opacity: i === 0 ? 1 : 0.55,
              transform: `translateX(${stripe(i * 3)}%) rotate(-7deg)`,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            top: 640,
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
              frame: frame - 2 - i * 4,
              fps,
              config: { damping: 11, stiffness: 190, mass: 0.6 },
            });
            const last = i === words.length - 1;
            return (
              <div
                key={i}
                style={{
                  fontFamily: DISPLAY,
                  fontSize: size,
                  lineHeight: 1.02,
                  letterSpacing: 2,
                  color: last ? brand.color : brand.textColor,
                  textShadow: SHADOW,
                  opacity: interpolate(s, [0, 0.3], [0, 1], clamp),
                  transform: `scale(${interpolate(s, [0, 1], [1.6, 1])})`,
                  transformOrigin: "left center",
                  marginLeft: i * TITLE_INDENT,
                  whiteSpace: "nowrap",
                }}
              >
                {w}
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
                whiteSpace: "normal",
                lineHeight: 1.15,
                padding: "14px 30px",
                backgroundColor: brand.color,
                color: brand.darkColor,
                fontFamily: BODY,
                fontWeight: 800,
                fontSize: 46,
                textTransform: "uppercase",
                letterSpacing: 1,
                borderRadius: 10,
                transform: `translateY(${interpolate(
                  spring({ frame: frame - 6 - words.length * 4, fps, config: { damping: 14 } }),
                  [0, 1],
                  [70, 0]
                )}px)`,
                opacity: interpolate(frame - 6 - words.length * 4, [0, 5], [0, 1], clamp),
              }}
            >
              {subtitle}
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
      <div
        style={{
          width: 18,
          backgroundColor: brand.color,
          transform: `scaleY(${bar})`,
          transformOrigin: "bottom",
          borderRadius: 4,
        }}
      />
      <div
        style={{
          clipPath: `inset(0 ${100 - panel * 100}% 0 0)`,
          backgroundColor: "rgba(11,11,15,0.86)",
          padding: "18px 34px 22px 26px",
          borderRadius: "0 14px 14px 0",
        }}
      >
        <div
          style={{
            fontFamily: BODY,
            fontWeight: 700,
            fontSize: 28,
            letterSpacing: 5,
            color: brand.color,
            opacity: interpolate(frame, [9, 16], [0, 1], clamp),
          }}
        >
          {`EXERCISE ${pad(item.index)} / ${pad(item.total)}`}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 24, marginTop: 4 }}>
          <div
            style={{
              fontFamily: DISPLAY,
              fontSize: 88,
              lineHeight: 1.08,
              color: brand.textColor,
              letterSpacing: 1.5,
              transform: `translateX(${name}px)`,
              opacity: interpolate(frame, [7, 13], [0, 1], clamp),
              // long exercise names wrap onto two lines instead of running off the frame
              whiteSpace: item.title.length > 22 ? "normal" : "nowrap",
              maxWidth: 820,
            }}
          >
            {item.title}
          </div>
          {item.detail ? (
            <div
              style={{
                fontFamily: BODY,
                fontWeight: 800,
                fontSize: 46,
                color: brand.darkColor,
                backgroundColor: brand.color,
                padding: "8px 22px",
                borderRadius: 10,
                whiteSpace: "nowrap",
                transform: `scale(${chip})`,
              }}
            >
              {item.detail}
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
            backgroundColor: i === 0 ? brand.color : brand.textColor,
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
const ProgressBar: React.FC<{ segments: ProgressSegment[]; brand: Brand }> = ({
  segments,
  brand,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (!segments.length) return null;
  const total = segments[segments.length - 1].to - segments[0].from;
  const current = segments.find((s) => t >= s.from && t < s.to) ?? segments[segments.length - 1];
  const appear = interpolate(frame, [0, 10], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", top: 118, left: 56, right: 56, opacity: appear }}>
      <div style={{ display: "flex", gap: 8 }}>
        {segments.map((s, i) => {
          const fill = interpolate(t, [s.from, s.to], [0, 100], clamp);
          return (
            <div
              key={i}
              style={{
                flex: (s.to - s.from) / total,
                height: 12,
                borderRadius: 6,
                backgroundColor: "rgba(255,255,255,0.32)",
                overflow: "hidden",
                boxShadow: "0 2px 8px rgba(0,0,0,0.35)",
              }}
            >
              <div
                style={{
                  width: `${fill}%`,
                  height: "100%",
                  backgroundColor: brand.color,
                  borderRadius: 6,
                }}
              />
            </div>
          );
        })}
      </div>
      <div
        style={{
          marginTop: 12,
          fontFamily: BODY,
          fontWeight: 800,
          fontSize: 28,
          letterSpacing: 3,
          color: brand.textColor,
          textTransform: "uppercase",
          textShadow:
            "0 0 2px rgba(0,0,0,0.95), 0 0 6px rgba(0,0,0,0.9), 0 2px 12px rgba(0,0,0,0.85)",
          WebkitTextStroke: "1px rgba(0,0,0,0.6)",
        }}
      >
        {current.label}
      </div>
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
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontFamily: DISPLAY,
              fontSize: size,
              lineHeight: 1.16,
              letterSpacing: 1.5,
              color: w.highlight ? brand.color : brand.textColor,
              WebkitTextStroke: `${Math.round(size * 0.13)}px ${brand.darkColor}`,
              paintOrder: "stroke fill",
              textShadow: "0 8px 22px rgba(0,0,0,0.6)",
              opacity: said ? 1 : 0,
              transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px) scale(${scale}) rotate(${
                w.highlight && active ? -2 : 0
              }deg)`,
            }}
          >
            {w.text}
          </span>
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
      <svg width={width} height={height} style={{ position: "absolute" }}>
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={brand.darkColor}
          strokeWidth={16}
          strokeDasharray={circ}
          strokeDashoffset={draw}
          opacity={0.55}
          transform={`rotate(-90 ${cx} ${cy}) translate(${cx} ${cy}) scale(${pulse}) translate(${-cx} ${-cy})`}
        />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={brand.color}
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
          stroke={brand.color}
          strokeWidth={7}
          strokeLinecap="round"
        />
      </svg>
      <div
        style={{
          position: "absolute",
          top: ly - 40,
          ...(right ? { left: lx - 20 } : { right: width - lx - 20 }),
          maxWidth: 560,
          backgroundColor: brand.color,
          color: brand.darkColor,
          fontFamily: DISPLAY,
          fontSize: 60,
          lineHeight: 1.1,
          letterSpacing: 1,
          padding: "12px 26px",
          borderRadius: 12,
          boxShadow: SHADOW,
          transform: `scale(${pop})`,
          transformOrigin: right ? "left bottom" : "right bottom",
        }}
      >
        {item.text}
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
          [bt]: `10px solid ${brand.color}`,
          [bs]: `10px solid ${brand.color}`,
          filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.5))",
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
        <div
          style={{
            position: "absolute",
            top: 232,
            left: 56,
            display: "flex",
            alignItems: "center",
            gap: 14,
            padding: "10px 22px",
            borderRadius: 10,
            backgroundColor: "rgba(11,11,15,0.86)",
            border: `4px solid ${brand.color}`,
            color: brand.textColor,
            fontFamily: BODY,
            fontWeight: 800,
            fontSize: 30,
            letterSpacing: 3,
            opacity: tag,
          }}
        >
          <div style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: "#E11D2E" }} />
          {ev.label ?? "CAM 2"}
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
      <div
        style={{
          position: "absolute",
          top: 232,
          right: 56,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "10px 22px",
          borderRadius: 10,
          backgroundColor: slow ? "rgba(11,11,15,0.86)" : brand.color,
          border: `4px solid ${brand.color}`,
          color: slow ? brand.textColor : brand.darkColor,
          fontFamily: BODY,
          fontWeight: 800,
          fontSize: 34,
          letterSpacing: 3,
          transform: `scale(${pop})`,
          transformOrigin: "right center",
        }}
      >
        {slow ? (
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: 9,
              backgroundColor: brand.color,
              opacity: blink,
            }}
          />
        ) : (
          <span style={{ transform: `translateX(${(frame % 10) - 5}px)` }}>{">>"}</span>
        )}
        {ev.label ?? (slow ? "SLOW-MO" : "FAST")}
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
                border: `8px solid ${brand.color}`,
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
            <path d={BM} fill={brand.color} stroke={brand.color} strokeWidth={14} strokeLinejoin="round" clipPath="url(#bmfill)" />
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
                  fontFamily: DISPLAY,
                  fontSize: Math.min(210, Math.floor(1500 / Math.max(text.length, 6))),
                  lineHeight: 1.05,
                  letterSpacing: 2,
                  color: i === words.length - 1 ? brand.color : brand.textColor,
                  textShadow: SHADOW,
                  opacity: interpolate(s, [0, 0.3], [0, 1], clamp),
                  transform: `scale(${interpolate(s, [0, 1], [2.2, 1])})`,
                }}
              >
                {w}
              </div>
            );
          })}
        </div>
        {subtitle ? (
          <div
            style={{
              marginTop: 26,
              fontFamily: BODY,
              fontWeight: 700,
              fontSize: 48,
              color: brand.textColor,
              textTransform: "uppercase",
              letterSpacing: 2,
              opacity: interpolate(frame, [24, 32], [0, 1], clamp),
              transform: `translateY(${interpolate(frame, [24, 32], [30, 0], clamp)}px)`,
            }}
          >
            {subtitle}
          </div>
        ) : null}
        <div
          style={{
            marginTop: 54,
            padding: "14px 34px",
            borderRadius: 50,
            backgroundColor: brand.color,
            color: brand.darkColor,
            fontFamily: BODY,
            fontWeight: 800,
            fontSize: 44,
            transform: `scale(${spring({
              frame: frame - 30,
              fps,
              config: { damping: 10, stiffness: 200, mass: 0.6 },
            })})`,
          }}
        >
          {brand.handle}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
export const Overlay: React.FC<OverlayProps> = (p) => {
  useFonts();
  const { fps } = useVideoConfig();
  const fr = (s: number) => Math.max(0, Math.round(s * fps));
  const seq = (from: number, to: number) => ({
    from: fr(from),
    durationInFrames: Math.max(1, fr(to) - fr(from)),
  });
  const end = p.endCard ? p.endCard.from : p.duration;
  const titleEnd = p.title ? p.title.to : 0;
  return (
    <AbsoluteFill>
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
      {p.lowerThirds.map((lt, i) => {
        const s = seq(lt.from, lt.to);
        return (
          <Sequence key={`l${i}`} {...s}>
            <LowerThirdCard item={lt} brand={p.brand} frames={s.durationInFrames} y={p.layout.lowerThirdY} />
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
      {p.title ? (
        <Sequence {...seq(p.title.from, p.title.to)}>
          <TitleCard
            text={p.title.text}
            subtitle={p.title.subtitle}
            brand={p.brand}
            frames={seq(p.title.from, p.title.to).durationInFrames}
            animation={p.title.animation}
          />
        </Sequence>
      ) : null}
      <Sequence from={0} durationInFrames={Math.max(1, fr(end))}>
        <ProgressBar segments={p.progress} brand={p.brand} />
      </Sequence>
      {p.endCard ? (
        <Sequence {...seq(p.endCard.from, p.endCard.to)}>
          <EndCard text={p.endCard.text} subtitle={p.endCard.subtitle} brand={p.brand} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
