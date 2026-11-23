#!/usr/bin/env python3
"""Glitch title style for the intro card (STYLE.md rule 0). WHITE-ONLY since 2026-11-23 (Director answer 24: no
colour anywhere, so the old Round 7 red / cyan split is replaced; the r7-03 golden compare is retired).

    python3 scripts/intro_glitch.py selftest --out output/white_look_test/glitch_selftest/

Motion (all relative to the beat frames; the title is pure white, config text_look):
    BURST [0,1,0,0,1,1,0,1] from b1 exactly as the pulse style (hidden on the 0 frames), then solid white.
    On beats[1:4] a SHORT 2-frame white burst:
      frame b    two white GHOST copies of the title at x -8 / +8 px, alpha 0.45, masked to the letter EDGES only
                 (ghost_alpha *= 1 - dilate(main alpha with grit holes filled, 1 px)), plus a SLICE JITTER: two thin
                 horizontal bands of the main title (each 12 % of the title height, fixed per beat) shifted
                 +10 / -10 px sideways
      frame b+1  ghosts at -4 / +4 px, alpha 0.25, no slice
      frame b+2  clean
    The ghosts are white like the letters, so nothing on screen is ever tinted; the text_look glow + shadow go on
    the whole result in style_fx (they follow the ghosts and the slices). The subtitle is never glitched.

Pure functions, no file I/O outside `selftest`, and no import of style_fx at module level (style_fx imports this).
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

BURST = [0, 1, 0, 0, 1, 1, 0, 1]            # title_styles.pulse BURST (== style_fx.BURST, checked in selftest)
WHITE = (255, 255, 255)                     # config text_look.color; the ghosts use the same white
OFFSETS = (8, 4)                            # px, frames b, b+1 (b+2 clean): short
GHOST_ALPHA = (0.45, 0.25)                  # ghost copies' alpha on frames b, b+1
SPLIT_ALPHA_MAX = 0.6                       # QA ceiling (unchanged name: qa_check reads split_alpha_max)
SLICE_SHIFT = 10                            # px, slice jitter on frame b only
SLICE_H = 0.12                              # each slice = 12 % of the title ink height
SLICE_AT = ((0.22, 0.64), (0.40, 0.78), (0.15, 0.55))   # slice band tops (fraction of ink height), per later beat
GRIT_MAX = 500                              # px: enclosed transparent specks smaller than this count as glyph
HOLE_A = 20
PAD = 16                                    # crop margin round the title ink (> max offset 8 + dilation 1)


def glitch_offset(k: int, beats: list[int]) -> int:
    """Ghost offset in px at frame k (0 = clean). Only beats[1:4]."""
    off = 0
    for b in beats[1:4]:
        d = k - b
        if 0 <= d < len(OFFSETS):
            off = OFFSETS[d]
    return off


def _beat_index(k: int, beats: list[int]) -> tuple[int, int] | None:
    """(which later beat 0..2, frame within the burst) or None."""
    for i, b in enumerate(beats[1:4]):
        if 0 <= k - b < len(OFFSETS):
            return i, k - b
    return None


def _visible(k: int, beats: list[int]) -> bool:
    b1 = beats[0]
    if k < b1:
        return False
    i = k - b1
    return bool(BURST[i]) if i < len(BURST) else True


def glitch_frames(beats: list[int], n: int | None = None) -> list[int]:
    """Frames that carry the burst (inside the window [0, n) when n is given, and where the title shows)."""
    return [k for b in beats[1:4] for k in range(b, b + len(OFFSETS))
            if (n is None or k < n) and _visible(k, beats)]


def glitch_fits(beats: list[int], n: int) -> bool:
    """False = unfit: no later beat with the whole burst inside the window."""
    return len(beats) > 1 and beats[1] + len(OFFSETS) - 1 < n


def _shift(a: np.ndarray, dx: int) -> np.ndarray:
    out = np.zeros_like(a)
    if dx > 0:
        out[:, dx:] = a[:, :-dx]
    elif dx < 0:
        out[:, :dx] = a[:, -dx:]
    else:
        out[:] = a
    return out


def _edge_keep(ma: np.ndarray) -> np.ndarray:
    """1 - dilate(main alpha with grit holes filled, 1 px) as float 0..1."""
    from scipy import ndimage
    ma = ma.copy()
    ink = ma > HOLE_A
    holes = ndimage.binary_fill_holes(ink) & ~ink
    lab, n = ndimage.label(holes)
    if n:
        sz = np.bincount(lab.ravel())
        ma[(sz < GRIT_MAX)[lab] & (lab > 0)] = 255
    dil = np.asarray(Image.fromarray(ma, "L").filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255.0
    return 1.0 - dil


def _parts(tl: Image.Image, off: int, ghost_a: float):
    """(crop box, ghost alpha float 0..255 (edges only), main RGBA uint8 crop, keep mask)."""
    bb = tl.getchannel("A").getbbox()
    W, H = tl.size
    x0, y0, x1, y1 = max(0, bb[0] - PAD), max(0, bb[1] - PAD), min(W, bb[2] + PAD), min(H, bb[3] + PAD)
    main = np.asarray(tl.crop((x0, y0, x1, y1)).convert("RGBA"))
    a = main[..., 3].astype(np.float32) / 255.0
    ga = np.minimum(1.0, _shift(a, -off) + _shift(a, off))
    keep = _edge_keep(main[..., 3])
    return (x0, y0, x1, y1), ga * ghost_a * 255.0 * keep, main, keep


def _slice(main: np.ndarray, which: int) -> np.ndarray:
    """Two thin horizontal bands of the main title shifted sideways (+SLICE_SHIFT, -SLICE_SHIFT)."""
    ys = np.nonzero(main[..., 3] > HOLE_A)[0]
    if not ys.size:
        return main
    top, hgt = int(ys.min()), int(ys.max() - ys.min() + 1)
    out = main.copy()
    for j, f in enumerate(SLICE_AT[which % len(SLICE_AT)]):
        a0 = top + int(f * hgt)
        a1 = min(main.shape[0], a0 + max(2, int(SLICE_H * hgt)))
        dx = SLICE_SHIFT if j == 0 else -SLICE_SHIFT
        band = main[a0:a1]
        sh = np.zeros_like(band)
        if dx > 0:
            sh[:, dx:] = band[:, :-dx]
        else:
            sh[:, :dx] = band[:, -dx:]
        out[a0:a1] = sh
    return out


def glitch_title(tl: Image.Image, k: int, beats: list[int]) -> Image.Image | None:
    """The full title layer for frame k (None = hidden). tl = the style_fx title layer (RGBA, W x H, white)."""
    if not beats or not _visible(k, beats):
        return None
    bi = _beat_index(k, beats)
    if bi is None or tl.getchannel("A").getbbox() is None:
        return tl
    which, d = bi
    (x0, y0, x1, y1), ga, main, _ = _parts(tl, OFFSETS[d], GHOST_ALPHA[d])
    ghost = np.zeros(main.shape, np.uint8)
    ghost[..., :3] = WHITE
    ghost[..., 3] = np.clip(np.rint(ga), 0, 255).astype(np.uint8)
    body = _slice(main, which) if d == 0 else main
    crop = Image.alpha_composite(Image.fromarray(ghost, "RGBA"), Image.fromarray(body, "RGBA"))
    out = Image.new("RGBA", tl.size, (0, 0, 0, 0))
    out.paste(crop, (x0, y0))
    return out


def glitch_stats(tl: Image.Image, beats: list[int], n: int) -> dict | None:
    """report 'glitch': {frames, split_alpha_max, split_offset_max_px, split_px_inside_letters, colour, slices}."""
    fr = glitch_frames(beats, n)
    if not fr:
        return None
    a_max, inside, off_max = 0, 0, 0
    for k in fr:
        _, d = _beat_index(k, beats)
        _, ga, _, keep = _parts(tl, OFFSETS[d], GHOST_ALPHA[d])
        sa = np.clip(np.rint(ga), 0, 255).astype(np.uint8)
        a_max = max(a_max, int(sa.max()))
        inside += int(((sa > 0) & (keep <= 0.0)).sum())
        off_max = max(off_max, OFFSETS[d])
    return {"frames": fr, "split_alpha_max": round(a_max / 255.0, 3), "split_offset_max_px": off_max,
            "split_px_inside_letters": inside, "colour": "white ghosts (no red / cyan)",
            "slice_shift_px": SLICE_SHIFT, "burst_frames_per_beat": len(OFFSETS)}


def _selftest(out_dir):
    """White-only self-check (no golden: the r7-03 golden is the retired red / cyan split)."""
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "scripts"))
    import style_fx as sf
    assert list(sf.BURST) == BURST, "BURST differs from style_fx"
    out = Path(out_dir).resolve()
    (out / "frames").mkdir(parents=True, exist_ok=True)
    N, beats = 90, [20, 40, 60, 80]
    spec = sf.TitleSpec("LOCKED IN", "5 LIFTS. ONE SONG.", sf.TITLE_W)
    tl, _sub, _ = spec.layers()
    fails, rows = [], {}
    gfr = set(glitch_frames(beats, N))
    for k in range(N):
        t = glitch_title(tl, k, beats)
        vis = t is not None
        if vis != _visible(k, beats):
            fails.append(f"f{k}: visible {vis}")
        if t is None:
            continue
        a = np.asarray(t)
        on = a[..., 3] > 0
        spread = int((a[..., :3][on].max(-1).astype(int) - a[..., :3][on].min(-1)).max()) if on.any() else 0
        if spread:
            fails.append(f"f{k}: tinted pixel (spread {spread})")
        diff = bool((np.asarray(t) != np.asarray(tl)).any())
        if diff != (k in gfr):
            fails.append(f"f{k}: changed {diff} but glitch frame {k in gfr}")
        rows[f"f{k}"] = {"glitch": k in gfr, "spread": spread}
        if k in (40, 41, 42):
            t.save(out / "frames" / f"frame_{k:04d}.png")
    st = glitch_stats(tl, beats, N)
    if st["frames"] != [40, 41, 60, 61, 80, 81]:
        fails.append(f"glitch frames {st['frames']}")
    if st["split_alpha_max"] > SPLIT_ALPHA_MAX or st["split_px_inside_letters"]:
        fails.append(f"stats {st}")
    res = {"ok": not fails, "fails": fails, "glitch": st, "per_frame": rows}
    (out / "selftest.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "per_frame"}, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("selftest")
    s.add_argument("--out", required=True)
    raise SystemExit(_selftest(ap.parse_args().out))
