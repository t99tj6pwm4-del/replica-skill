export type Brand = {
  name: string;
  handle: string;
  color: string;
  textColor: string;
  darkColor: string;
  /** pop-up cards gold (config/brand.json "popup_color"), default #D4A017 */
  popupColor?: string;
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
  // optional: ring follows a moving target (absolute seconds, 0..1 coords);
  // the label stays anchored to x/y
  track?: { t: number; x: number; y: number }[];
};

export type TimedEvent = {
  from: number;
  to: number;
  kind: "punch_in" | "slow_mo" | "speed_ramp" | "cam";
  label?: string;
  /** optional tag position in px (cam events only); default left 56, top 232 */
  x?: number;
  y?: number;
};

export type ListCardItem = {
  from: number;
  to: number;
  title: string;
  items: string[];
  y: number; // px from the top of the 1920 frame
  compact?: boolean; // header + one row of items (~112px tall)
};

/* Pop-up cards (Alfonso, 2026-11-17): gym reels only. Times are cut seconds, y is px from the top (1920). */
export type ExerciseBarPopup = {
  from: number;
  to: number;
  title: string; // exercise name, shown in caps
  detail: string; // "4 x 12 \u2022 Press de mina"
  y: number;
};

export type FormTipPopup = {
  from: number;
  to: number;
  lift: string;
  cue: string; // English cue
  cueEs: string; // Spanish line
  y: number;
};

export type ChecklistPopup = {
  from: number;
  to: number;
  items: string[]; // every lift in the video, in order
  current: number; // index of the lift on screen; items before it are done
  y: number;
};

export type Popups = {
  bars: ExerciseBarPopup[];
  formTip: FormTipPopup | null;
  checklists: ChecklistPopup[];
};

export type OverlayProps = {
  fps: number;
  width: number;
  height: number;
  duration: number; // seconds
  brand: Brand;
  layout: { captionY: number; lowerThirdY: number; titleOffsetY?: number };
  title: { from: number; to: number; text: string; subtitle?: string; animation?: string } | null;
  lowerThirds: LowerThird[];
  progress: ProgressSegment[];
  captions: CaptionPage[];
  callouts: Callout[];
  events: TimedEvent[];
  endCard: { from: number; to: number; text: string; subtitle?: string } | null;
  lists?: ListCardItem[];
  /** cut-time windows where the clip has its own baked-in text: nothing but a bare progress bar is drawn */
  noTextWindows?: { from: number; to: number }[];
  /** false = progress bar without the segment name under it */
  progressLabels?: boolean;
  /** pop-up cards: exercise bar, form tip, routine checklist (optional; absent = no pop-ups) */
  popups?: Popups;
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
