#!/usr/bin/env python3
"""Style Lab round 4: cut out + punch in, background = the ORIGINAL frame, flickering (his round 3 note).
He stays steady in front; behind him the frozen original background flickers. Only what it flickers to changes.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r3", HERE.parent / "round3" / "build.py")
r3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r3)
r1 = r3.r1
W, H, FPS = r1.W, r1.H, r1.FPS
r1.OUT = r1.ROOT / "output" / "style_lab" / "r4"
r1.TMP = r1.OUT / "tmp"

PATTERN = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0]   # 1 = flicker frame, irregular like a strobe


def build(cid, kind):
    A = r1.frames(r1.clip(r1.B_STAND, "b_stand_raw", grade=False))
    B = r1.frames(r1.clip(r1.D_BACK, "d_back_raw", grade=False))
    F = A[-1]
    session, _ = r3.lt.cut_session()
    m = np.asarray(r3.lt.person_mask(session, Image.fromarray((F * 255).astype(np.uint8))).filter(
        ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
    ys, xs = np.nonzero(m[..., 0] > 0.5)
    cx, cy = float(xs.mean()), float(np.percentile(ys, 25))
    alt = {"white": np.ones_like(F),
           "black": np.zeros_like(F),
           "blown": np.clip(F * 1.8 + 0.25, 0, 1)}[kind]      # the same background, overexposed
    clicks, out = [], list(A)

    def frame(k):
        on = PATTERN[k % len(PATTERN)]
        bg = alt if on else F
        if on and (k == 0 or not PATTERN[(k - 1) % len(PATTERN)]):
            clicks.append(len(out) / FPS)
        return m * F + (1 - m) * bg

    k = 0
    for i in range(10):                                   # cut out, hold, background flickering
        out.append(r3.zoom(frame(k), 1 + 0.03 * (i + 1) / 10, W / 2, H / 2))
        k += 1
    shakes = [(18, -12), (-14, 10), (9, -6), (-5, 4), (0, 0)]
    pin = len(out)
    for i in range(5):                                    # punch in, still flickering
        z = 1.03 + 0.37 * (1 - (1 - (i + 1) / 5) ** 3)
        out.append(r3.zoom(frame(k), z, W / 2 + (cx - W / 2) * (i + 1) / 5, H / 2 + (cy - H / 2) * (i + 1) / 5,
                           *shakes[i]))
        k += 1
    out += list(B)
    p = r1.TMP / f"{cid}.mp4"
    r1.write(out, p)
    r1.finish(p, cid, [("pop", len(A) / FPS, -6), ("impact", pin / FPS - 0.02, -3),
                       ("whoosh", (pin + 5) / FPS - 0.2, -10)] + [("click", c, -14) for c in clicks])


if __name__ == "__main__":
    r1.TMP.mkdir(parents=True, exist_ok=True)
    for cid, kind in (("r4-c1", "white"), ("r4-c2", "black"), ("r4-c3", "blown")):
        build(cid, kind)
