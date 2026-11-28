#!/usr/bin/env python3
"""VIDEO-INSIDE-TEXT intro (Alfonso, 2026-11-23, Director answer 25). THE default intro for every gym video; it
replaces the round 7 rotation (strobe / pulse / glitch / smash, kept in style_fx.py unused, for history) and every
older intro card. Order in the video: logo opener (answer 23) -> this -> normal video.

    python3 scripts/style_fx.py intro IN.mp4 OUT.mp4 --style video_text --title "GRIND DAY" --piece --start 1.183
    python3 scripts/intro_video_text.py selftest --out output/video_text_test/selftest/   # synthetic footage

Timeline (fixed seconds, not beat-snapped; config intro.video_text):
    0.0        full black frame over the video, which is already playing underneath
    0.0-1.2 s  the title types on letter by letter with a blinking text cursor at the end; the letters are cut OUT
               of the black, so his footage shows THROUGH them, everything else solid black
    1.2-1.8 s  hold, the cursor blinks twice   (all three times configurable: config intro.video_text type_end /
               hold_end / dur, cap max_dur 3.5 s since his round 8 note "Slower open fine if it needs to go past 3 s")
    1.8-2.6 s  the black splits along a horizontal line through the middle of the title: the top half slides up off
               screen, the bottom half down, each taking its half of the letters; ease out (cubic). The last frame of
               the window has no matte left, so the next frame (normal video) continues with no cut and no jump
    2.6 s      over; never more than 3 s
Text: this video's hook / title (storyboard intro.title or the hook title), 1-2 words, ALL CAPS, Montserrat Black,
as big as fits the width with a safe margin, centred, 2 words stacked on 2 lines. No tilt, box, label, subtitle,
logo or glow (the white text look does NOT apply: these letters are holes). The cursor is a cut-out bar too.
Brightening: if the footage seen through the letters is too dark (mean luma inside the letters < `min_luma`),
ONLY the pixels inside the letter holes are brightened (gain <= `max_gain`); nothing else is ever graded.
The footage under the matte is the real start of the video (IN from --start), not a separate clip; audio untouched
(the piece carries only quiet sfx: a soft tick per letter, a whoosh on the split, mixed under the song by finish_fx).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "remotion" / "public" / "fonts" / "Montserrat.ttf"
DEFAULTS = {"dur": 2.6, "type_end": 1.2, "hold_end": 1.8, "max_dur": 3.5, "margin": 80, "line_gap": 0.06,
            "max_size": 420, "min_luma": 0.32, "max_gain": 1.9, "tick_db": -20, "whoosh_db": -14,
            "cursor_w": 0.10, "cursor_gap": 0.06, "blinks": 2, "ease": "cubic", "seam_frames": 0, "seam_px": 8,
            "force_gain": None}
# Style Lab round 8 variants change only these keys: cursor_w / blinks (B2 thinner, faster cursor), ease "expo"
# (B2 harder split), force_gain (B3 letters-only brightening shown), seam_frames / seam_px (B4 a thin line of video
# opens at the seam for 2 frames before the halves move). The production default is B1 = Alfonso's exact spec.


class VideoTextUnfit(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason, self.style = reason, "video_text"


def cfg() -> dict:
    try:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from common import load_config
        c = (load_config().get("intro") or {}).get("video_text") or {}
    except Exception:
        c = {}
    return {**DEFAULTS, **c}


def clean_title(title: str) -> list[str]:
    words = [w for w in title.upper().replace("\n", " ").split() if w]
    if not 1 <= len(words) <= 2:
        raise VideoTextUnfit(f"title {title!r} must be 1-2 words (got {len(words)})")
    if any(not w.isascii() or "#" in w for w in words):
        raise VideoTextUnfit(f"title {title!r}: English, no hashtags")
    return words


def _font(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT), size)
    try:
        f.set_variation_by_name("Black")
    except Exception:
        pass
    return f


class Layout:
    """Montserrat Black, the biggest size whose widest line (+ the cursor) fits W - 2 * margin; lines centred on the
    frame, the block centred vertically on `cy` (default the frame centre). split_y = the title's vertical centre."""

    def __init__(self, words: list[str], c: dict, cy: int | None = None):
        self.lines, self.c = words, c
        avail = W - 2 * int(c["margin"])
        lo, hi = 20, int(c["max_size"])
        while lo < hi:
            mid = (lo + hi + 1) // 2
            f = _font(mid)
            wid = max(f.getlength(t) for t in words) + mid * (c["cursor_w"] + c["cursor_gap"])
            lo, hi = (mid, hi) if wid <= avail else (lo, mid - 1)
        self.size = lo
        self.font = _font(lo)
        hb = self.font.getbbox("H")
        self.cap = hb[3] - hb[1]
        self.pitch = int(round(self.cap * (1 + c["line_gap"] + 0.22)))
        cy = H // 2 if cy is None else cy
        n = len(words)
        self.centres = [int(round(cy + (i - (n - 1) / 2) * self.pitch)) for i in range(n)]
        self.split_y = int(round((self.centres[0] + self.centres[-1]) / 2))
        self.hb = hb

    def letters(self) -> list[tuple[int, int, int]]:
        """(line index, char index, x of the char's pen position) for every character, typing order."""
        out = []
        for li, t in enumerate(self.lines):
            x0 = W / 2 - self.font.getlength(t) / 2
            for ci in range(len(t)):
                out.append((li, ci, x0 + self.font.getlength(t[:ci])))
        return out

    def holes(self, n_letters: int, cursor: bool) -> np.ndarray:
        """Letter holes (bool H x W) with the first n_letters typed, plus the cursor bar after the last one."""
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        left = n_letters
        last = (0, W / 2 - self.font.getlength(self.lines[0]) / 2)       # where the cursor sits
        for li, t in enumerate(self.lines):
            if left <= 0:
                break
            shown = t[:left]
            left -= len(t)
            x0 = W / 2 - self.font.getlength(t) / 2
            y = self.centres[li] - (self.hb[3] + self.hb[1]) // 2
            if shown.strip():
                d.text((x0, y), shown, font=self.font, fill=255)
            last = (li, x0 + self.font.getlength(shown))
            if left > 0 and li + 1 < len(self.lines) and left >= 0 and len(shown) == len(t) and left == 0:
                pass
        if n_letters and n_letters == sum(len(t) for t in self.lines[: last[0] + 1]) and last[0] + 1 < len(self.lines) \
                and n_letters < sum(len(t) for t in self.lines):
            nl = last[0] + 1                                              # line done: cursor waits on the next line
            last = (nl, W / 2 - self.font.getlength(self.lines[nl]) / 2)
        if cursor:
            li, x = last
            cy = self.centres[li]
            gap, cw = self.size * self.c["cursor_gap"], self.size * self.c["cursor_w"]
            top = cy - self.cap / 2 - self.cap * 0.08
            d.rectangle((x + gap, top, x + gap + cw, top + self.cap * 1.16), fill=255)
        return np.asarray(im) > 127

    def bbox(self) -> tuple[int, int, int, int]:
        h = self.holes(sum(len(t) for t in self.lines), True)
        ys, xs = np.nonzero(h)
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def schedule(n_chars: int, c: dict, n: int) -> list[dict]:
    """Per frame: typed letters, cursor on/off, split progress 0..1 (eased), offsets of the two halves."""
    t_end, h_end = int(round(c["type_end"] * FPS)), int(round(c["hold_end"] * FPS))
    out = []
    for k in range(n):
        typed = min(n_chars, int(n_chars * (k + 1) / t_end)) if k < t_end else n_chars
        if k < t_end:
            cur = True                                           # solid while typing
        elif k < h_end:
            per = (h_end - t_end) / max(1, int(c["blinks"]))     # blinks twice in the hold: off / on, off / on
            cur = int((k - t_end) // (per / 2)) % 2 == 1
        else:
            cur = False
        sf = int(c.get("seam_frames") or 0)                    # B4: a thin seam of video first, then the split
        seam = 0
        if k < h_end:
            p = 0.0
        elif k < h_end + sf:
            p, seam = 0.0, int(c["seam_px"])
        else:
            span = max(1, n - 1 - h_end - sf)
            p = min(1.0, (k - h_end - sf) / span)
            seam = int(c["seam_px"]) if sf else 0
        e = 1 - 2 ** (-10 * p) if c.get("ease") == "expo" and p < 1 else (1.0 if p >= 1 else 1 - (1 - p) ** 3)
        out.append({"typed": typed, "cursor": cur, "split": round(p, 4), "ease": round(e, 4), "seam": seam})
    return out


def matte_frame(holes: np.ndarray, split_y: int, ease: float, seam: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """(black alpha 0/1, letter-hole mask) for the frame: the matte (1 - holes) split at split_y, top half moved up
    by ease * split_y (+ margin), bottom half down by ease * (H - split_y) (+ margin); uncovered = no black."""
    black = np.zeros((H, W), bool)
    hole = np.zeros((H, W), bool)
    m = ~holes
    up = int(round(ease * (split_y + 8))) + seam // 2
    dn = int(round(ease * (H - split_y + 8))) + (seam - seam // 2)
    if up < split_y:                                             # top half: rows [0, split_y) -> [-up, split_y-up)
        black[: split_y - up] = m[up:split_y]
        hole[: split_y - up] = holes[up:split_y]
    if split_y + dn < H:                                         # bottom half: rows [split_y, H) -> + dn
        black[split_y + dn:] = m[split_y: H - dn]
        hole[split_y + dn:] = holes[split_y: H - dn]
    return black, hole


def _luma(f: np.ndarray) -> np.ndarray:
    return (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]) / 255.0


def render(pics: list[np.ndarray], title: str, c: dict | None = None, cy: int | None = None) -> tuple[list, dict]:
    """pics = the real footage frames (uint8 H x W x 3), as many as the intro window. Returns (frames, report)."""
    c = {**cfg(), **(c or {})}
    n = len(pics)
    if n / FPS > float(c["max_dur"]) + 1e-6:
        raise VideoTextUnfit(f"{n / FPS:.2f}s is over the {c['max_dur']}s limit")
    words = clean_title(title)
    lay = Layout(words, c, cy)
    n_chars = sum(len(t) for t in words)
    sch = schedule(n_chars, c, n)
    full = lay.holes(n_chars, False)
    h_end = int(round(c["hold_end"] * FPS))
    # brightness through the letters over the black part (only the letter holes may be brightened)
    lum = [float(_luma(pics[k].astype(np.float32))[full].mean()) for k in range(0, min(n, h_end), 3)]
    mean_l = float(np.mean(lum)) if lum else 1.0
    gain = 1.0 if mean_l >= c["min_luma"] else min(float(c["max_gain"]), float(c["min_luma"]) / max(mean_l, 1e-3))
    if c.get("force_gain"):
        gain = float(c["force_gain"])
    out, stats = [], {"outside_black_max": 0, "through_luma_min": 9.0, "black_cover": [], "gain": round(gain, 3)}
    cache = {}
    for k in range(n):
        s = sch[k]
        key = (s["typed"], s["cursor"])
        if key not in cache:
            cache[key] = lay.holes(*key)
        black, hole = matte_frame(cache[key], lay.split_y, s["ease"], s["seam"])
        f = pics[k].astype(np.float32)
        if gain > 1.0 and hole.any():
            f[hole] = np.clip(f[hole] * gain, 0, 255)
        f[black] = 0.0
        g = f.astype(np.uint8)
        out.append(g)
        cover = float(black.mean())
        stats["black_cover"].append(round(cover, 4))
        if k < h_end:
            stats["outside_black_max"] = max(stats["outside_black_max"], int(g[~cache[key]].max()) if (~cache[key]).any() else 0)
            if hole.any() and s["typed"] == n_chars:
                stats["through_luma_min"] = min(stats["through_luma_min"], float(_luma(g.astype(np.float32))[hole].mean()))
    last_diff = float(np.abs(out[-1].astype(np.int16) - pics[-1].astype(np.int16)).mean())
    t_end = int(round(c["type_end"] * FPS))
    rep = {"style": "video_text", "max_dur": float(c["max_dur"]), "timeline": {"type_end": c["type_end"],
           "hold_end": c["hold_end"], "dur": round(n / FPS, 3)}, "title": words, "font": "Montserrat Black", "size": lay.size,
           "line_centres_y": lay.centres, "split_y": lay.split_y, "text_box": list(lay.bbox()),
           "frames": n, "dur": round(n / FPS, 3), "type_end_s": c["type_end"], "hold_end_s": c["hold_end"],
           "split_from_s": round(h_end / FPS, 3), "matte_gone_frame": next((k for k in range(n) if stats["black_cover"][k] == 0), None),
           "cover_at_split_start": stats["black_cover"][min(h_end, n - 1)],
           "cover_first_frame": stats["black_cover"][0],
           "outside_letters_max_value_0_1_8": stats["outside_black_max"],
           "through_letters_luma_min": round(stats["through_luma_min"], 3) if stats["through_luma_min"] < 9 else None,
           "through_letters_luma_raw": round(mean_l, 3), "brighten_gain_letters_only": stats["gain"],
           "last_frame_vs_footage_mean_abs": round(last_diff, 3),
           "typed_at_type_end": sch[min(t_end, n - 1)]["typed"], "chars": n_chars,
           "cursor_blinks_in_hold": sum(1 for k in range(t_end + 1, min(h_end, n))
                                         if sch[k]["cursor"] and not sch[k - 1]["cursor"]),
           "variant": {k: c[k] for k in ("cursor_w", "blinks", "ease", "seam_frames", "seam_px", "force_gain")},
           "letter_frames": sorted({next(k for k in range(n) if sch[k]["typed"] >= i) for i in range(1, n_chars + 1)})}
    return out, rep


def checks(rep: dict) -> list[str]:
    """Hard problems (empty = fine): used by style_fx before writing and repeated by qa_check."""
    bad = []
    cap = float(rep.get("max_dur") or 3.5)
    if rep["dur"] > cap + 1e-6:
        bad.append(f"intro {rep['dur']}s is over the {cap} s cap")
    if rep["outside_letters_max_value_0_1_8"] > 2:
        bad.append(f"outside the letters is not black in 0-1.8 s (max value {rep['outside_letters_max_value_0_1_8']})")
    if rep["through_letters_luma_min"] is None or rep["through_letters_luma_min"] < 0.08:
        bad.append(f"too dark through the letters (luma {rep['through_letters_luma_min']})")
    if rep["matte_gone_frame"] is None or rep["matte_gone_frame"] > rep["frames"] - 1:
        bad.append(f"matte not fully gone by the end (frames {rep['frames']})")
    if rep["cover_at_split_start"] < 0.5:
        bad.append(f"black not covering the frame when the split starts ({rep['cover_at_split_start']})")
    if rep["last_frame_vs_footage_mean_abs"] > 0.5:
        bad.append(f"last intro frame differs from the footage ({rep['last_frame_vs_footage_mean_abs']}): jump")
    if rep["typed_at_type_end"] != rep["chars"]:
        bad.append("title not fully typed by 1.2 s")
    return bad


def _selftest(out_dir: str) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = 78
    yy, xx = np.mgrid[0:H, 0:W]
    pics = []
    for k in range(n):
        f = np.zeros((H, W, 3), np.uint8)
        f[..., 0] = (xx * 255 // W + k * 3) % 256
        f[..., 1] = (yy * 255 // H)
        f[..., 2] = 140
        pics.append(f)
    fr, rep = render(pics, "Grind Day")
    bad = checks(rep)
    for k in (6, 24, 45, 60, 69, 77):
        Image.fromarray(fr[k]).resize((360, 640)).save(out / f"f{k:02d}.png")
    rep["problems"] = bad
    (out / "report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != "letter_frames"}, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("selftest")
    s.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.exit(_selftest(a.out))
