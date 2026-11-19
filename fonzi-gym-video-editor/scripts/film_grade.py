#!/usr/bin/env python3
"""Fonzi film grade (Style Lab brief, 2026-11-19): Alfonso's 5-step teal & orange film look, built by us.

    python3 scripts/film_grade.py IN.mp4 OUT.mp4 [--strength light|medium|heavy] [--ss S --t T]

Order (his spec, style-lab/GRADE_AND_TRANSITIONS.md):
 1. Rec 709: his iPhone footage is already Rec 709 (log footage is not handled here).
 2. 2383-style print film base (our own curve, no third-party LUT file).
 3. Primaries: warm white balance, exposure, medium-high saturation.
 4. Teal & orange: shadows #093647, mids #1B4E5B, skin/wood stay warm, crushed blacks.
 5. Film effects: halation + glow on bright edges, bleach bypass, grain. Highlights may blow out.
Steps 2-4 are baked into a 3D LUT (.cube, cached in output/work/grade/); step 5 is an ffmpeg filter chain.
Picture only: audio is copied untouched.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, W, WORK, run  # noqa: E402

STRENGTH = {
    #          teal mix, crush, contrast, halation, glow, bleach, grain
    "light":  dict(teal=0.35, crush=0.03, k=5.0, hal=0.22, glow=0.12, bleach=0.12, grain=6),
    "medium": dict(teal=0.55, crush=0.06, k=6.5, hal=0.35, glow=0.18, bleach=0.25, grain=10),
    "heavy":  dict(teal=0.75, crush=0.09, k=8.0, hal=0.50, glow=0.25, bleach=0.38, grain=15),
}
SHADOW = np.array([0x09, 0x36, 0x47]) / 255
MID = np.array([0x1B, 0x4E, 0x5B]) / 255
HIGH = np.array([1.0, 0.95, 0.86])            # warm white highlights
LUMA = np.array([0.2126, 0.7152, 0.0722])


def _sig(x):
    return 1 / (1 + np.exp(-x))


def warm_weight(x: np.ndarray) -> np.ndarray:
    """1 on clearly orange things (skin, wood, gold), 0 on greys and beige walls."""
    mx, mn = x.max(-1, keepdims=True), x.min(-1, keepdims=True)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = x[..., 0:1], x[..., 1:2], x[..., 2:3]
    hue = (np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) + 360) % 360
    return np.exp(-(((hue - 25 + 180) % 360 - 180) / 20) ** 2) * np.clip((sat - 0.18) / 0.17, 0, 1)


def grade_rgb(x: np.ndarray, p: dict) -> np.ndarray:
    """x: (..., 3) floats 0-1 -> graded floats 0-1 (steps 2-4)."""
    warm = warm_weight(x)                                         # decided on the ungraded colour
    x = x * np.array([1.04, 1.0, 0.95])                          # 3: warm white balance
    x = np.clip((x - p["crush"]) / (1 - p["crush"]), 0, 1)       # crush blacks
    k = p["k"]                                                    # 2: print-film S-curve
    x = (_sig(k * (x - 0.5)) - _sig(-k / 2)) / (_sig(k / 2) - _sig(-k / 2))
    l = (x * LUMA).sum(-1, keepdims=True)
    # 4: everything that is not warm drifts toward the teal of its brightness
    t = np.where(l < 0.35, SHADOW + (MID - SHADOW) * (l / 0.35),
                 MID + (HIGH - MID) * np.clip((l - 0.35) / 0.55, 0, 1))
    t = t * (l / np.maximum((t * LUMA).sum(-1, keepdims=True), 1e-6))   # keep brightness
    m = p["teal"] * (1 - warm)
    x = x * (1 - m) + t * m
    # 3: saturation medium-high on the warm tones, a touch more orange
    l2 = (x * LUMA).sum(-1, keepdims=True)
    x = l2 + (x - l2) * (1 + 0.15 * warm)
    x = x * (1 + warm * np.array([0.04, 0.0, -0.06]))
    return np.clip(x, 0, 1)


def make_lut(strength: str, n: int = 33) -> Path:
    out = WORK / "grade" / f"fonzi_{strength}.cube"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    v = np.linspace(0, 1, n)
    b, g, r = np.meshgrid(v, v, v, indexing="ij")             # .cube: red changes fastest
    grid = np.stack([r, g, b], -1).reshape(-1, 3)
    y = grade_rgb(grid, STRENGTH[strength])
    with open(out, "w") as f:
        f.write(f'TITLE "fonzi {strength}"\nLUT_3D_SIZE {n}\n')
        f.writelines(f"{a:.6f} {c:.6f} {d:.6f}\n" for a, c, d in y)
    return out


def filter_chain(strength: str, src: str = "0:v", out: str = "v") -> str:
    """ffmpeg filter_complex for the full grade (steps 2-5) on a 1080x1920 frame."""
    p, lut = STRENGTH[strength], make_lut(strength)
    return (
        f"[{src}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
        f"lut3d=file='{lut}',format=gbrp,split=4[g_b][g_h][g_g][g_l];"
        # halation: only the brightest parts, tinted orange-red, blurred wide
        f"[g_h]curves=all='0/0 0.78/0 1/1',colorchannelmixer=rr=1:gg=0.55:bb=0.25,gblur=sigma=22[g_hal];"
        f"[g_g]curves=all='0/0 0.6/0.05 1/1',gblur=sigma=40[g_glow];"
        f"[g_l]hue=s=0[g_luma];"
        f"[g_b][g_hal]blend=all_mode=screen:all_opacity={p['hal']}[g_1];"
        f"[g_1][g_glow]blend=all_mode=screen:all_opacity={p['glow']}[g_2];"
        f"[g_2][g_luma]blend=all_mode=overlay:all_opacity={p['bleach']}[g_3];"
        f"[g_3]noise=alls={p['grain']}:allf=t+u,format=yuv420p[{out}]"
    )


def grade(inp: Path, out: Path, strength: str = "medium", ss: float | None = None, t: float | None = None):
    pre = (["-ss", f"{ss:.3f}"] if ss is not None else []) + (["-t", f"{t:.3f}"] if t is not None else [])
    run(["ffmpeg", "-v", "error", "-y", *pre, "-i", inp, "-filter_complex", filter_chain(strength),
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-c:a", "copy", out])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--strength", default="medium", choices=list(STRENGTH))
    ap.add_argument("--ss", type=float)
    ap.add_argument("--t", type=float)
    a = ap.parse_args()
    grade(a.inp, a.out, a.strength, a.ss, a.t)
    print(f"graded  {a.out}  ({a.strength})")
