#!/usr/bin/env python3
"""Glitch title style for the intro card (STYLE.md rule 0, Round 7; Python port of Style Lab r7-03).

    python3 scripts/intro_glitch.py selftest --out output/visuals/round7_prod/R7P-01/

Motion (style sheet title_styles.glitch, all relative to the beat frames):
    BURST [0,1,0,0,1,1,0,1] from b1 exactly as the pulse style (hidden on the 0 frames), then solid gold.
    On beats[1:4] a 3-frame RGB split: frame b red copy x -8 / cyan copy x +8, b+1 -5 / +5, b+2 -2 / +2, b+3 gone.
    The two copies add (R only + G,B only = the gold itself where they overlap), the group is held at alpha 0.6,
    then masked to the letter EDGES only:
        split_alpha *= 1 - dilate(main alpha with grit holes filled, 1 px, 3x3 max filter)
    (grit holes = enclosed transparent components < 500 px; real counters of O / D stay open), and the main gold
    title is composited OVER the masked split. The main title is never blinked, scaled or tinted here; the
    subtitle is never glitched (style_fx draws it separately).

Pure functions, no file I/O outside `selftest`, and no import of style_fx at module level (style_fx imports this).
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

BURST = [0, 1, 0, 0, 1, 1, 0, 1]            # title_styles.pulse BURST (== style_fx.BURST, checked in selftest)
GOLD = (212, 160, 23)                       # colours.gold #D4A017
RED = (212, 0, 0)                           # colours.glitch_red #D40000  (the gold's R channel)
CYAN = (0, 160, 23)                         # colours.glitch_cyan #00A017 (the gold's G + B channels)
OFFSETS = (8, 5, 2)                         # px, frames b, b+1, b+2
SPLIT_ALPHA_MAX = 0.6
GRIT_MAX = 500                              # px: enclosed transparent specks smaller than this count as glyph
HOLE_A = 20                                 # alpha > 20 = ink when finding the enclosed holes (as r7-03)
SIL_IOU_MIN = 0.96                          # selftest golden compare (Director, R7P-01 Option A)
RAW_IOU_MARGIN = 0.02                       # raw alpha IoU floor = title_ref-vs-golden limit - this
PAD = 16                                    # crop margin round the title ink (> max offset 8 + dilation 1)


def glitch_offset(k: int, beats: list[int]) -> int:
    """Split offset in px at frame k (0 = no split). Only beats[1:4]."""
    off = 0
    for b in beats[1:4]:
        d = k - b
        if 0 <= d < len(OFFSETS):
            off = OFFSETS[d]
    return off


def _visible(k: int, beats: list[int]) -> bool:
    b1 = beats[0]
    if k < b1:
        return False
    i = k - b1
    return bool(BURST[i]) if i < len(BURST) else True


def glitch_frames(beats: list[int], n: int | None = None) -> list[int]:
    """Frames that carry the split (inside the window [0, n) when n is given, and where the title shows)."""
    return [k for b in beats[1:4] for k in range(b, b + len(OFFSETS))
            if (n is None or k < n) and _visible(k, beats)]


def glitch_fits(beats: list[int], n: int) -> bool:
    """False = unfit (title_styles.glitch.unfit_when): no later beat with all 3 glitch frames inside the window."""
    return len(beats) > 1 and beats[1] + len(OFFSETS) - 1 < n


def _shift(a: np.ndarray, dx: int) -> np.ndarray:
    """Translate a 2-D array by dx px along x, zero fill (no wrap)."""
    out = np.zeros_like(a)
    if dx > 0:
        out[:, dx:] = a[:, :-dx]
    elif dx < 0:
        out[:, :dx] = a[:, -dx:]
    else:
        out[:] = a
    return out


def _edge_keep(ma: np.ndarray) -> np.ndarray:
    """1 - dilate(main alpha with grit holes filled, 1 px) as float 0..1 (r7-03 tools/mask_splits.py)."""
    from scipy import ndimage
    ma = ma.copy()
    ink = ma > HOLE_A
    holes = ndimage.binary_fill_holes(ink) & ~ink
    lab, n = ndimage.label(holes)
    if n:
        sz = np.bincount(lab.ravel())
        grit = (sz < GRIT_MAX)[lab] & (lab > 0)
        ma[grit] = 255
    dil = np.asarray(Image.fromarray(ma, "L").filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255.0
    return 1.0 - dil


def _split_parts(tl: Image.Image, off: int):
    """(crop box, masked split RGBA float array, main RGBA uint8 crop, keep mask) for offset `off`."""
    bb = tl.getchannel("A").getbbox()
    W, H = tl.size
    x0, y0, x1, y1 = max(0, bb[0] - PAD), max(0, bb[1] - PAD), min(W, bb[2] + PAD), min(H, bb[3] + PAD)
    main = np.asarray(tl.crop((x0, y0, x1, y1)).convert("RGBA"))
    a = main[..., 3].astype(np.float32) / 255.0
    ra, ca = _shift(a, -off), _shift(a, off)                    # red left, cyan right, y offset 0
    pr = ra[..., None] * np.array(RED, np.float32) + ca[..., None] * np.array(CYAN, np.float32)
    sa = np.minimum(1.0, ra + ca)                               # plus-lighter group (isolated)
    rgb = np.where(sa[..., None] > 0, pr / np.maximum(sa, 1e-6)[..., None], 0.0)
    keep = _edge_keep(main[..., 3])
    s = np.dstack([np.clip(rgb, 0, 255), sa * SPLIT_ALPHA_MAX * 255.0 * keep])
    return (x0, y0, x1, y1), s, main, keep


def glitch_title(tl: Image.Image, k: int, beats: list[int]) -> Image.Image | None:
    """The full title layer for frame k (None = hidden). tl = the style_fx title layer (RGBA, W x H, gold)."""
    if not beats or not _visible(k, beats):
        return None
    off = glitch_offset(k, beats)
    if not off or tl.getchannel("A").getbbox() is None:
        return tl
    (x0, y0, x1, y1), s, main, _ = _split_parts(tl, off)
    sm = Image.fromarray(np.clip(np.rint(s), 0, 255).astype(np.uint8), "RGBA")
    crop = Image.alpha_composite(sm, Image.fromarray(main, "RGBA"))   # main OVER the masked split
    out = Image.new("RGBA", tl.size, (0, 0, 0, 0))
    out.paste(crop, (x0, y0))
    return out


def glitch_stats(tl: Image.Image, beats: list[int], n: int) -> dict | None:
    """report_schema 'glitch': {frames, split_alpha_max, split_offset_max_px, split_px_inside_letters}."""
    fr = glitch_frames(beats, n)
    if not fr:
        return None
    a_max, inside, off_max = 0, 0, 0
    for k in fr:
        off = glitch_offset(k, beats)
        _, s, main, keep = _split_parts(tl, off)
        sa = np.clip(np.rint(s[..., 3]), 0, 255).astype(np.uint8)
        a_max = max(a_max, int(sa.max()))
        inside += int(((sa > 0) & (keep <= 0.0)).sum())        # split under the dilated, grit-filled letters
        off_max = max(off_max, off)
    return {"frames": fr, "split_alpha_max": round(a_max / 255.0, 3), "split_offset_max_px": off_max,
            "split_px_inside_letters": inside}


# ---------------------------------------------------------------- selftest (Locked In vs r7-03 golden)
def _selftest(out_dir):
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "scripts"))
    import style_fx as sf
    assert list(sf.BURST) == BURST and tuple(sf.GOLD) == GOLD, "BURST / GOLD differ from style_fx"
    out = Path(out_dir).resolve()
    if "style_lab" in out.parts:
        raise SystemExit("selftest: never writes under output/style_lab/")
    fdir = out / "frames"
    fdir.mkdir(parents=True, exist_ok=True)
    gold_dir = root / "output" / "style_lab" / "r7" / "r7-03" / "overlay"
    N, beats, SPLIT_Y = 90, [20, 40, 60, 80], 1260
    spec = sf.TitleSpec("LOCKED IN", "5 LIFTS. ONE SONG.", sf.TITLE_W)
    spec.y1 = 1000
    tl, _sub, _ = spec.layers()
    hi = np.array([0xEC, 0xD4, 0x97])
    gfr = set(glitch_frames(beats, N))
    rows, fails, mine, gold = {}, [], {}, {}
    for k in range(N):
        t = glitch_title(tl, k, beats)
        t = t if t is not None else Image.new("RGBA", tl.size, (0, 0, 0, 0))
        t.save(fdir / f"frame_{k:06d}.png")
        g = Image.open(gold_dir / f"frame_{k + 1:06d}.png").convert("RGBA")
        mine[k], gold[k] = t, g
        m = np.asarray(t)[:SPLIT_Y]
        r = np.asarray(g)[:SPLIT_Y]
        ma, ga = m[..., 3] > 20, r[..., 3] > 20
        mv, gv = bool(ma.any()), bool(ga.any())
        row = {"visible": mv, "golden_visible": gv}
        if mv != gv:
            fails.append(f"f{k}: visible {mv} vs golden {gv}")
        if mv and gv:
            iou = float((ma & ga).sum() / (ma | ga).sum())
            mb = [int(v) for v in (np.nonzero(ma.any(0))[0][[0, -1]].tolist() + np.nonzero(ma.any(1))[0][[0, -1]].tolist())]
            gb = [int(v) for v in (np.nonzero(ga.any(0))[0][[0, -1]].tolist() + np.nonzero(ga.any(1))[0][[0, -1]].tolist())]
            dev = max(abs(a - b) for a, b in zip(mb, gb))
            sm_, sg_ = _silhouette(m[..., 3]), _silhouette(r[..., 3])
            row.update(alpha_iou=round(iou, 4),
                       silhouette_iou=round(float((sm_ & sg_).sum() / (sm_ | sg_).sum()), 4),
                       bbox=[mb[0], mb[2], mb[1] + 1, mb[3] + 1],
                       golden_bbox=[gb[0], gb[2], gb[1] + 1, gb[3] + 1], bbox_dev_px=dev)
            if dev > 3:
                fails.append(f"f{k}: bbox dev {dev}")
            if row["silhouette_iou"] < SIL_IOU_MIN:
                fails.append(f"f{k}: silhouette IoU {row['silhouette_iou']:.4f} < {SIL_IOU_MIN}")
        # split colour present: pixel (alpha > 20) far from gold, i.e. a red or cyan fringe
        def split_px(arr):
            a = arr[..., 3] > 20
            d = np.abs(arr[..., :3].astype(int) - np.array(GOLD)).max(-1)
            return int((a & (d > 40)).sum())

        def split_mask(arr):
            d = np.abs(arr[..., :3].astype(int) - np.array(GOLD)).max(-1)
            return (arr[..., 3] > 20) & (d > 40)
        sp_m, sp_g = split_px(m), split_px(r)
        row.update(split_px=sp_m, golden_split_px=sp_g)
        if sp_m and sp_g:
            fm, fg = split_mask(m), split_mask(r)
            row["split_fringe_iou"] = round(float((fm & fg).sum() / (fm | fg).sum()), 4)
        if (sp_m > 0) != (k in gfr):
            fails.append(f"f{k}: split px {sp_m} but glitch frame = {k in gfr}")
        if (sp_g > 0) != (k in gfr):
            fails.append(f"f{k}: golden split px {sp_g} vs glitch frame = {k in gfr}")
        full = np.asarray(t)
        rgb = full[..., :3][full[..., 3] > 128]
        if rgb.size:
            row["max_rgb"] = rgb.max(0).tolist()
            if (rgb > hi).any(axis=-1).any():
                fails.append(f"f{k}: pixel brighter than #ECD497")
            if k not in gfr and not (rgb == np.array(GOLD)).all():
                fails.append(f"f{k}: title RGB not pure #D4A017 where alpha > 128")
        if (full[..., 3] > 0).any() and (full[..., :3][full[..., 3] > 0] >= 250).all(-1).any():
            fails.append(f"f{k}: white pixel")
        rows[f"f{k}"] = row
    # BURST visibility f20-27
    burst = [rows[f"f{k}"]["visible"] for k in range(20, 28)]
    if burst != [bool(v) for v in BURST]:
        fails.append(f"burst visibility {burst} != {BURST}")
    st = glitch_stats(tl, beats, N)
    if st["frames"] != [40, 41, 42, 60, 61, 62, 80, 81, 82]:
        fails.append(f"glitch frames {st['frames']}")
    if st["split_alpha_max"] > SPLIT_ALPHA_MAX or st["split_px_inside_letters"] != 0:
        fails.append(f"split stats {st}")
    offs = [glitch_offset(k, beats) for k in (40, 41, 42, 43)]
    if offs != [8, 5, 2, 0]:
        fails.append(f"offsets {offs}")
    # safe area (alpha > 20)
    ys = [int(np.nonzero(np.asarray(mine[k])[..., 3] > 20)[0].min()) for k in mine if mine[k].getbbox()]
    ye = [int(np.nonzero(np.asarray(mine[k])[..., 3] > 20)[0].max()) for k in mine if mine[k].getbbox()]
    text_y = [min(ys), max(ye)]
    if text_y[0] < 110 or text_y[1] > 1500:
        fails.append(f"text y {text_y} outside the safe area")
    vis = [r for r in rows.values() if "alpha_iou" in r]
    # rasteriser floor: the production title layer (== r7-00/ref/title_ref.png) vs the golden at rest (f35)
    ref = np.asarray(Image.open(root / "output/style_lab/r7/r7-00/ref/title_ref.png").convert("RGBA"))[:SPLIT_Y, :, 3]
    g35 = np.asarray(gold[35])[:SPLIT_Y, :, 3]
    tl_eq_ref = bool((np.asarray(tl)[:SPLIT_Y, :, 3] == ref).all())
    floor = float(((ref > 20) & (g35 > 20)).sum() / ((ref > 20) | (g35 > 20)).sum())
    fr_iou = [r["split_fringe_iou"] for r in rows.values() if "split_fringe_iou" in r]
    if not tl_eq_ref:
        fails.append("title layer differs from r7-00/ref/title_ref.png (production title)")
    raw_floor = round(floor - RAW_IOU_MARGIN, 4)
    for name, r in rows.items():
        if "alpha_iou" in r and r["alpha_iou"] < raw_floor:
            fails.append(f"{name}: raw alpha IoU {r['alpha_iou']:.4f} < floor {raw_floor}")
    summary = {"ok": not fails, "fails": fails,
               "golden_check": {
                   "rule": f"silhouette IoU (alpha > {HOLE_A}, grit holes < {GRIT_MAX} px filled, same rule as the "
                           f"edge mask) >= {SIL_IOU_MIN} and bbox dev <= 3 px on every visible frame; raw alpha "
                           f"IoU reported, must be >= (title_ref vs golden f35 limit) - {RAW_IOU_MARGIN}",
                   "reason": "rasteriser difference: PIL vs Chrome; title layer must equal production title_ref",
                   "decision": "Director, R7P-01 Option A (replaces alpha_iou_min 0.97 for this compare)",
                   "silhouette_iou_min_required": SIL_IOU_MIN, "raw_alpha_iou_floor": raw_floor},
               "title_layer_equals_title_ref": tl_eq_ref,
               "golden_rest_vs_title_ref_alpha_iou_f35": round(floor, 4),
               "silhouette_iou_min": min(r["silhouette_iou"] for r in vis),
               "split_fringe_iou_min": min(fr_iou), "split_fringe_iou_mean": round(sum(fr_iou) / len(fr_iou), 4), "frames": N, "beats": beats, "title_size": spec.size,
               "title_y1": spec.y1, "compare_rows_y_lt": SPLIT_Y, "golden": str(gold_dir),
               "visible_frames_compared": len(vis),
               "alpha_iou_min": min(r["alpha_iou"] for r in vis), "bbox_dev_px_max": max(r["bbox_dev_px"] for r in vis),
               "glitch": st, "glitch_offsets_f40_43": offs, "burst_visibility_f20_27": burst,
               "title_max_rgb": np.max([r["max_rgb"] for r in rows.values() if "max_rgb" in r], 0).tolist(),
               "text_y_range": text_y, "per_frame": rows}
    (out / "golden_compare.json").write_text(json.dumps(summary, indent=1))
    _sheet(mine, gold, out / "sheet.png")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_frame"}, indent=1))
    return 0 if summary["ok"] else 1


def _silhouette(a):
    """alpha > 20 with the grit holes filled (the letter shapes without the dirt texture)."""
    from scipy import ndimage
    ink = a > HOLE_A
    holes = ndimage.binary_fill_holes(ink) & ~ink
    lab, n = ndimage.label(holes)
    if not n:
        return ink
    return ink | ((np.bincount(lab.ravel()) < GRIT_MAX)[lab] & (lab > 0))


def _sheet(mine, gold, path):
    from PIL import ImageDraw
    ks = list(range(19, 23)) + list(range(39, 44)) + list(range(59, 64))
    box = (150, 900, 930, 1260)                                  # title rows only
    cw, ch = (box[2] - box[0]) // 2, (box[3] - box[1]) // 2
    lab = 22
    sheet = Image.new("RGB", (2 * (2 * cw + 12) + 12, 12 + 7 * (ch + lab + 12)), (40, 40, 44))
    d = ImageDraw.Draw(sheet)
    for i, k in enumerate(ks):
        col, row = i % 2, i // 2
        x = 12 + col * (2 * cw + 12)
        y = 12 + row * (ch + lab + 12)
        d.text((x, y), f"f{k}  port | golden r7-03", fill=(230, 230, 230))
        for j, im in enumerate((mine[k], gold[k])):
            bg = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (90, 90, 96, 255))
            c = Image.alpha_composite(bg, im.crop(box)).convert("RGB").resize((cw, ch), Image.LANCZOS)
            sheet.paste(c, (x + j * cw, y + lab))
    sheet.save(path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("selftest")
    s.add_argument("--out", required=True)
    raise SystemExit(_selftest(ap.parse_args().out))
