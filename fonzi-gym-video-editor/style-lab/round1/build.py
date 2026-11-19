#!/usr/bin/env python3
"""Style Lab round 1: grade strengths, gold name title, transitions, logo end card.
All picture from Alfonso's own After Hours footage (input/icloud_0efbfJGz.mov), footage audio muted,
only our own synthesised sounds (sfx/). Writes output/style_lab/r1/<id>_full.mp4 and <id>_prev.mp4.

    python3 style-lab/round1/build.py [ids...]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import film_grade  # noqa: E402
import layered_title  # noqa: E402

SRC = ROOT / "input" / "icloud_0efbfJGz.mov"
OUT = ROOT / "output" / "style_lab" / "r1"
TMP = OUT / "tmp"
SFX = ROOT / "sfx"
W, H, FPS = 1080, 1920, 30
LOGO = ROOT / "brand" / "fonzi_logo.png"

# pieces of his footage (seconds in the source)
CURL = (8.0, 3.0)        # seated curl, face + tattoo: grade comparison
STAND = (36.0, 4.5)      # standing, YLA tank: name title
A_CURL = (4.0, 1.6)
B_STAND = (30.0, 1.6)
C_CABLE = (140.0, 1.6)
D_BACK = (104.0, 1.6)


def sh(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def clip(span, name, strength="medium", grade=True) -> Path:
    """A 1080x1920 30fps piece of the source, graded (or not), silent audio track added."""
    out = TMP / f"{name}.mp4"
    if out.exists():
        return out
    ss, t = span
    if grade:
        fc = film_grade.filter_chain(strength)
    else:
        fc = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p[v]"
    sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-i", SRC, "-f", "lavfi", "-i",
        "anullsrc=r=48000:cl=stereo", "-t", f"{t}", "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-shortest", out])
    return out


def frames(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32) / 255


def write(fr, out: Path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                          "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for f in fr:
        p.stdin.write((np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit(f"ffmpeg failed writing {out}")


def finish(pic: Path, cid: str, sounds: list[tuple[str, float, float]]):
    """Mux our sounds [(file, start_s, gain_db)] under the picture; write full + small muted preview."""
    full, prev = OUT / f"{cid}_full.mp4", OUT / f"{cid}_prev.mp4"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(pic)], capture_output=True, text=True).stdout)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", pic, "-f", "lavfi", "-t", f"{dur:.3f}", "-i",
           "anullsrc=r=48000:cl=stereo"]
    parts, labels = [], ["[1:a]"]
    for k, (name, at, db) in enumerate(sounds):
        cmd += ["-i", SFX / f"{name}.wav"]
        ms = max(0, int(at * 1000))
        parts.append(f"[{k + 2}:a]volume={db}dB,adelay={ms}|{ms}[s{k}]")
        labels.append(f"[s{k}]")
    fc = ";".join(parts + [f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
                           f"alimiter=limit=0.89[a]"])
    sh(cmd + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "19",
              "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
              full])
    sh(["ffmpeg", "-v", "error", "-y", "-i", full, "-an", "-vf", "scale=360:640,fps=30", "-c:v", "libx264",
        "-crf", "30", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", prev])
    print(f"{cid}: {dur:.2f}s  full {full.stat().st_size // 1024} KB  preview {prev.stat().st_size // 1024} KB")


# ---------------- grade ----------------
def grade_cards():
    finish(clip(CURL, "curl_raw", grade=False), "r1-g0", [])
    for cid, s in (("r1-g1", "light"), ("r1-g2", "medium"), ("r1-g3", "heavy")):
        finish(clip(CURL, f"curl_{s}", s), cid, [])


# ---------------- gold name title ----------------
def punch_in(src: Path, at: float, out: Path):
    """Hard snap on the title: 2-frame white flash, zoom 1.08 -> 1 over 6 frames, small shake."""
    fr = frames(src)
    k0 = int(round(at * FPS))
    img = []
    for k, f in enumerate(fr):
        d = k - k0
        if 0 <= d < 8:
            z = 1 + 0.08 * (1 - d / 7) ** 2
            dx, dy = [(14, -10), (-12, 8), (8, -6), (-5, 4), (3, -2), (0, 0), (0, 0), (0, 0)][d]
            im = Image.fromarray((f * 255).astype(np.uint8)).resize((int(W * z), int(H * z)), Image.BICUBIC)
            l, t = (im.width - W) // 2 + dx, (im.height - H) // 2 + dy
            f = np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255
            if d < 2:
                f = f + (0.55 if d == 0 else 0.25)
        img.append(f)
    write(img, out)


def title_cards():
    at, dur = 0.4, 3.6
    raw = clip(STAND, "stand_raw", grade=False)
    graded = clip(STAND, "stand_medium")
    clean = TMP / "title_clean.mp4"
    if not clean.exists():
        layered_title.build(graded, clean, at, dur, "FONZI", "STAYS FIT", "this is", tag="_sl")
    finish(clean, "r1-t1", [("whoosh", at - 0.25, -6)])
    under = TMP / "title_under.mp4"
    if not under.exists():
        pre = TMP / "title_raw.mp4"
        layered_title.build(raw, pre, at, dur, "FONZI", "STAYS FIT", "this is", tag="_sl")
        film_grade.grade(pre, under, "medium")
    finish(under, "r1-t2", [("whoosh", at - 0.25, -6)])
    snap = TMP / "title_snap.mp4"
    punch_in(clean, at, snap)
    finish(snap, "r1-t3", [("impact", at - 0.02, -3)])


# ---------------- transitions ----------------
def pair(a, b, an, bn):
    return frames(clip(a, an)), frames(clip(b, bn))


def screen(base, layer):
    return 1 - (1 - base) * (1 - layer)


def tr_luma():
    A, B = pair(A_CURL, B_STAND, "a_curl", "b_stand")
    n = 12   # 0.4 s: highlights blow first, then dissolve through white
    out = list(A[:-n])
    for k in range(n):
        t = (k + 1) / n
        a = A[len(A) - n + k]
        lum = a.mean(-1, keepdims=True)
        blown = np.clip(a + t * 1.6 * np.clip(lum - 0.25, 0, 1) + t * 0.35, 0, 1)
        b = np.clip(B[k] + (1 - t) * 0.9, 0, 1)
        out.append(blown * (1 - t ** 2) + b * t ** 2)
    out += list(B[n:])
    p = TMP / "x_luma.mp4"
    write(out, p)
    cut = (len(A) - n) / FPS
    finish(p, "r1-x1", [("riser", cut - 1.0, -8), ("whoosh", cut + 0.15, -10)])


def leak_frame(k, n, rng):
    """Our own light leak: soft vertical magenta / orange / purple bands drifting across, with sprocket holes."""
    x = np.linspace(0, 1, W)[None, :, None]
    cols = [np.array([1.0, 0.2, 0.6]), np.array([1.0, 0.55, 0.1]), np.array([0.55, 0.2, 1.0])]
    img = np.zeros((1, W, 3), np.float32)
    for i, c in enumerate(cols):
        cx = -0.3 + 1.6 * (k / n) + 0.22 * i
        img += c * np.exp(-((x - cx) / 0.09) ** 2)
    img = np.repeat(img, H, 0)
    img[:, :int(W * 0.035)] *= 0.1   # film edge
    for y in range(40, H, 150):
        img[y:y + 70, 8:28] = 0.9
    return img * (0.5 + 0.5 * rng.random())


def tr_flicker():
    A, B = pair(B_STAND, C_CABLE, "b_stand", "c_cable")
    rng = np.random.default_rng(7)
    n, mid = 14, 7
    out = list(A[:-mid])
    on = [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0]
    clicks = []
    for k in range(n):
        base = A[len(A) - mid + k] if k < mid else B[k - mid]
        f = screen(base, leak_frame(k, n, rng) * 0.9) if on[k] else base * 0.75
        if on[k] and (k == 0 or not on[k - 1]):
            clicks.append((len(out)) / FPS)
        out.append(f)
    out += list(B[n - mid:])
    p = TMP / "x_flicker.mp4"
    write(out, p)
    cut = (len(A) - mid) / FPS
    finish(p, "r1-x2", [("crackle", cut - 0.25, -8)] + [("click", c, -12) for c in clicks])


def tr_burn():
    A, B = pair(C_CABLE, D_BACK, "c_cable", "d_back")
    n, mid = 16, 8
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(3)
    out = list(A[:-mid])
    for k in range(n):
        t = k / (n - 1)
        r = 0.15 + 1.5 * np.sin(np.pi * t) ** 0.8              # grows to cover the frame, then pulls back
        cx, cy = -0.1 * W, H * (0.45 + 0.1 * np.sin(k))
        d = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H * 0.6) ** 2) / r
        heat = np.clip(1.4 - d, 0, 1)[..., None] ** 1.5
        heat *= 0.9 + 0.2 * rng.random((H // 16 + 1, W // 16 + 1)).repeat(16, 0).repeat(16, 1)[:H, :W, None]
        burn = heat * np.array([1.0, 0.55, 0.15]) + np.clip(heat - 0.6, 0, 1) * 2.0   # orange, white core
        base = A[len(A) - mid + k] if k < mid else B[k - mid]
        out.append(screen(base, np.clip(burn, 0, 1)))
    out += list(B[n - mid:])
    p = TMP / "x_burn.mp4"
    write(out, p)
    cut = (len(A) - mid) / FPS
    finish(p, "r1-x3", [("crackle", cut - 0.3, -6), ("whoosh", cut - 0.2, -10)])


def tr_rise():
    A, B = pair(D_BACK, A_CURL, "d_back", "a_curl")
    n = 9   # 0.3 s: the top clip slides up and off the frame, ease-in, vertical motion blur
    out = list(A[:-n])
    for k in range(n):
        t = ((k + 1) / n) ** 2
        off = int(H * t)
        a = A[len(A) - n + k]
        f = B[k].copy()
        if off < H:
            f[:H - off] = a[off:]
        im = Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(0)) if k == 0 else None
        blur = max(1, int(30 * np.sin(np.pi * (k + 1) / n)))
        f = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).resize((W, H // blur)).resize((W, H))) / 255 \
            if blur > 3 else f
        out.append(np.asarray(f, np.float32))
    out += list(B[n:])
    p = TMP / "x_rise.mp4"
    write(out, p)
    cut = (len(A) - n) / FPS
    finish(p, "r1-x4", [("whoosh", cut - 0.2, -4)])


def tr_zoom():
    A, B = pair(B_STAND, D_BACK, "b_stand", "d_back")
    n = 10   # punch into the black tank top until the frame goes dark, next clip rises out of the dark
    out = list(A[:-n])
    cx, cy = W * 0.5, H * 0.52
    for k in range(n):
        t = ((k + 1) / n) ** 2
        z = 1 + 5 * t
        a = Image.fromarray((A[len(A) - n + k] * 255).astype(np.uint8))
        cw, ch = W / z, H / z
        a = a.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H))
        out.append(np.asarray(a, np.float32) / 255 * (1 - 0.8 * t))
    for k in range(8):
        t = (k + 1) / 8
        out.append(B[k] * t)
    out += list(B[8:])
    p = TMP / "x_zoom.mp4"
    write(out, p)
    cut = (len(A)) / FPS
    finish(p, "r1-x5", [("whoosh", cut - 0.45, -8), ("impact", cut, -6)])


# ---------------- logo end card ----------------
def logo_layers():
    lg = Image.open(LOGO).convert("RGBA")
    s = int(W * 0.78)
    lg = lg.resize((s, s), Image.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(lg, ((W - s) // 2, (H - s) // 2 - 60), lg)
    a = np.asarray(layer, np.float32) / 255
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
    return a, glow


def logo_bg(n):
    bg = frames(clip((44.0, n / FPS + 0.2), "logo_bg"))[:n]
    out = []
    for f in bg:
        im = Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
        out.append(np.asarray(im, np.float32) / 255 * 0.35)
    return out


def over(base, layer, alpha=1.0, glow=None, g=0.0):
    a = layer[..., 3:4] * alpha
    f = base * (1 - a) + layer[..., :3] * a
    if glow is not None and g > 0:
        f = screen(f, glow[..., :3] * glow[..., 3:4] * g)
    return f


def logo_cards():
    n = int(2.6 * FPS)
    lay, glow = logo_layers()
    bg = logo_bg(n)
    ys = np.arange(H)[:, None, None]
    # L1 drip reveal: wipe down from the top with a soft edge, like paint running
    out = []
    for k in range(n):
        t = min(1, k / (0.9 * FPS))
        edge = -200 + (H + 400) * (1 - (1 - t) ** 2)
        m = np.clip((edge - ys) / 120, 0, 1)
        l2 = lay.copy()
        l2[..., 3:4] *= m
        out.append(over(bg[k], l2, 1, glow, 0.35 * t))
    p = TMP / "l_drip.mp4"
    write(out, p)
    finish(p, "r1-l1", [("riser", 0.0, -12), ("whoosh", 0.55, -10)])
    # L2 flicker on: off/on like a sign warming up, then a steady glow
    pat = [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1] + [1] * n
    out, clicks = [], []
    for k in range(n):
        if pat[k] and (k == 0 or not pat[k - 1]):
            clicks.append(k / FPS)
        out.append(over(bg[k], lay, pat[k], glow, 0.6 * pat[k]))
    p = TMP / "l_flicker.mp4"
    write(out, p)
    finish(p, "r1-l2", [("click", c, -10) for c in clicks] + [("crackle", 0.0, -14)])
    # L3 slam: drops in from big, lands at 0.35 s with a shake
    out = []
    land = int(0.35 * FPS)
    for k in range(n):
        if k < land:
            z = 1 + 1.4 * (1 - k / land) ** 2
            im = Image.fromarray((lay * 255).astype(np.uint8))
            im = im.resize((int(W * z), int(H * z)), Image.BICUBIC)
            l, t = (im.width - W) // 2, (im.height - H) // 2
            l2 = np.asarray(im.crop((l, t, l + W, t + H)), np.float32) / 255
            out.append(over(bg[k], l2, k / land))
        else:
            d = k - land
            dx, dy = [(16, -12), (-14, 9), (9, -6), (-5, 4), (2, -2)][d] if d < 5 else (0, 0)
            f = over(bg[k], np.roll(np.roll(lay, dy, 0), dx, 1), 1, glow, 0.4)
            out.append(f + (0.3 if d == 0 else 0))
    p = TMP / "l_slam.mp4"
    write(out, p)
    finish(p, "r1-l3", [("impact", land / FPS - 0.02, -3)])


STEPS = {"grade": grade_cards, "title": title_cards, "luma": tr_luma, "flicker": tr_flicker, "burn": tr_burn,
         "rise": tr_rise, "zoom": tr_zoom, "logo": logo_cards}

if __name__ == "__main__":
    TMP.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or STEPS:
        STEPS[name]()
    print(json.dumps(sorted(p.name for p in OUT.glob("*_prev.mp4"))))
