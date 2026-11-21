#!/usr/bin/env python3
"""Style Lab round 2 (from his round 1 notes). Ungraded footage only (he grades himself).
 - Logo: the kept "flicker on" + REAL dripping (his note), three amounts of drip.
 - Luma fade and flicker mask (Maybes): faster/slower, subtler.
 - Zoom through (Keep): pushed further.
Reuses the round 1 helpers. Writes output/style_lab/r2/<id>_full.mp4 / _prev.mp4.

    python3 style-lab/round2/build.py [logo luma flicker zoom]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r1", HERE.parent / "round1" / "build.py")
r1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r1)
W, H, FPS = r1.W, r1.H, r1.FPS
r1.OUT = r1.ROOT / "output" / "style_lab" / "r2"
r1.TMP = r1.OUT / "tmp"


def raw(span, name):
    return r1.frames(r1.clip(span, name + "_raw", grade=False))


# ---------------- logo with real drips ----------------
def drip_tips(alpha: np.ndarray, n: int):
    """Ends of the logo's drips (halo, letters, tail): a bottom edge that hangs from a narrow stem
    and has nothing lower right next to it."""
    op = alpha > 0.5
    edge = op & ~np.roll(op, -1, 0)
    ys, xs = np.nonzero(edge)
    cand = []
    for y, x in zip(ys, xs):
        if y < 20 or y > H - 30:
            continue
        row = op[y - 14]
        if not row[x]:
            continue
        l = x
        while l > 0 and row[l - 1]:
            l -= 1
        r = x
        while r < W - 1 and row[r + 1]:
            r += 1
        if r - l > 44:                     # too wide to be a drip stem
            continue
        near = (np.abs(xs - x) <= 22) & (ys > y) & (ys <= y + 30)
        if near.any():
            continue
        cand.append((y, x, r - l + 1))
    cand.sort(key=lambda c: -c[0])
    tips = []
    for y, x, w in cand:
        if all(abs(x - tx) > 26 or abs(y - ty) > 40 for tx, ty, _ in tips):
            tips.append((int(x), int(y), int(w)))
    rng = np.random.default_rng(5)
    rng.shuffle(tips)
    return tips[:n]


def drip_layer(tips, k, rng_phase, period, length, drops=True):
    """White drips at time k: each runs down from its tip, a drop swells, lets go and falls."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    t_s = k / FPS
    for (x, y, w), ph in zip(tips, rng_phase):
        w = min(w, 26)
        if drops:
            c = ((t_s + ph) % period) / period
            run = length * min(1, c / 0.7) ** 1.6                    # drip stretches down
            r = w * (0.35 + 0.35 * min(1, c / 0.7))                # bead at the end swells
            if c < 0.7:
                d.rounded_rectangle((x - w * 0.32, y - 6, x + w * 0.32, y + run), radius=w * 0.3, fill="white")
                d.ellipse((x - r, y + run - r, x + r, y + run + r), fill="white")
            else:                                                   # lets go: the drop falls, the drip pulls back
                f = (c - 0.7) / 0.3
                back = length * (1 - f) ** 2
                d.rounded_rectangle((x - w * 0.3, y - 6, x + w * 0.3, y + back * 0.6), radius=w * 0.3, fill="white")
                fall = y + length + 1400 * (f * period * 0.3) ** 2
                d.ellipse((x - r * 0.9, fall - r * 1.2, x + r * 0.9, fall + r * 1.2),
                          fill=(255, 255, 255, int(255 * (1 - f * 0.6))))
        else:                                                       # wet paint: drips creep down and stay
            run = length * min(1, max(0, t_s - ph * 0.3) / 2.6) ** 0.7
            r = w * 0.55
            d.rounded_rectangle((x - w * 0.32, y - 6, x + w * 0.32, y + run), radius=w * 0.3, fill="white")
            d.ellipse((x - r, y + run - r, x + r, y + run + r), fill="white")
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(im, np.float32) / 255


def logo_cards():
    n = int(3.5 * FPS)
    lay, glow = r1.logo_layers()
    bgf = raw((44.0, n / FPS + 0.2), "logo_bg")[:n]
    bg = [np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)),
                     np.float32) / 255 * 0.35 for f in bgf]
    pat = [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1] + [1] * n            # the locked flicker-on
    clicks = [k / FPS for k in range(n) if pat[k] and (k == 0 or not pat[k - 1])]
    rng = np.random.default_rng(11)
    for cid, ntips, period, length, drops, desc in (
            ("r2-l1", 6, 2.4, 90, True, "slow"), ("r2-l2", 14, 1.7, 150, True, "heavy"),
            ("r2-l3", 14, 0, 170, False, "wet")):
        tips = drip_tips(lay[..., 3], ntips)
        ph = rng.uniform(0, max(period, 1), len(tips))
        out = []
        for k in range(n):
            a = pat[k]
            f = r1.over(bg[k], lay, a, glow, 0.6 * a)
            if a and k >= 14:
                dl = drip_layer(tips, k - 14, ph, period, length, drops)
                f = r1.over(f, dl, 1.0)
            out.append(f)
        p = r1.TMP / f"{cid}.mp4"
        r1.write(out, p)
        r1.finish(p, cid, [("click", c, -10) for c in clicks] + [("crackle", 0.0, -14)])


# ---------------- luma fade: faster / slower ----------------
def luma(cid, n):
    A, B = raw(r1.A_CURL, "a_curl"), raw(r1.B_STAND, "b_stand")
    out = list(A[:-n])
    for k in range(n):
        t = (k + 1) / n
        a = A[len(A) - n + k]
        lum = a.mean(-1, keepdims=True)
        blown = np.clip(a + t * 1.6 * np.clip(lum - 0.25, 0, 1) + t * 0.35, 0, 1)
        b = np.clip(B[k] + (1 - t) * 0.9, 0, 1)
        out.append(blown * (1 - t ** 2) + b * t ** 2)
    out += list(B[n:])
    p = r1.TMP / f"{cid}.mp4"
    r1.write(out, p)
    cut = (len(A) - n) / FPS
    r1.finish(p, cid, [("riser", cut + n / FPS - 1.2, -8), ("whoosh", cut + n / FPS - 0.25, -10)])


# ---------------- flicker mask: subtler / quicker ----------------
def warm_leak(k, n, rng):
    x = np.linspace(0, 1, W)[None, :, None]
    cols = [np.array([1.0, 0.45, 0.08]), np.array([1.0, 0.7, 0.3])]
    img = np.zeros((1, W, 3), np.float32)
    for i, c in enumerate(cols):
        img += c * np.exp(-((x - (-0.2 + 1.4 * (k / n) + 0.25 * i)) / 0.14) ** 2)
    return np.repeat(img, H, 0) * (0.45 + 0.35 * rng.random())


def flicker(cid, n, leak, on, gain):
    A, B = raw(r1.B_STAND, "b_stand"), raw(r1.C_CABLE, "c_cable")
    rng = np.random.default_rng(7)
    mid = n // 2
    out, clicks = list(A[:-mid]), []
    for k in range(n):
        base = A[len(A) - mid + k] if k < mid else B[k - mid]
        f = r1.screen(base, leak(k, n, rng) * gain) if on[k] else base * 0.8
        if on[k] and (k == 0 or not on[k - 1]):
            clicks.append(len(out) / FPS)
        out.append(f)
    out += list(B[n - mid:])
    p = r1.TMP / f"{cid}.mp4"
    r1.write(out, p)
    r1.finish(p, cid, [("crackle", (len(A) - mid) / FPS - 0.2, -10)] + [("click", c, -12) for c in clicks])


# ---------------- zoom through: pushed further ----------------
def zoom(cid, src_a, an, cx, cy, n, blur):
    A, B = raw(src_a, an), raw(r1.D_BACK, "d_back")
    out = list(A[:-n])
    for k in range(n):
        t = ((k + 1) / n) ** 2
        z = 1 + 5 * t
        a = Image.fromarray((A[len(A) - n + k] * 255).astype(np.uint8))
        cw, ch = W / z, H / z
        a = a.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H))
        f = np.asarray(a, np.float32) / 255
        if blur:   # radial zoom blur: average a few slightly bigger copies
            acc, m = f.copy(), 1
            for s in (1.03, 1.06, 1.1)[: 1 + int(3 * t)]:
                im = a.resize((int(W * s), int(H * s)))
                l, tp = (im.width - W) // 2, (im.height - H) // 2
                acc += np.asarray(im.crop((l, tp, l + W, tp + H)), np.float32) / 255
                m += 1
            f = acc / m
        out.append(f * (1 - 0.8 * t))
    for k in range(8):
        out.append(B[k] * (k + 1) / 8)
    out += list(B[8:])
    p = r1.TMP / f"{cid}.mp4"
    r1.write(out, p)
    cut = len(A) / FPS
    r1.finish(p, cid, [("whoosh", cut - 0.45, -8), ("impact", cut, -6)])


STEPS = {
    "logo": logo_cards,
    "luma": lambda: (luma("r2-x1", 6), luma("r2-x2", 20)),
    "flicker": lambda: (flicker("r2-x3", 14, warm_leak, [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0], 0.6),
                        flicker("r2-x4", 8, r1.leak_frame, [1, 0, 1, 1, 0, 1, 1, 0], 0.9)),
    "zoom": lambda: (zoom("r2-x5", r1.B_STAND, "b_stand", W * 0.5, H * 0.52, 10, True),
                     zoom("r2-x6", r1.A_CURL, "a_curl", W * 0.8, H * 0.85, 6, False)),
}

if __name__ == "__main__":
    r1.TMP.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or STEPS:
        STEPS[name]()
