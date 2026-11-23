#!/usr/bin/env python3
"""Fonzi style effects, locked in Style Lab (style-lab/STYLE.md). Our own code and sounds; no colour grade ever.

    python3 scripts/style_fx.py snap IN.mp4 OUT.mp4 --at 0.4
        Gold title landing hit: 2-frame white flash, punch-in 1.08 -> 1 over 6 frames, small shake (+ impact sfx).
    python3 scripts/style_fx.py zoom A.mp4 B.mp4 OUT.mp4 [--cx 0.5 --cy 0.52]
        Zoom through: last 10 frames of A punch into a dark object (default his tank top, frame centre) with a
        radial zoom blur until black; B fades up out of the dark over 8 frames (+ whoosh, impact on the cut).
    python3 scripts/style_fx.py cutout A.mp4 B.mp4 OUT.mp4 [--to black|white]
        Cut out + punch in: A freezes on its last frame, he is cut out (rembg), the ORIGINAL background strobes
        to black (locked; white = optional) behind him for 10 frames, 5-frame punch-in with shake, hard cut to B
        (+ pop, clicks on the flickers, impact, whoosh).
    python3 scripts/style_fx.py logo OUT.mp4 --bg CLIP.mp4 [--drips slow|heavy|wet] [--dur 3.5]
        Logo end card: brand/fonzi_logo.png flickers on, then real drips run from the halo, letters and tail.
        Rotate slow / heavy / wet across videos. Background = CLIP blurred and darkened to 35 %.

    python3 scripts/style_fx.py intro IN.mp4 OUT.mp4 --title "LOCKED IN" --subtitle "5 LIFTS. ONE SONG."
            --style strobe|pulse|glitch|smash (--beats 0.667,1.335 | --bpm 89.88 --phase 0.667) [--dur 2.0]
            [--logo flat|3d] [--smash-keep-out left|right|none|x0,y0,x1,y1] [--piece] [--mask-src CLEAN.mp4]
            [--report intro.json] [--dump-layers DIR]
        Intro card (STYLE.md rule 0, locked 2026-11-21, Round 7 styles 2026-11-22): Rubik Dirt gold title (no
        drips) IN FRONT of him and below his face, small white letter-spaced subtitle, the Fonzi logo (white,
        ~1000 px, whole logo in frame) BEHIND him (rembg cut-out per frame, per shot when there is a hard cut
        inside the window). Four title styles, all landing on beat 1:
          strobe  solid from beat 1, off 2 frames on each later beat (r6-01, unchanged)
          pulse   round-2 flicker-on burst, then brighter + 1.0->1.06 on each later beat (r6-03, unchanged)
          glitch  the pulse burst, then on beats 2-4 a 3-frame red / cyan split (8/5/2 px, alpha <= 0.6) on the
                  letter edges only (scripts/intro_glitch.py, r7-03)
          smash   letters fade in scattered below his face and off the dumbbell side, fly into a spaced row,
                  smash home on beat 1 with a decaying shake, then the pulse (scripts/intro_smash.py, r7-05)
        Two logos: flat (fades up b1-4 -> b1, unchanged) or 3d (14 px white extrusion swinging to rest by b1+10,
        scripts/intro_logo3d.py, r7-04). Whoosh into beat 1, impact on beat 1, same for every style.
        No scrim, no box, no flash, no snap. Fails (exit 1) rather than draw on his face or clip the logo; a
        glitch or smash that cannot be drawn cleanly raises IntroStyleUnfit (finish_fx falls back to pulse).
        OUT = IN with the first --dur seconds replaced, IN's audio kept with the two sfx mixed under it.
        --piece: OUT is only the intro window, carrying only our sfx (like the other commands here).
        --dump-layers DIR: also save every frame's title and logo RGBA (title_NNNN.png / logo_NNNN.png; tests).

All inputs are scaled to 1080x1920 @ 30 fps. snap / zoom / cutout / logo drop the footage audio (the song goes on
later) and carry only our sfx (config.yaml sfx.roles: OpenFilm CC0 library, sfx/*.wav fallback), so mix it under the song or keep picture only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
W, H, FPS = 1080, 1920, 30
SFX = ROOT / "sfx"                 # old synthesised wavs; the sounds now come from common.sfx_file(<role>)
SOUNDS_USED: list[dict] = []       # every sound this process mixed in (role, offset in its piece, library id, licence)
LOGO = ROOT / "brand" / "fonzi_logo.png"

from intro_smash import IntroUnfit as _IntroUnfit  # noqa: E402  (numpy / PIL only; no style_fx import there)


class IntroStyleUnfit(_IntroUnfit):
    """The glitch / smash title cannot be drawn cleanly for this video (intro_smash.IntroUnfit re-exported, so
    `except IntroUnfit` and `except IntroStyleUnfit` both catch it). .style = the planned style, .reason = why.
    A SystemExit: uncaught it exits 1 with the message; finish_fx catches it and renders pulse instead."""
    def __init__(self, reason: str, style: str = "smash"):
        self.reason, self.style = reason, style
        SystemExit.__init__(self, f"IntroStyleUnfit: intro {style} unfit: {reason}")


# ---------- io ----------
def sound(role: str, at: float, db: float) -> Path:
    """The file for a sound role (config.yaml sfx.roles: OpenFilm CC0 library, old sfx/*.wav as the fallback),
    recorded in SOUNDS_USED so finish_fx.py / the caller can log it in output/work/sfx_log.json."""
    from common import sfx_log_entry
    e = sfx_log_entry(role, max(0.0, at), db, by="style_fx")
    SOUNDS_USED.append(e)
    return ROOT / e["file"]


def frames(path: Path) -> list[np.ndarray]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255
    if not len(a):
        raise SystemExit(f"no frames in {path}")
    return list(a)


def write(fr, out: Path, sounds: list[tuple[str, float, float]]):
    tmp = out.with_suffix(".pic.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                          "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    for f in fr:
        p.stdin.write((f if f.dtype == np.uint8 else (np.clip(f, 0, 1) * 255).astype(np.uint8)).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg failed writing the picture")
    dur = len(fr) / FPS
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", tmp, "-f", "lavfi", "-t", f"{dur:.3f}", "-i",
           "anullsrc=r=48000:cl=stereo"]
    parts, labels = [], ["[1:a]"]
    for k, (name, at, db) in enumerate(sounds):
        cmd += ["-i", sound(name, at, db)]
        ms = max(0, int(at * 1000))
        parts.append(f"[{k + 2}:a]volume={db}dB,adelay={ms}|{ms}[s{k}]")
        labels.append(f"[s{k}]")
    fc = ";".join(parts + [f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
                           "alimiter=limit=0.89[a]"])
    subprocess.run([str(c) for c in cmd + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]],
                   check=True)
    tmp.unlink()
    print(f"wrote {out} ({dur:.2f}s)")


def u8(f):
    return Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))


def zoom(f, z, cx, cy, dx=0, dy=0):
    cw, ch = W / z, H / z
    l, t = cx - cw / 2 + dx, cy - ch / 2 + dy
    return np.asarray(u8(f).crop((int(l), int(t), int(l + cw), int(t + ch))).resize((W, H), Image.BICUBIC),
                      np.float32) / 255


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


# ---------- effects ----------
def snap(inp: Path, out: Path, at: float):
    fr, k0 = frames(inp), int(round(at * FPS))
    shake = [(14, -10), (-12, 8), (8, -6), (-5, 4), (3, -2), (0, 0), (0, 0), (0, 0)]
    for d in range(8):
        k = k0 + d
        if k >= len(fr):
            break
        f = zoom(fr[k], 1 + 0.08 * (1 - d / 7) ** 2, W / 2, H / 2, *shake[d])
        fr[k] = f + (0.55 if d == 0 else 0.25 if d == 1 else 0)
    write(fr, out, [("snap_hit", at - 0.02, -3)])


def zoom_through(a: Path, b: Path, out: Path, cx=0.5, cy=0.52):
    A, B = frames(a), frames(b)
    n, cx, cy = 10, W * cx, H * cy
    res = A[:-n]
    for k in range(n):
        t = ((k + 1) / n) ** 2
        z = 1 + 5 * t
        im = u8(A[len(A) - n + k])
        cw, ch = W / z, H / z
        im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H))
        acc, m = np.asarray(im, np.float32) / 255, 1
        for s in (1.03, 1.06, 1.1)[: 1 + int(3 * t)]:       # radial zoom blur
            big = im.resize((int(W * s), int(H * s)))
            l, tp = (big.width - W) // 2, (big.height - H) // 2
            acc = acc + np.asarray(big.crop((l, tp, l + W, tp + H)), np.float32) / 255
            m += 1
        res.append(acc / m * (1 - 0.8 * t))
    res += [B[k] * (k + 1) / 8 for k in range(min(8, len(B)))] + B[8:]
    cut = len(A) / FPS
    write(res, out, [("zoom_whoosh", cut - 0.45, -8), ("zoom_impact", cut, -6)])


PATTERN = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0]


def cutout(a: Path, b: Path, out: Path, to: str = "black"):
    import layered_title as lt
    A, B = frames(a), frames(b)
    F = A[-1]
    session, _ = lt.cut_session()
    m = np.asarray(lt.person_mask(session, u8(F)).filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
    ys, xs = np.nonzero(m[..., 0] > 0.5)
    if not len(xs):
        raise SystemExit("cutout: no person found in the last frame of A; pick another cut point")
    cx, cy = float(xs.mean()), float(np.percentile(ys, 25))
    alt = np.zeros_like(F) if to == "black" else np.ones_like(F)
    res, clicks = list(A), []

    def fr(k):
        on = PATTERN[k % len(PATTERN)]
        if on and (k == 0 or not PATTERN[(k - 1) % len(PATTERN)]):
            clicks.append(len(res) / FPS)
        return m * F + (1 - m) * (alt if on else F)

    for i in range(10):
        res.append(zoom(fr(i), 1 + 0.03 * (i + 1) / 10, W / 2, H / 2))
    pin = len(res)
    shakes = [(18, -12), (-14, 10), (9, -6), (-5, 4), (0, 0)]
    for i in range(5):
        z = 1.03 + 0.37 * (1 - (1 - (i + 1) / 5) ** 3)
        res.append(zoom(fr(10 + i), z, W / 2 + (cx - W / 2) * (i + 1) / 5, H / 2 + (cy - H / 2) * (i + 1) / 5,
                        *shakes[i]))
    res += B
    write(res, out, [("cutout_pop", len(A) / FPS, -6), ("cutout_hit", pin / FPS - 0.02, -3),
                     ("cutout_whoosh", (pin + 5) / FPS - 0.2, -10)] + [("cutout_click", c, -14) for c in clicks])


def drip_tips(alpha, n, seed=5):
    op = alpha > 0.5
    edge = op & ~np.roll(op, -1, 0)
    ys, xs = np.nonzero(edge)
    cand = []
    for y, x in zip(ys, xs):
        if y < 20 or y > H - 30 or not op[y - 14, x]:
            continue
        row = op[y - 14]
        l = x
        while l > 0 and row[l - 1]:
            l -= 1
        r = x
        while r < W - 1 and row[r + 1]:
            r += 1
        if r - l > 44 or ((np.abs(xs - x) <= 22) & (ys > y) & (ys <= y + 30)).any():
            continue
        cand.append((y, x, r - l + 1))
    cand.sort(key=lambda c: -c[0])
    tips = []
    for y, x, w in cand:
        if all(abs(x - tx) > 26 or abs(y - ty) > 40 for tx, ty, _ in tips):
            tips.append((int(x), int(y), int(w)))
    np.random.default_rng(seed).shuffle(tips)
    return tips[:n]


def drip_layer(tips, k, ph, period, length, drops):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ts = k / FPS
    for (x, y, w), p in zip(tips, ph):
        w = min(w, 26)
        if drops:
            c = ((ts + p) % period) / period
            run, r = length * min(1, c / 0.7) ** 1.6, w * (0.35 + 0.35 * min(1, c / 0.7))
            if c < 0.7:
                d.rounded_rectangle((x - w * .32, y - 6, x + w * .32, y + run), radius=w * .3, fill="white")
                d.ellipse((x - r, y + run - r, x + r, y + run + r), fill="white")
            else:
                f = (c - 0.7) / 0.3
                d.rounded_rectangle((x - w * .3, y - 6, x + w * .3, y + length * (1 - f) ** 2 * .6), radius=w * .3,
                                    fill="white")
                fall = y + length + 1400 * (f * period * 0.3) ** 2
                d.ellipse((x - r * .9, fall - r * 1.2, x + r * .9, fall + r * 1.2),
                          fill=(255, 255, 255, int(255 * (1 - f * .6))))
        else:
            run, r = length * min(1, max(0, ts - p * 0.3) / 2.6) ** 0.7, w * 0.55
            d.rounded_rectangle((x - w * .32, y - 6, x + w * .32, y + run), radius=w * .3, fill="white")
            d.ellipse((x - r, y + run - r, x + r, y + run + r), fill="white")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255


def over(base, layer, alpha=1.0, glow=None, g=0.0):
    a = layer[..., 3:4] * alpha
    f = base * (1 - a) + layer[..., :3] * a
    if glow is not None and g > 0:
        f = screen(f, glow[..., :3] * glow[..., 3:4] * g)
    return f


def logo(out: Path, bg: Path, drips: str = "heavy", dur: float = 3.5):
    n = int(dur * FPS)
    lg = Image.open(LOGO).convert("RGBA")
    s = int(W * 0.78)
    lg = lg.resize((s, s), Image.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(lg, ((W - s) // 2, (H - s) // 2 - 60), lg)
    lay = np.asarray(layer, np.float32) / 255
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
    src = frames(bg)
    bgs = [np.asarray(u8(src[k % len(src)]).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255 * 0.35
           for k in range(n)]
    ntips, period, length, drops = {"slow": (6, 2.4, 90, True), "heavy": (14, 1.7, 150, True),
                                    "wet": (14, 0, 170, False)}[drips]
    tips = drip_tips(lay[..., 3], ntips)
    ph = np.random.default_rng(11).uniform(0, max(period, 1), len(tips))
    pat = [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1] + [1] * n
    clicks = [k / FPS for k in range(n) if pat[k] and (k == 0 or not pat[k - 1])]
    res = []
    for k in range(n):
        f = over(bgs[k], lay, pat[k], glow, 0.6 * pat[k])
        if pat[k] and k >= 14:
            f = over(f, drip_layer(tips, k - 14, ph, period, length, drops))
        res.append(f)
    write(res, out, [("logo_click", c, -10) for c in clicks] + [("logo_crackle", 0.0, -14)])


# ---------- intro card (STYLE.md rule 0, Style Lab rounds 5-6, locked 2026-11-21) ----------
TITLE_FONT = ROOT / "brand" / "fonts" / "RubikDirt-Regular.ttf"
SUB_FONT = ROOT / "remotion" / "public" / "fonts" / "Montserrat.ttf"
GOLD = (212, 160, 23)                       # #D4A017
SAFE_TOP, SAFE_BOTTOM = 110, H - 420        # Instagram's own buttons cover the rest
BURST = [0, 1, 0, 0, 1, 1, 0, 1]            # the locked round-2 flicker-on, first 8 frames (pulse style)
LOGO_ART_W = 1000                           # logo art width on screen (the png has margins round the art)
TITLE_W = 700                               # widest title line (round 5/6: "LOCKED" = 700 px)
TITLE_Y1 = 1000                             # preferred centre of the first title line (round 5/6 spot)
SUB_GAP = 140                               # last title line centre -> subtitle centre (at the 700 px size)
SUB_SIZE, SUB_TRACK = 46, 8
FACE_MARGIN = 40                            # clear space between his face box and the title block


def _font(path, size, weight=None):
    from PIL import ImageFont
    f = ImageFont.truetype(str(path), size)
    if weight:
        f.set_variation_by_name(weight)
    return f


def _fit(text, width):
    lo, hi = 10, 600
    while lo < hi:
        mid = (lo + hi + 1) // 2
        bb = _font(TITLE_FONT, mid).getbbox(text)
        lo, hi = (mid, hi) if bb[2] - bb[0] <= width else (lo, mid - 1)
    return lo


def _lines(title: str) -> list[str]:
    """One word: one line. More: two lines, as balanced as the words allow ("LOCKED" / "IN")."""
    w = title.upper().split()
    if len(w) <= 1:
        return w
    best = min(range(1, len(w)), key=lambda i: abs(len(" ".join(w[:i])) - len(" ".join(w[i:]))))
    return [" ".join(w[:best]), " ".join(w[best:])]


class TitleSpec:
    """Title + subtitle geometry for a given widest-line width; y is set later by the face guard."""
    def __init__(self, title, subtitle, width):
        self.lines, self.sub = _lines(title), subtitle.upper()
        ref = _fit("LOCKED", TITLE_W)                       # never bigger than the locked round-6 size
        self.size = min(_fit(max(self.lines, key=lambda t: _font(TITLE_FONT, 100).getlength(t)), width),
                        int(ref * width / TITLE_W))
        self.font = _font(TITLE_FONT, self.size)
        k = self.size / ref
        self.pitch = int(round(165 * k))                    # round 5: LOCKED 1000 / IN 1165
        self.sub_gap = int(round(SUB_GAP * k))
        self.sub_font = _font(SUB_FONT, SUB_SIZE, "ExtraBold")
        self.y1 = TITLE_Y1

    def centres(self):
        cys = [self.y1 + i * self.pitch for i in range(len(self.lines))]
        return cys, cys[-1] + self.sub_gap

    def _ink(self, f, text, cy):
        hb, bb = f.getbbox("H"), f.getbbox(text)
        y = cy - (hb[3] + hb[1]) // 2
        return y + bb[1], y + bb[3]

    def extent(self, pad_scale=1.0):
        """(x0, y0, x1, y1) of everything drawn, with room for the shadow (6 px down, 10 px blur) and the pulse."""
        cys, sy = self.centres()
        tops, bots = zip(*[self._ink(self.font, t, cy) for t, cy in zip(self.lines, cys)])
        st, sb = self._ink(self.sub_font, self.sub, sy) if self.sub else (min(tops), max(bots))
        y0, y1 = min(min(tops), st), max(max(bots), sb)
        tw = max(self.font.getlength(t) for t in self.lines)
        sw = sum(self.sub_font.getlength(c) for c in self.sub) + SUB_TRACK * max(0, len(self.sub) - 1)
        half = max(tw, sw) / 2
        tc = (cys[0] + cys[-1]) / 2
        ty0, ty1 = tc - (tc - min(tops)) * pad_scale, tc + (max(bots) - tc) * pad_scale
        half = max(half, tw / 2 * pad_scale)
        return (int(W / 2 - half - 24), int(min(y0, ty0) - 24), int(W / 2 + half + 24), int(max(y1, ty1) + 30))

    def layers(self):
        from PIL import Image as _I
        title, sub = _I.new("RGBA", (W, H), (0, 0, 0, 0)), _I.new("RGBA", (W, H), (0, 0, 0, 0))
        cys, sy = self.centres()
        for t, cy in zip(self.lines, cys):
            _line(title, t, self.font, cy, GOLD + (255,))
        if self.sub:
            _line(sub, self.sub, self.sub_font, sy, (255, 255, 255, 255), track=SUB_TRACK)
        return title, sub, (W / 2, (cys[0] + cys[-1]) / 2)


def _line(layer, text, f, cy, color, track=0):
    d = ImageDraw.Draw(layer)
    hb = f.getbbox("H")
    y = cy - (hb[3] + hb[1]) // 2
    if not track:
        bb = f.getbbox(text)
        d.text((W // 2 - (bb[2] - bb[0]) // 2 - bb[0], y), text, font=f, fill=color)
        return
    x = W / 2 - (sum(f.getlength(c) for c in text) + track * (len(text) - 1)) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=color)
        x += f.getlength(c) + track


def _scaled(layer, s, cx, cy):
    if abs(s - 1) < 1e-3:
        return layer
    big = layer.resize((int(round(W * s)), int(round(H * s))), Image.BICUBIC)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(big, (int(round(cx - cx * s)), int(round(cy - cy * s))), big)
    return out


def _with_alpha(layer, a):
    if a >= 1:
        return layer
    r = layer.copy()
    r.putalpha(r.getchannel("A").point(lambda v: int(v * a)))
    return r


def _shadow(layer, blur=10, opacity=0.6):
    """Tight soft shadow that follows the letters (fills the dirt specks so the gold reads over the white logo).
    Not a scrim."""
    a = layer.getchannel("A").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: int(min(255, v * 1.6) * opacity))
    sh = Image.new("RGBA", (W, H), (8, 8, 10, 0))
    sh.putalpha(a)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(sh, (0, 6), sh)
    return out


def _tint(layer, rgb):
    r = Image.new("RGBA", layer.size, tuple(rgb) + (0,))
    r.putalpha(layer.getchannel("A"))
    return r


def big_logo():
    """Logo art fitted to ~1000 px wide (or the frame height), white 85 %, centred; the whole art inside the frame."""
    src = Image.open(LOGO).convert("RGBA")
    art = src.crop(Image.fromarray((np.asarray(src)[..., 3] > 8).astype(np.uint8) * 255).getbbox())
    s = min(LOGO_ART_W / art.width, (H - 40) / art.height, (W - 40) / art.width)
    art = art.resize((int(round(art.width * s)), int(round(art.height * s))), Image.LANCZOS)
    a = art.getchannel("A").point(lambda v: int(v * 0.85))
    art = Image.merge("RGBA", (*[Image.new("L", art.size, 255)] * 3, a))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0 = (W - art.width) // 2, (H - art.height) // 2
    layer.paste(art, (x0, y0), art)
    box = (x0, y0, x0 + art.width, y0 + art.height)
    if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
        raise SystemExit(f"intro: the logo would be clipped by the frame edge {box}")
    return layer, box


def beat_frames(n: int, beats: list[float] | None, bpm: float | None, phase: float | None) -> list[int]:
    if beats:
        ts = sorted(beats)
    elif bpm:
        per, ph = 60.0 / bpm, (phase or 0.0)
        ts = [ph + i * per for i in range(200)]
    else:
        raise SystemExit("intro: give the song's beats (--beats t1,t2,... or --bpm N --phase T)")
    out = sorted({int(round(t * FPS)) for t in ts if 0 <= t * FPS < n})
    if not out:
        raise SystemExit(f"intro: no beat inside the first {n / FPS:.2f}s; the title lands on beat 1")
    return out


def title_state(style: str, k: int, beats: list[int]):
    """(visible, brightness 0-1, scale) of the title at frame k. Nothing before beat 1."""
    b1 = beats[0]
    if k < b1:
        return None
    if style == "strobe":                                   # r6-01: solid, off 2 frames on every later beat
        return None if any(b > b1 and 0 <= k - b < 2 for b in beats) else (0.0, 1.0)
    if style == "pulse":                                    # r6-03: burst on beat 1, then pulse each beat
        i = k - b1
        if i < len(BURST):
            return (0.0, 1.0) if BURST[i] else None
        for b in beats[1:]:
            d = k - b
            if 0 <= d < 6:
                e = (1, 0.8, 0.55, 0.3, 0.12, 0)[d]
                return (0.55 * e, 1.0 + 0.06 * e)
        return (0.0, 1.0)
    raise SystemExit(f"intro: unknown style {style!r} (strobe | pulse)")


def _extract(path: Path, n: int, into: Path) -> list[Path]:
    into.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf",
                    f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                    f"trim=end_frame={n},setpts=PTS-STARTPTS", "-an", str(into / "f%04d.png")], check=True)
    got = sorted(into.glob("f*.png"))
    if len(got) < n:
        raise SystemExit(f"intro: {path} has only {len(got)} frames, need {n}")
    return got[:n]


def shot_cuts(paths: list[Path]) -> list[int]:
    """Frames that start a new shot (hard cut inside the window): big jump in the downscaled picture."""
    sm = [np.asarray(Image.open(p).convert("L").resize((54, 96)), np.float32) / 255 for p in paths]
    d = [float(np.abs(sm[k] - sm[k - 1]).mean()) for k in range(1, len(sm))]
    med = float(np.median(d)) if d else 0.0
    return [k for k in range(1, len(sm)) if d[k - 1] > max(0.08, 4 * med)]


def head_box(mask: np.ndarray):
    """His head (cap + face + beard) from the cut-out: the top of the person, about 1.7 head-widths tall.
    None when there is no person in the frame."""
    rows = np.nonzero(mask.sum(1) >= 25)[0]
    if len(rows) < 80:
        return None
    top = int(rows[0])
    widths = mask[top: top + 160].sum(1)
    hw = float(np.median(widths[20:140])) if len(widths) >= 140 else float(widths.max())
    hw = min(max(hw, 120.0), 480.0)
    cols = np.nonzero(mask[top: top + int(0.8 * hw)].any(0))[0]
    x0, x1 = int(cols.min()), int(cols.max())
    return (max(0, x0 - 30), max(0, top - 10), min(W, x1 + 30), min(H, int(top + 1.7 * hw) + 30))


def _overlap_x(a, b):
    return a[0] < b[2] and b[0] < a[2]


def place_title(spec: TitleSpec, heads: list, visible: list[int], style: str, title_y: int | None,
                extra_face: tuple | None):
    """Put the title block below his face in every frame where it shows; shrink it if it does not fit; fail if
    there is no clean spot (never draw over his face)."""
    pad = 1.06 if style in ("pulse", "smash") else 1.0      # smash ends in the same pulse (style sheet pad 1.06)
    boxes = [heads[k] for k in visible if heads[k]] + ([extra_face] if extra_face else [])
    for width in range(TITLE_W, 519, -20):
        s = TitleSpec(" ".join(spec.lines), spec.sub, width)
        s.y1 = title_y or TITLE_Y1
        x0, y0, x1, y1 = s.extent(pad)
        need = max([b[3] + FACE_MARGIN for b in boxes if _overlap_x(b, (x0, y0, x1, y1))] + [SAFE_TOP])
        if title_y is None and y0 < need:
            s.y1 += need - y0
        x0, y0, x1, y1 = s.extent(pad)
        clear = all(not (_overlap_x(b, (x0, y0, x1, y1)) and y0 < b[3] + FACE_MARGIN) for b in boxes)
        if clear and y0 >= SAFE_TOP and y1 <= SAFE_BOTTOM:
            return s
        if title_y is not None:
            break
    lowest = max((b[3] for b in boxes), default=0)
    raise SystemExit(f"intro: no clean spot for the title below his face (his head reaches y={lowest}, the "
                     f"title must end above y={SAFE_BOTTOM}). Pick a shot where his face sits higher, a shorter "
                     "--dur, or --title-y by hand; not drawing over his face.")


TITLE_STYLES = ("strobe", "pulse", "glitch", "smash")
LOGO_STYLES = ("flat", "3d")
GOLD_MAX = (236, 212, 151)                  # #ECD497, brightest a title pixel may be (glitch / smash hard check)
LOGO_FIT_BOX = (4, 4, W - 4, H - 4)         # logo alpha > 8 bbox must stay inside on every frame


def _pulse_window(k: int, beats: list[int]) -> bool:
    return any(0 <= k - b < 6 for b in beats[1:])


def intro(inp: Path, out: Path, title: str, subtitle: str, style: str, beats=None, bpm=None, phase=None,
          dur: float = 3.0, piece: bool = False, mask_src: Path | None = None, report: Path | None = None,
          title_y: int | None = None, face_box: tuple | None = None, logo: str = "flat",
          smash_keep_out=None, dump_layers: Path | None = None) -> dict:
    import json
    import shutil
    import tempfile
    import layered_title as lt
    if style not in TITLE_STYLES:
        raise SystemExit(f"intro: unknown style {style!r} ({' | '.join(TITLE_STYLES)})")
    if logo not in LOGO_STYLES:
        raise SystemExit(f"intro: unknown logo {logo!r} ({' | '.join(LOGO_STYLES)})")
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(inp)], capture_output=True, text=True, check=True).stdout.strip())
    n = int(round(min(dur, total) * FPS))
    bts = beat_frames(n, beats, bpm, phase)
    b1 = bts[0]
    if style == "glitch":                                   # unfit checks before the slow cut-out
        import intro_glitch as ig
        if not ig.glitch_fits(bts, n):
            raise IntroStyleUnfit(f"no later beat with all 3 glitch frames inside the {n}-frame window "
                                  f"(beat frames {bts})", "glitch")
    if style == "smash" and b1 < 10:
        raise IntroStyleUnfit(f"beat 1 is on frame {b1}; the smash needs 10 frames before it (fade b1-9..b1-5, "
                              "fly b1-3..b1-1)", "smash")
    tmp = Path(tempfile.mkdtemp(prefix=".intro_", dir=out.parent))
    try:
        pics = _extract(inp, n, tmp / "pic")
        msrc = _extract(mask_src, n, tmp / "mask") if mask_src else pics
        cuts = shot_cuts(msrc)
        edges = [0] + cuts + [n]
        session, model = lt.cut_session()
        masks = []
        for a, b in zip(edges, edges[1:]):                 # per shot: no mask is ever mixed across a hard cut
            masks += lt.smooth_masks(lt.raw_masks(session, model, msrc[a:b]))
        marr = [np.asarray(m) > 128 for m in masks]
        heads = [head_box(m) for m in marr]
        visible = list(range(b1, n))
        spec = place_title(TitleSpec(title, subtitle, TITLE_W), heads, visible, style, title_y, face_box)
        tl, sub, (gcx, gcy) = spec.layers()
        plan = None
        if style == "smash":
            import intro_smash as ism
            try:
                plan = ism.SmashPlan.build(spec.lines, TITLE_FONT, spec.size, spec.centres()[0], tl, heads, marr,
                                           b1, n, keep_out=smash_keep_out, extra_face=face_box)
            except ism.IntroUnfit as e:
                raise IntroStyleUnfit(e.reason, "smash") from e
        flat, box = big_logo()
        logo_a = np.asarray(flat)[..., 3]
        art_px = float((logo_a > 20).sum())
        lg = None
        if logo == "3d":
            from intro_logo3d import Logo3D
            lg = Logo3D(flat, box)
            lg.fit(b1, n)                                   # shrinks in 2 % steps until every frame fits
        if dump_layers:
            dump_layers = Path(dump_layers)
            dump_layers.mkdir(parents=True, exist_ok=True)
        empty = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        issues, edge_px, vis_pct = [], 0, {}
        logo_max, logo_face, title_max = None, 0, None
        pic = tmp / "intro.pic.mp4"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                                "-pix_fmt", "yuv420p", str(pic)], stdin=subprocess.PIPE)
        yr = [H, 0]
        for k in range(n):
            img = Image.open(pics[k]).convert("RGBA")
            la = min(1.0, max(0.0, (k - (b1 - 4)) / 4))     # logo fades up under beat 1 (never flickers)
            comp = img
            lay = empty
            if la > 0:
                if lg is None:
                    lay = _with_alpha(flat, la)
                    fa = logo_a * la                        # flat: the round-6 measure, unchanged
                    fpx = art_px
                else:
                    lay, _ = lg.frame(k, b1)
                    fa = np.asarray(lay)[..., 3]
                    fpx = float((fa > 20).sum()) or 1.0
                comp = Image.alpha_composite(comp, lay)
                person = img.copy()
                person.putalpha(masks[k])
                comp = Image.alpha_composite(comp, person)
                vis = (fa > 20) & ~marr[k]
                edge_px += int(vis[0].sum() + vis[-1].sum() + vis[:, 0].sum() + vis[:, -1].sum())
                if k in (b1, n // 2, n - 1):
                    vis_pct[f"f{k}"] = round(100 * float(vis.sum()) / fpx, 1)
                lb = Image.fromarray((np.asarray(lay)[..., 3] > 8).astype(np.uint8) * 255).getbbox()
                if lb:
                    logo_max = list(lb) if logo_max is None else [min(logo_max[0], lb[0]), min(logo_max[1], lb[1]),
                                                                  max(logo_max[2], lb[2]), max(logo_max[3], lb[3])]
                    if (lb[0] < LOGO_FIT_BOX[0] or lb[1] < LOGO_FIT_BOX[1] or lb[2] > LOGO_FIT_BOX[2]
                            or lb[3] > LOGO_FIT_BOX[3]):
                        issues.append(f"f{k}: logo bbox {list(lb)} leaves the frame {list(LOGO_FIT_BOX)}")
                if heads[k]:                                # round-6 measure: visible logo on the soft
                    x0, y0, x1, y1 = heads[k]                   # mask edge (64 < mask <= 128) in his head box
                    soft = np.asarray(masks[k])[y0:y1, x0:x1] > 64
                    logo_face += int((vis[y0:y1, x0:x1] & soft).sum())
            txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            t = None
            if style in ("strobe", "pulse"):
                st = title_state(style, k, bts)
                if st:
                    amt, sc = st
                    t = tl
                    if amt:
                        g = np.array(GOLD, np.float32)
                        t = _tint(tl, [int(v) for v in g + (255 - g) * amt])
                    t = _scaled(t, sc, gcx, gcy)
            elif style == "glitch":
                t = ig.glitch_title(tl, k, bts)
            else:
                t = plan.title(k, tl, bts)
            if t is not None:
                txt = Image.alpha_composite(txt, t)
                ta = np.asarray(t)
                on = ta[..., 3] > 128
                if on.any():
                    mx = ta[..., :3][on].max(0)
                    title_max = mx if title_max is None else np.maximum(title_max, mx)
                    hard = style == "glitch" or (style == "smash" and not _pulse_window(k, bts))
                    if hard and (mx > np.array(GOLD_MAX)).any():
                        issues.append(f"f{k}: title pixel {mx.tolist()} brighter than #ECD497")
            if dump_layers:
                (t if t is not None else empty).save(dump_layers / f"title_{k:04d}.png")
                lay.save(dump_layers / f"logo_{k:04d}.png")
            sd = k - (b1 + 8)
            if sd >= 0 and spec.sub:                        # subtitle eases up under the title, then holds
                e = 1 - (1 - min(1.0, sd / 6)) ** 3
                sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                sl.paste(sub, (0, int(18 * (1 - e))), sub)
                txt = Image.alpha_composite(txt, _with_alpha(sl, e))
            if txt.getbbox():                               # every style: title, split copies, glyphs, subtitle
                comp = Image.alpha_composite(Image.alpha_composite(comp, _shadow(txt)), txt)
                ys, xs = np.nonzero(np.asarray(txt.getchannel("A")) > 20)
                yr = [min(yr[0], int(ys.min())), max(yr[1], int(ys.max()))]
                if ys.min() < SAFE_TOP or ys.max() > SAFE_BOTTOM:
                    issues.append(f"f{k}: text y {ys.min()}-{ys.max()} outside the safe area")
                for hb in [heads[k], face_box]:
                    if hb:
                        x0, y0, x1, y1 = hb
                        c = int(((xs >= x0) & (xs < x1) & (ys >= y0) & (ys < y1)).sum())
                        if c:
                            issues.append(f"f{k}: {c} title px on his face box {hb}")
            enc.stdin.write(np.asarray(comp.convert("RGB"), np.uint8).tobytes())
        enc.stdin.close()
        if enc.wait():
            raise SystemExit("intro: ffmpeg failed writing the picture")
        if edge_px:
            issues.append(f"logo touches the frame edge ({edge_px} px)")
        gl = ig.glitch_stats(tl, bts, n) if style == "glitch" else None
        if gl and (gl["split_px_inside_letters"] or gl["split_alpha_max"] > ig.SPLIT_ALPHA_MAX):
            issues.append(f"glitch split inside the letters / too strong: {gl}")
        if issues:
            raise SystemExit("intro: refusing to write it:\n  " + "\n  ".join(issues[:12]))
        sounds = [("intro_whoosh", b1 / FPS - 0.30, -14), ("intro_impact", b1 / FPS - 0.02, -5)]
        _intro_out(pic, inp, out, n, total, sounds, piece)
        res = {"ok": True, "style": style, "title": spec.lines, "subtitle": spec.sub, "font": TITLE_FONT.name,
               "title_size": spec.size, "title_y1": spec.y1, "title_extent": list(spec.extent()),
               "text_y_range": yr, "dur": round(n / FPS, 3), "frames": n, "beat_frames": bts,
               "beats_s": [round(b / FPS, 3) for b in bts], "shot_cuts": cuts, "cut_model": model,
               "logo_box": list(box), "logo_size": [box[2] - box[0], box[3] - box[1]], "logo_visible_pct": vis_pct,
               "logo_edge_px": edge_px, "face_max_y": max((h[3] for h in heads if h), default=None),
               "faces_found": sum(1 for h in heads if h), "sounds": [list(s) for s in sounds],
               "piece": piece, "input": str(inp), "output": str(out),
               "logo_style": logo, "logo_scale": lg.scale if lg else 1.0, "logo_box_max": logo_max,
               "logo_on_face_px_max": logo_face,      # window total, as round 6 (2087)
               "title_max_rgb": [int(v) for v in title_max] if title_max is not None else None,
               "glitch": gl, "smash": plan.stats() if plan else None}
        print(f"intro {style} / logo {logo}: {' / '.join(spec.lines)} ({spec.size}px, line 1 at y={spec.y1}), logo "
              f"{res['logo_size']} at {box} (scale {res['logo_scale']}), beats {res['beats_s']}, shots "
              f"{len(edges) - 1}, his face down to y={res['face_max_y']}, text y {yr[0]}-{yr[1]}: clear of his "
              f"face in all {n} frames; title max rgb {res['title_max_rgb']}, logo on face {logo_face} px")
        if report:
            report.write_text(json.dumps(res, indent=1))
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _intro_out(pic: Path, inp: Path, out: Path, n: int, total: float, sounds, piece: bool):
    if piece:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", pic, "-f", "lavfi", "-t", f"{n / FPS:.3f}", "-i",
               "anullsrc=r=48000:cl=stereo"]
        base, first = "[1:a]", 2
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", inp]
        base, first = "[1:a]", 2
    parts, labels = [], [base]
    for k, (name, at, db) in enumerate(sounds):
        cmd += ["-i", sound(name, at, db)]
        ms = max(0, int(at * 1000))
        parts.append(f"[{k + first}:a]volume={db}dB,adelay={ms}|{ms}[s{k}]")
        labels.append(f"[s{k}]")
    mix = f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.89:level=0:latency=1[a]"
    if piece:
        fc = ";".join(parts + [mix])
        tail = ["-map", "0:v", "-map", "[a]", "-c:v", "copy", "-t", f"{n / FPS:.3f}"]
    else:
        fc = ";".join(parts + [
            f"[0:v]fps={FPS},format=yuv420p,setsar=1[i]",
            f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
            f"trim=start_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[r]",
            "[i][r]concat=n=2:v=1:a=0[v]", mix])
        tail = ["-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v",
                "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{total:.3f}"]
    subprocess.run([str(c) for c in cmd + ["-filter_complex", fc, *tail, "-c:a", "aac", "-b:a", "192k",
                                           "-movflags", "+faststart", out]], check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snap"); s.add_argument("inp", type=Path); s.add_argument("out", type=Path)
    s.add_argument("--at", type=float, required=True)
    z = sub.add_parser("zoom"); z.add_argument("a", type=Path); z.add_argument("b", type=Path)
    z.add_argument("out", type=Path); z.add_argument("--cx", type=float, default=0.5); z.add_argument("--cy", type=float, default=0.52)
    c = sub.add_parser("cutout"); c.add_argument("a", type=Path); c.add_argument("b", type=Path)
    c.add_argument("out", type=Path); c.add_argument("--to", choices=["black", "white"], default="black")
    lo = sub.add_parser("logo"); lo.add_argument("out", type=Path); lo.add_argument("--bg", type=Path, required=True)
    lo.add_argument("--drips", choices=["slow", "heavy", "wet"], default="heavy"); lo.add_argument("--dur", type=float, default=3.5)
    it = sub.add_parser("intro"); it.add_argument("inp", type=Path); it.add_argument("out", type=Path)
    it.add_argument("--title", required=True); it.add_argument("--subtitle", default="")
    it.add_argument("--style", choices=list(TITLE_STYLES), required=True,
                    help="strobe | pulse (round 6, unchanged) | glitch (r7-03 edge split) | smash (r7-05 letters)")
    it.add_argument("--logo", choices=list(LOGO_STYLES), default="flat",
                    help="flat (round 6, unchanged) | 3d (r7-04 extruded white logo swinging to rest)")
    it.add_argument("--smash-keep-out", help="smash only: left | right | none | x0,y0,x1,y1 (default: auto side)")
    it.add_argument("--dump-layers", type=Path, help="test use: save each frame's title / logo RGBA here")
    it.add_argument("--beats", help="beat times in seconds, comma list (beat 1 = first one)")
    it.add_argument("--bpm", type=float); it.add_argument("--phase", type=float, default=0.0)
    it.add_argument("--dur", type=float, default=3.0)
    it.add_argument("--piece", action="store_true", help="write only the intro window with only our sfx")
    it.add_argument("--mask-src", type=Path, help="clean picture (no graphics) to cut him out of; default IN")
    it.add_argument("--title-y", type=int, help="centre of the first title line by hand (still face-checked)")
    it.add_argument("--face-box", help="x0,y0,x1,y1 extra face box to keep clear (for a hard shot)")
    it.add_argument("--report", type=Path)
    a = ap.parse_args()
    if a.cmd == "intro":
        intro(a.inp, a.out, a.title, a.subtitle, a.style,
              [float(x) for x in a.beats.split(",") if x.strip()] if a.beats else None, a.bpm, a.phase, a.dur,
              a.piece, a.mask_src, a.report, a.title_y,
              tuple(int(v) for v in a.face_box.split(",")) if a.face_box else None, a.logo,
              (tuple(int(v) for v in a.smash_keep_out.split(",")) if "," in a.smash_keep_out else a.smash_keep_out)
              if a.smash_keep_out else None, a.dump_layers)
    elif a.cmd == "snap":
        snap(a.inp, a.out, a.at)
    elif a.cmd == "zoom":
        zoom_through(a.a, a.b, a.out, a.cx, a.cy)
    elif a.cmd == "cutout":
        cutout(a.a, a.b, a.out, a.to)
    else:
        logo(a.out, a.bg, a.drips, a.dur)
