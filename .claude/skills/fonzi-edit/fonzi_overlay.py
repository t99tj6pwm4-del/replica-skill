#!/usr/bin/env python3
"""Motion graphics for /fonzi-edit: title card, progress HUD, lower thirds, viewfinder
corners, tracked callouts, kinetic captions, badges and the save-this end card.

Needs Pillow, numpy, opencv (opencv-python-headless) and ffmpeg. Used by fonzi_recipe.py;
the plan it reads is built from the recipe (see fonzi_recipe.py).
"""

import functools
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
YEL = (255, 200, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


@functools.lru_cache(maxsize=64)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def anton(size):
    return font("Anton-Regular.ttf", size)


def mont(size, heavy=True):
    return font("Montserrat-ExtraBold.ttf" if heavy else "Montserrat-Bold.ttf", size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def window(t, t0, t1, fin=0.25, fout=0.25):
    """0..1 visibility of something shown from t0 to t1."""
    if t < t0 or t > t1:
        return 0.0
    return min(clamp((t - t0) / fin) if fin else 1.0, clamp((t1 - t) / fout) if fout else 1.0)


def rgba(color, a):
    return (color[0], color[1], color[2], int(255 * clamp(a)))


def track_width(text, f, track):
    return sum(f.getlength(c) + track for c in text) - track if text else 0


def draw_tracked(d, xy, text, f, fill, track=0):
    x, y = xy
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track
    return x


# ---------- elements ----------

def progress(d, t, groups):
    """Segmented bar across the top, one segment per exercise, plus its name."""
    if not groups:
        return
    n, x0, x1, gap, y = len(groups), 48, W - 48, 10, 56
    seg = (x1 - x0 - gap * (n - 1)) / n
    current = None
    for i, g in enumerate(groups):
        a = x0 + i * (seg + gap)
        d.rounded_rectangle((a, y, a + seg, y + 6), 3, fill=(255, 255, 255, 70))
        frac = clamp((t - g["start"]) / max(0.01, g["end"] - g["start"]))
        if frac > 0:
            d.rounded_rectangle((a, y, a + seg * frac, y + 6), 3, fill=rgba(YEL, 1))
        if g["start"] <= t < g["end"]:
            current = g["name"]
    if current:
        draw_tracked(d, (48, 76), current, mont(22), (255, 255, 255, 235), 4)


def title_card(layer, t, plan):
    tt = plan.get("title_seconds", 2.7)
    if t > tt + 0.05 or not plan.get("title"):
        return
    a = window(t, 0, tt, 0.05, 0.35)
    d0 = ImageDraw.Draw(layer)
    d0.rectangle((0, 0, W, H), fill=rgba(BLACK, 0.55 * a))
    lines = plan["title"]
    block = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(block)
    size = 235
    y = 600
    sx = 0
    d.polygon([(0, y - 70), (560, y - 118), (560, y - 100), (0, y - 52)], fill=rgba(YEL, 1))
    d.polygon([(0, y - 40), (440, y - 78), (440, y - 70), (0, y - 32)], fill=rgba(YEL, 1))
    for i, line in enumerate(lines):
        last = i == len(lines) - 1
        e = ease_out((t - 0.08 * i) / 0.45)
        f = anton(size)
        d.text((70 - (1 - e) * 900, y + i * 215), line, font=f,
               fill=rgba(YEL if last else WHITE, 1))
    sub = plan.get("subtitle", "")
    if sub:
        e = ease_out((t - 0.35) / 0.4)
        f = mont(40)
        tw = track_width(sub, f, 2)
        ty = y + len(lines) * 215 + 95
        d.rounded_rectangle((70 - (1 - e) * 900, ty, 70 + tw + 50 - (1 - e) * 900, ty + 74), 8,
                            fill=rgba(YEL, 1))
        draw_tracked(d, (95 - (1 - e) * 900, ty + 14), sub, f, rgba(BLACK, 1), 2)
    block = block.rotate(7, center=(60, 900), resample=Image.BICUBIC)
    if a < 1:
        block.putalpha(block.getchannel("A").point(lambda v: int(v * a)))
    layer.alpha_composite(block)


def lower_third(d, t, clip, n_groups):
    if not clip.get("group") or not clip.get("first_of_group"):
        return
    t0 = clip["start"] + 0.35
    a = window(t, t0, t0 + 2.9, 0.3, 0.25)
    if a <= 0:
        return
    e = ease_out((t - t0) / 0.35)
    ox = -(1 - e) * 520
    small = "EXERCISE %02d / %02d" % (clip["group_index"], n_groups)
    name = clip["group"]
    wide = max(track_width(name, anton(84), 0), track_width(small, mont(26), 4)) + 86
    x, y, h = 48 + ox, 1340, 176
    d.rounded_rectangle((x, y, x + wide + 20, y + h), 8, fill=(0, 0, 0, int(150 * a)))
    d.rectangle((x, y, x + 9, y + h), fill=rgba(YEL, a))
    draw_tracked(d, (x + 36, y + 24), small, mont(26), rgba(YEL, a), 4)
    d.text((x + 36, y + 52), name, font=anton(84), fill=rgba(WHITE, a))


def brackets(d, t, t0, t1):
    a = window(t, t0, t1, 0.2, 0.2)
    if a <= 0:
        return
    grow = ease_out((t - t0) / 0.3)
    inset = 18 * (1 - grow)
    x0, y0, x1, y1, L, w = 42 + inset, 300 + inset, W - 42 - inset, 1560 - inset, 66, 7
    c = rgba(YEL, a)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * L, cy), fill=c, width=w)
        d.line((cx, cy, cx, cy + sy * L), fill=c, width=w)


def pill(d, x, y, text, a, dot, right=False):
    f = mont(26)
    tw = track_width(text, f, 2)
    w = tw + 78
    if right:
        x = x - w
    d.rounded_rectangle((x, y, x + w, y + 56), 12, fill=(0, 0, 0, int(110 * a)),
                        outline=rgba(YEL, a), width=3)
    d.ellipse((x + 20, y + 21, x + 34, y + 35), fill=rgba(dot, a))
    draw_tracked(d, (x + 48, y + 12), text, f, rgba(WHITE, a), 2)


def callout(d, t, c, pos):
    t0, t1 = c["abs_at"], c["abs_at"] + c["dur"]
    a = window(t, t0, t1, 0.15, 0.25)
    if a <= 0:
        return
    x, y = pos
    x, y = x * W, y * H
    pop = ease_back((t - t0) / 0.28)
    r = 46 * pop
    d.ellipse((x - r, y - r, x + r, y + r), outline=rgba(YEL, a), width=6)
    d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=rgba(YEL, a))
    f = anton(50)
    label = c["label"]
    tw = f.getlength(label) + 52
    th = 78
    direction = c.get("dir", "ur")
    if direction == "ur" and x + 100 + tw > W - 36:
        direction = "ul"
    if direction == "ul" and x - 100 - tw < 36:
        direction = "ur"
    sx = 1 if direction == "ur" else -1
    lx, ly = x + sx * 100, y - 100
    ly = max(ly, 340 + th)
    g = ease_out((t - t0 - 0.1) / 0.25)
    ex = x + sx * (r * 0.72) + (lx - x - sx * r * 0.72) * g
    ey = y - r * 0.72 + (ly - y + r * 0.72) * g
    d.line((x + sx * r * 0.72, y - r * 0.72, ex, ey), fill=rgba(YEL, a), width=5)
    if g > 0.6:
        ta = a * clamp((g - 0.6) / 0.4)
        bx0 = lx if sx == 1 else lx - tw
        d.rounded_rectangle((bx0, ly - th, bx0 + tw, ly), 12, fill=rgba(YEL, ta))
        d.text((bx0 + 26, ly - th + 4), label, font=f, fill=rgba(BLACK, ta))


def caption(layer, t, cap):
    t0, t1 = cap["abs_at"], cap["abs_at"] + cap["dur"]
    a = window(t, t0, t1, 0.0, 0.22)
    if a <= 0:
        return
    words = cap["text"].split()
    hi = set(cap.get("hi", [len(words) - 1]))
    size = 132
    gap = 30
    total = sum(anton(size).getlength(w) for w in words) + gap * (len(words) - 1)
    if total > 940:
        size = int(size * 940 / total)
        total = sum(anton(size).getlength(w) for w in words) + gap * (len(words) - 1)
    f = anton(size)
    x = (W - total) / 2
    base_y = cap.get("y", 1380)
    for i, w in enumerate(words):
        wt = t - (t0 + 0.13 * i)
        if wt < 0:
            x += f.getlength(w) + gap
            continue
        s = 0.55 + 0.45 * ease_back(wt / 0.2)
        ww = int(f.getlength(w)) + 24
        sprite = Image.new("RGBA", (ww, int(size * 1.5)), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sprite)
        col = YEL if i in hi else WHITE
        sd.text((12, 8), w, font=f, fill=rgba(col, 1), stroke_width=5, stroke_fill=(0, 0, 0, 215))
        if s != 1.0:
            sprite = sprite.resize((max(1, int(sprite.width * s)), max(1, int(sprite.height * s))),
                                   Image.BILINEAR)
        if a < 1:
            sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * a)))
        layer.alpha_composite(sprite, (int(x - 12 + (ww - sprite.width) / 2),
                                       int(base_y + (size * 1.5 - sprite.height) / 2 - size * 0.4)))
        x += f.getlength(w) + gap


def bookmark(d, cx, cy, a):
    w, h = 124, 170
    x0, y0 = cx - w / 2, cy - h / 2
    outline = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (cx, y0 + h * 0.72), (x0, y0 + h)]
    d.line(outline + [outline[0]], fill=rgba(WHITE, a), width=9, joint="curve")
    inner = [(x0 + 6, y0 + h * 0.56), (x0 + w - 6, y0 + h * 0.56), (x0 + w - 6, y0 + h - 14),
             (cx, y0 + h * 0.7), (x0 + 6, y0 + h - 14)]
    d.polygon(inner, fill=rgba(YEL, a))


def end_card(layer, t, total, plan):
    dur = plan.get("end_seconds", 3.4)
    t0 = total - dur
    a = window(t, t0, total + 1, 0.3, 0)
    if a <= 0:
        return
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, W, H), fill=rgba(BLACK, 0.62 * a))
    bm = ease_back((t - t0 - 0.15) / 0.35)
    bookmark(d, W // 2, 640 - (1 - clamp(bm)) * 30, a * clamp(bm))
    big = plan.get("cta", "SAVE THIS").split()
    sizes = [150, 230]
    fs = [anton(sizes[min(i, 1)]) for i in range(len(big))]
    gap = 34
    total_w = sum(f.getlength(w) for f, w in zip(fs, big)) + gap * (len(big) - 1)
    x = (W - total_w) / 2
    for i, (f, w) in enumerate(zip(fs, big)):
        wt = t - (t0 + 0.4 + 0.18 * i)
        if wt >= 0:
            s = 0.5 + 0.5 * ease_back(wt / 0.25)
            sp = Image.new("RGBA", (int(f.getlength(w)) + 20, 360), (0, 0, 0, 0))
            ImageDraw.Draw(sp).text((10, 0), w, font=f,
                                    fill=rgba(YEL if i == len(big) - 1 else WHITE, 1))
            sp = sp.resize((int(sp.width * s), int(sp.height * s)), Image.BILINEAR)
            layer.alpha_composite(sp, (int(x - 10 + (f.getlength(w) + 20 - sp.width) / 2),
                                       int(800 + (360 - sp.height) / 2)))
        x += f.getlength(w) + gap
    sub = plan.get("cta_sub", "")
    e = ease_out((t - t0 - 0.9) / 0.3)
    if sub and e > 0:
        f = mont(36)
        tw = track_width(sub, f, 4)
        draw_tracked(d, ((W - tw) / 2, 1130), sub, f, rgba(WHITE, e), 4)
    handle = plan.get("handle", "")
    if handle and e > 0:
        f = mont(34)
        tw = track_width(handle, f, 2)
        d.rounded_rectangle(((W - tw) / 2 - 34, 1215, (W + tw) / 2 + 34, 1291), 38, fill=rgba(YEL, e))
        draw_tracked(d, ((W - tw) / 2, 1232), handle, f, rgba(BLACK, e), 2)


# ---------- frame ----------

def draw_frame(t, plan, tracks):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total = plan["total"]
    ending = t > total - plan.get("end_seconds", 3.4)
    if not ending:
        progress(d, t, plan["groups"])
        for clip in plan["clips"]:
            if clip["start"] - 0.01 <= t < clip["end"]:
                lower_third(d, t, clip, len(plan["groups"]))
                for key, (dx, dy) in (("bracket", (0, 0)),):
                    b = clip.get("bracket")
                    if b:
                        brackets(d, t, clip["start"] + b[0], clip["start"] + b[0] + b[1])
                for cam in clip.get("cams", []):
                    a = window(t, clip["start"] + cam["at"], clip["start"] + cam["at"] + cam["dur"], 0.15, 0.2)
                    if a > 0:
                        pill(d, 48, 236, cam["label"], a, (235, 50, 50))
                if clip.get("slow"):
                    pill(d, W - 48, 236, "SLOW-MO %gx" % clip["slow"], 1.0, YEL, right=True)
        for i, c in enumerate(plan["callouts"]):
            pos = tracks.get(i)
            if pos is None:
                continue
            k = int(round((t - c["abs_at"]) * FPS))
            k = max(0, min(len(pos) - 1, k))
            callout(d, t, c, pos[k])
        for cap in plan["captions"]:
            caption(layer, t, cap)
        title_card(layer, t, plan)
    else:
        end_card(layer, t, total, plan)
    return layer


# ---------- tracking ----------

def track_callouts(base, callouts, scale=0.5):
    """Follow each callout's anchor with optical flow. Returns {index: [(x, y) per frame]}."""
    import cv2
    out = {}
    w, h = int(W * scale), int(H * scale)
    for idx, c in enumerate(callouts):
        n = int(c["dur"] * FPS) + 2
        cmd = ["ffmpeg", "-v", "error", "-ss", "%.3f" % c["abs_at"], "-i", base, "-frames:v", str(n),
               "-vf", "scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"]
        raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
        frames = [np.frombuffer(raw[i * w * h:(i + 1) * w * h], np.uint8).reshape(h, w)
                  for i in range(len(raw) // (w * h))]
        ax, ay = c["anchor"][0] * w, c["anchor"][1] * h
        positions = [(ax / w, ay / h)]
        if len(frames) > 1:
            mask = np.zeros((h, w), np.uint8)
            cv2.circle(mask, (int(ax), int(ay)), 55, 255, -1)
            pts = cv2.goodFeaturesToTrack(frames[0], 12, 0.01, 6, mask=mask)
            cx, cy = ax, ay
            sx, sy = ax, ay
            for i in range(1, len(frames)):
                if pts is not None and len(pts) >= 2:
                    nxt, st, _ = cv2.calcOpticalFlowPyrLK(frames[i - 1], frames[i], pts, None,
                                                          winSize=(31, 31), maxLevel=3)
                    good = st.reshape(-1) == 1
                    if good.sum() >= 2:
                        move = np.median(nxt[good].reshape(-1, 2) - pts[good].reshape(-1, 2), axis=0)
                        if np.hypot(*move) < 60 * scale:       # a jump this big is a cut, hold still
                            cx += move[0]
                            cy += move[1]
                        pts = nxt[good].reshape(-1, 1, 2)
                    else:
                        pts = None
                if pts is None or len(pts) < 5:
                    m = np.zeros((h, w), np.uint8)
                    cv2.circle(m, (int(clamp(cx, 0, w - 1)), int(clamp(cy, 0, h - 1))), 55, 255, -1)
                    pts = cv2.goodFeaturesToTrack(frames[i], 12, 0.01, 6, mask=m)
                sx += (cx - sx) * 0.6                       # light smoothing
                sy += (cy - sy) * 0.6
                positions.append((clamp(sx / w, 0.02, 0.98), clamp(sy / h, 0.02, 0.98)))
        out[idx] = positions
    return out


# ---------- compose ----------

def compose(base, out, plan, tracks, total_frames):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", base,
                            "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    size = W * H * 3
    i = 0
    while i < total_frames:
        buf = dec.stdout.read(size)
        while buf and len(buf) < size:
            more = dec.stdout.read(size - len(buf))
            if not more:
                break
            buf += more
        if len(buf) < size:
            break
        frame = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1).convert("RGBA")
        frame.alpha_composite(draw_frame(i / FPS, plan, tracks))
        enc.stdin.write(frame.convert("RGB").tobytes())
        i += 1
    enc.stdin.close()
    dec.stdout.close()
    if enc.wait() != 0:
        sys.exit("overlay encode failed")
    dec.wait()
    return i
