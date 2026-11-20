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

All inputs are scaled to 1080x1920 @ 30 fps; footage audio is dropped (the song goes on later), each output
carries only our own sfx (sfx/*.wav), so mix it under the song or keep picture only.
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
SFX = ROOT / "sfx"
LOGO = ROOT / "brand" / "fonzi_logo.png"


# ---------- io ----------
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
        p.stdin.write((np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg failed writing the picture")
    dur = len(fr) / FPS
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", tmp, "-f", "lavfi", "-t", f"{dur:.3f}", "-i",
           "anullsrc=r=48000:cl=stereo"]
    parts, labels = [], ["[1:a]"]
    for k, (name, at, db) in enumerate(sounds):
        cmd += ["-i", SFX / f"{name}.wav"]
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
    write(fr, out, [("impact", at - 0.02, -3)])


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
    write(res, out, [("whoosh", cut - 0.45, -8), ("impact", cut, -6)])


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
    write(res, out, [("pop", len(A) / FPS, -6), ("impact", pin / FPS - 0.02, -3),
                     ("whoosh", (pin + 5) / FPS - 0.2, -10)] + [("click", c, -14) for c in clicks])


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
    write(res, out, [("click", c, -10) for c in clicks] + [("crackle", 0.0, -14)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snap"); s.add_argument("inp", type=Path); s.add_argument("out", type=Path)
    s.add_argument("--at", type=float, required=True)
    z = sub.add_parser("zoom"); z.add_argument("a", type=Path); z.add_argument("b", type=Path)
    z.add_argument("out", type=Path); z.add_argument("--cx", type=float, default=0.5); z.add_argument("--cy", type=float, default=0.52)
    c = sub.add_parser("cutout"); c.add_argument("a", type=Path); c.add_argument("b", type=Path)
    c.add_argument("out", type=Path); c.add_argument("--to", choices=["black", "white"], default="black")
    lo = sub.add_parser("logo"); lo.add_argument("out", type=Path); lo.add_argument("--bg", type=Path, required=True)
    lo.add_argument("--drips", choices=["slow", "heavy", "wet"], default="heavy"); lo.add_argument("--dur", type=float, default=3.5)
    a = ap.parse_args()
    if a.cmd == "snap":
        snap(a.inp, a.out, a.at)
    elif a.cmd == "zoom":
        zoom_through(a.a, a.b, a.out, a.cx, a.cy)
    elif a.cmd == "cutout":
        cutout(a.a, a.b, a.out, a.to)
    else:
        logo(a.out, a.bg, a.drips, a.dur)
