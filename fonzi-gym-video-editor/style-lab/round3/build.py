#!/usr/bin/env python3
"""Style Lab round 3: "cut out, then punch in" (his round 2 note on the fast luma fade).
The shot freezes, he is cut out of the frame (rembg, same model as the gold titles), holds a beat, then the
camera punches in on him with an impact, hard cut to the next shot. Only what's behind him changes.
Ungraded footage, our own sounds. Writes output/style_lab/r3/<id>_full.mp4 / _prev.mp4.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r1", HERE.parent / "round1" / "build.py")
r1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r1)
W, H, FPS = r1.W, r1.H, r1.FPS
r1.OUT = r1.ROOT / "output" / "style_lab" / "r3"
r1.TMP = r1.OUT / "tmp"
lt = r1.layered_title


def zoom(f, z, cx, cy, dx=0, dy=0):
    im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
    cw, ch = W / z, H / z
    l, t = cx - cw / 2 + dx, cy - ch / 2 + dy
    return np.asarray(im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((W, H), Image.BICUBIC),
                      np.float32) / 255


def build(cid, bg_kind):
    A = r1.frames(r1.clip(r1.B_STAND, "b_stand_raw", grade=False))
    B = r1.frames(r1.clip(r1.D_BACK, "d_back_raw", grade=False))
    F = A[-1]
    session, _ = lt.cut_session()
    m = np.asarray(lt.person_mask(session, Image.fromarray((F * 255).astype(np.uint8))).filter(
        ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
    ys, xs = np.nonzero(m[..., 0] > 0.5)
    cx, cy = float(xs.mean()), float(np.percentile(ys, 25))          # punch toward his chest / face
    if bg_kind == "black":
        bg = np.zeros_like(F)
        ring = None
    elif bg_kind == "outline":
        bg = F * 0.12
        big = np.asarray(Image.fromarray((m[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25)),
                         np.float32)[..., None] / 255
        ring = np.clip(big - m, 0, 1)
    else:   # white flash behind him
        bg = np.ones_like(F)
        ring = None
    cut = m * F + (1 - m) * bg
    if ring is not None:
        cut = cut * (1 - ring) + ring
    out = list(A)
    for k in range(3):                                   # background drops away
        t = (k + 1) / 3
        out.append(F * (1 - t) + cut * t)
    for k in range(7):                                   # hold, slight drift in
        out.append(zoom(cut, 1 + 0.03 * (k + 1) / 7, W / 2, H / 2))
    shakes = [(18, -12), (-14, 10), (9, -6), (-5, 4), (0, 0)]
    pin = len(out)
    for k in range(5):                                   # punch in on him
        z = 1.03 + 0.37 * (1 - (1 - (k + 1) / 5) ** 3)
        f = zoom(cut, z, W / 2 + (cx - W / 2) * (k + 1) / 5, H / 2 + (cy - H / 2) * (k + 1) / 5, *shakes[k])
        if k == 0:
            f = np.clip(f + 0.35, 0, 1)
        out.append(f)
    out += list(B)
    p = r1.TMP / f"{cid}.mp4"
    r1.write(out, p)
    t_cut = len(A) / FPS
    r1.finish(p, cid, [("pop", t_cut, -6), ("impact", pin / FPS - 0.02, -3), ("whoosh", (pin + 5) / FPS - 0.2, -10)])


if __name__ == "__main__":
    r1.TMP.mkdir(parents=True, exist_ok=True)
    for cid, kind in (("r3-c1", "black"), ("r3-c2", "outline"), ("r3-c3", "white")):
        build(cid, kind)
