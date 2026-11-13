export type Brand = {
  name: string;
  handle: string;
  color: string;
  textColor: string;
  darkColor: string;
};

export type CaptionWord = {
  text: string;
  start: number;
  end: number;
  highlight?: boolean;
};

export type CaptionPage = {
  start: number;
  end: number;
  words: CaptionWord[];
};

export type LowerThird = {
  from: number;
  to: number;
  title: string;
  detail?: string;
  index: number;
  total: number;
};

export type ProgressSegment = { from: number; to: number; label: string };

export type Callout = {
  from: number;
  to: number;
  text: string;
  x: number; // 0..1 of frame width — the thing being pointed at
  y: number; // 0..1 of frame height
};

export type TimedEvent = {
  from: number;
  to: number;
  kind: "punch_in" | "slow_mo" | "speed_ramp";
  label?: string;
};

export type OverlayProps = {
  fps: number;
  width: number;
  height: number;
  duration: number; // seconds
  brand: Brand;
  layout: { captionY: number; lowerThirdY: number };
  title: { from: number; to: number; text: string; subtitle?: string } | null;
  lowerThirds: LowerThird[];
  progress: ProgressSegment[];
  captions: CaptionPage[];
  callouts: Callout[];
  events: TimedEvent[];
  endCard: { from: number; to: number; text: string; subtitle?: string } | null;
};

export type CarouselProps = {
  brand: Brand;
  slide: {
    kind: "cover" | "exercise";
    title: string;
    detail?: string;
    cue?: string;
    index: number;
    total: number;
    image?: string; // file name inside the public dir
  };
};
