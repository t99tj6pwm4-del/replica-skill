#!/usr/bin/env python3
"""3D logo behind him for the intro card (Round 7, r7-04 port to numpy / PIL; no HyperFrames at render time).

The big_logo art stacked 14 times 1 px apart in depth (copy 0 = the front face = the style_fx.big_logo layer
exactly, copies 1-13 = the extrusion sides), perspective 1600 px, perspective origin (540, 960), transform origin
the logo box centre (output/style_lab/r7/r7-04/hf_logo/index.html). It swings rotateY -8 -> 0 deg and
rotateX 4 -> 0 deg from b1-4 (the fade start) to b1+10 with cubic in-out, then is settled and still (the settled
layer is computed once and reused). Alphas as output/style_lab/r7/r7-04/build_r7-04.py, white only:
  front : the big_logo layer alpha (72 % effective, max 183), warped like copy 0
  sides : 30 % of the side coverage, only where the front face is not (knock-out, no stacking)
  fade  : a = clamp((k - (b1-4)) / 4, 0, 1), monotonic, never flickers
fit(): every frame's alpha>8 bbox must sit inside [4, 4, 1076, 1916]; otherwise the art shrinks in 2 % steps.

    from intro_logo3d import Logo3D
    lg = Logo3D(front_layer, box); lg.fit(b1, n); layer, bbox = lg.frame(k, b1); lg.stats()

    python3 scripts/intro_logo3d.py selftest --out output/visuals/round7_prod/R7P-03/
        Locked In, b1 = 20, f0-89 vs the r7-04 golden logo_seq/ (writes logo/ RGBA + golden_compare.json).

Values: output/visuals/round7_prod/style_sheet.json logo_styles.3d, colours.logo_front / logo_depth_side,
safe_area_and_face.logo_in_frame. No style_fx import at module level (style_fx imports this module).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

W, H = 1080, 1920
PERSPECTIVE = 1600.0                   # px
PERSP_ORIGIN = (540.0, 960.0)
N_COPIES, GAP_PX = 14, 1.0             # copy i sits at z = -i px
RY0, RX0 = -8.0, 4.0                   # deg, swing start pose -> 0
SWING_PRE, SWING_POST = 4, 10          # swing b1-4 .. b1+10
FADE_PRE = 4                           # fade b1-4 .. b1
FRONT_A, SIDE_A = 0.85, 0.30           # big_logo alpha*0.85 pasted with itself (72 % eff.), sides 30 %
FIT_BOX = (4, 4, 1076, 1916)           # alpha>8 bbox must be inside
FIT_STEP, FIT_MIN = 0.02, 0.50
BBOX_A = 8


def ease_in_out(x: float) -> float:
    """r7-04 easeInOut (extruded-logo settle): cubic in-out on [0, 1]."""
    u = min(1.0, max(0.0, x))
    return 4 * u * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def fade(k: int, b1: int) -> float:
    return min(1.0, max(0.0, (k - (b1 - FADE_PRE)) / FADE_PRE))


def _rot(ry_deg: float, rx_deg: float) -> np.ndarray:
    """CSS 'rotateY(ry) rotateX(rx)' (y down, +z toward the viewer), column vectors: M = Ry @ Rx."""
    a, b = math.radians(ry_deg), math.radians(rx_deg)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return ry @ rx


class Logo3D:
    def __init__(self, front_layer: Image.Image, box):
        a = np.asarray(front_layer.convert("RGBA"))[..., 3]
        if a.shape != (H, W):
            raise ValueError(f"Logo3D: front layer must be {W}x{H}, got {a.shape[1]}x{a.shape[0]}")
        self.box = tuple(int(v) for v in box)
        self.front_a = a.copy()
        # png coverage c behind the 72 % transfer a = (0.85 c)^2 / 255 (needed for the side copies + knock-out)
        cov = np.clip(np.sqrt(a.astype(np.float64) * 255.0) / FRONT_A, 0, 255)
        self._front_img = Image.fromarray(a, "L")
        self._cov_img = Image.fromarray(np.round(cov).astype(np.uint8), "L")
        self.T = ((self.box[0] + self.box[2]) / 2.0, (self.box[1] + self.box[3]) / 2.0)
        self.scale = 1.0
        self._raw: dict = {}            # (scale, step) -> float alpha (unfaded)
        self._settled = None            # (Image, bbox) of the settled, fully faded layer
        self._boxes: list = []
        self._fitted = None

    # ----- geometry -----
    def _fwd(self, step: int, z: float) -> np.ndarray:
        """3x3 homography: layer px (x, y) -> screen px for copy at depth z, swing step 0..14."""
        s = ease_in_out(step / (SWING_PRE + SWING_POST))
        R = _rot(RY0 * (1 - s), RX0 * (1 - s))
        sc, (tx, ty), (px, py), p = self.scale, self.T, PERSP_ORIGIN, PERSPECTIVE
        L = np.array([[sc, 0, -sc * tx], [0, sc, -sc * ty], [0, 0, 1]])
        V = np.array([[R[0, 0], R[0, 1], R[0, 2] * z], [R[1, 0], R[1, 1], R[1, 2] * z],
                      [R[2, 0], R[2, 1], R[2, 2] * z], [0, 0, 1]])
        Q = np.array([[1, 0, -px / p, tx], [0, 1, -py / p, ty], [0, 0, -1 / p, 1]])
        return Q @ V @ L

    def _warp(self, img: Image.Image, F: np.ndarray) -> np.ndarray:
        if np.allclose(F, np.eye(3), atol=1e-12):
            return np.asarray(img, np.float64)
        x0, y0, x1, y1 = self.box
        c = np.array([[x0, y0, 1], [x1, y0, 1], [x0, y1, 1], [x1, y1, 1]], np.float64).T
        sp = F @ c
        sx, sy = sp[0] / sp[2], sp[1] / sp[2]
        ox, oy = max(0, int(math.floor(sx.min())) - 3), max(0, int(math.floor(sy.min())) - 3)
        ex, ey = min(W, int(math.ceil(sx.max())) + 3), min(H, int(math.ceil(sy.max())) + 3)
        out = np.zeros((H, W), np.float64)
        if ex <= ox or ey <= oy:
            return out
        inv = np.linalg.inv(F) @ np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]], np.float64)
        inv = inv / inv[2, 2]
        w = img.transform((ex - ox, ey - oy), Image.Transform.PERSPECTIVE, tuple(inv.ravel()[:8]),
                          Image.Resampling.BILINEAR)
        out[oy:ey, ox:ex] = np.asarray(w, np.float64)
        return out

    def _raw_alpha(self, step: int) -> np.ndarray:
        step = min(max(step, 0), SWING_PRE + SWING_POST)
        key = (round(self.scale, 4), step)
        if key not in self._raw:
            front = self._warp(self._front_img, self._fwd(step, 0.0))
            cf = self._warp(self._cov_img, self._fwd(step, 0.0)) / 255.0
            keep = np.ones((H, W), np.float64)               # union of copies 1-13 (source-over)
            for i in range(1, N_COPIES):
                keep *= 1.0 - self._warp(self._cov_img, self._fwd(step, -i * GAP_PX)) / 255.0
            cs = 1.0 - keep
            side = 255.0 * cs * SIDE_A * (1.0 - cf)
            self._raw[key] = np.clip(front + side, 0, 255)
        return self._raw[key]

    def _layer(self, a: np.ndarray, la: float):
        a = np.floor(a * la) if la < 1 else a
        a8 = a.astype(np.uint8)
        rgba = np.dstack([np.full_like(a8, 255)] * 3 + [a8])
        im = Image.fromarray(rgba, "RGBA")
        bb = Image.fromarray(((a8 > BBOX_A) * 255).astype(np.uint8)).getbbox()
        return im, (list(bb) if bb else None)

    # ----- api -----
    def frame(self, k: int, b1: int):
        """(RGBA WxH layer with the fade applied, alpha>8 bbox or None) for intro frame k."""
        la = fade(k, b1)
        if la <= 0:
            return Image.new("RGBA", (W, H), (0, 0, 0, 0)), None
        step = k - (b1 - SWING_PRE)
        if la >= 1 and step >= SWING_PRE + SWING_POST:
            if self._settled is None or self._settled[0] != self.scale:
                self._settled = (self.scale, *self._layer(self._raw_alpha(SWING_PRE + SWING_POST), 1.0))
            return self._settled[1], self._settled[2]
        return self._layer(self._raw_alpha(step), la)

    def _frame_boxes(self, b1: int, n: int):
        return [(k, self.frame(k, b1)[1]) for k in range(n)]

    def fit(self, b1: int, n: int) -> float:
        """Shrink the art in 2 % steps until every frame's alpha>8 bbox is inside FIT_BOX. Returns the scale."""
        while True:
            boxes = self._frame_boxes(b1, n)
            bad = [b for _, b in boxes if b and (b[0] < FIT_BOX[0] or b[1] < FIT_BOX[1] or b[2] > FIT_BOX[2]
                                                 or b[3] > FIT_BOX[3])]
            if not bad:
                break
            nxt = round(self.scale - FIT_STEP, 4)
            if nxt < FIT_MIN:
                raise SystemExit(f"intro: the 3D logo does not fit in the frame even at scale {self.scale}")
            self.scale = nxt
            self._raw.clear()
            self._settled = None
        self._boxes = boxes
        self._fitted = (b1, n)
        return self.scale

    def stats(self) -> dict:
        bxs = [b for _, b in self._boxes if b]
        mx = [min(b[0] for b in bxs), min(b[1] for b in bxs), max(b[2] for b in bxs), max(b[3] for b in bxs)] \
            if bxs else None
        return {"logo_scale": self.scale, "logo_box_max": mx}


# ---------------- selftest (Locked In, b1 = 20, vs r7-04 golden) ----------------
def _selftest(out):
    import hashlib
    import json
    import sys
    import time
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "scripts"))
    import style_fx

    out = Path(out)
    (out / "logo").mkdir(parents=True, exist_ok=True)
    gold_dir = root / "output" / "style_lab" / "r7" / "r7-04" / "logo_seq"
    B1, N = 20, 90
    front, box = style_fx.big_logo()
    flat_max = int(np.asarray(front)[..., 3].max())

    def run(save):
        lg = Logo3D(front, box)
        t0 = time.time()
        scale = lg.fit(B1, N)
        arrs = []
        for k in range(N):
            im, bb = lg.frame(k, B1)
            a = np.asarray(im)
            arrs.append(a)
            if save:
                im.save(out / "logo" / f"l{k:04d}.png")
        return lg, scale, arrs, time.time() - t0

    lg, scale, arrs, dt90 = run(True)
    _, _, arrs2, _ = run(False)
    det = all(np.array_equal(a, b) for a, b in zip(arrs, arrs2))
    png_md5 = hashlib.md5(b"".join((out / "logo" / f"l{k:04d}.png").read_bytes() for k in range(N))).hexdigest()

    # runtime for 60 frames (fresh object, includes fit)
    t0 = time.time()
    lg60 = Logo3D(front, box)
    lg60.fit(B1, 60)
    for k in range(60):
        lg60.frame(k, B1)
    dt60 = time.time() - t0

    def bbox(m):
        bb = Image.fromarray((m * 255).astype(np.uint8)).getbbox()
        return list(bb) if bb else None

    rows, fails = [], []
    for k in range(N):
        a = arrs[k][..., 3].astype(np.int32)
        g = np.asarray(Image.open(gold_dir / f"l{k:04d}.png").convert("RGBA"))[..., 3].astype(np.int32)
        ma, mg = a > 20, g > 20
        r = {"k": k, "fade": round(fade(k, B1), 3), "max_a": int(a.max()), "gold_max_a": int(g.max()),
             "sum_a": int(a.sum())}
        if ma.any() or mg.any():
            iou = float((ma & mg).sum()) / float((ma | mg).sum())
            ba, bg = bbox(ma), bbox(mg)
            dev = max(abs(x - y) for x, y in zip(ba, bg)) if ba and bg else 999
            u = (a > 0) | (g > 0)
            r.update({"iou_a20": round(iou, 4), "bbox_a20": ba, "gold_bbox_a20": bg, "bbox_dev_px": dev,
                      "mean_abs_alpha_in_logo": round(float(np.abs(a - g)[u].mean()), 3),
                      "mean_abs_alpha_frame": round(float(np.abs(a - g).mean()), 4)})
            if iou < 0.97:
                fails.append(f"f{k} IoU {iou:.4f}")
            if 18 <= k <= 30 and dev > 3:
                fails.append(f"f{k} bbox dev {dev}")
            if k >= B1 + SWING_POST and r["mean_abs_alpha_in_logo"] > 4:
                fails.append(f"f{k} settled mean |da| {r['mean_abs_alpha_in_logo']}")
        bb8 = Image.fromarray(((a > 8) * 255).astype(np.uint8)).getbbox()
        if bb8 and (bb8[0] < 4 or bb8[1] < 4 or bb8[2] > 1076 or bb8[3] > 1916):
            fails.append(f"f{k} bbox {bb8} leaves the frame")
        rgb = arrs[k][..., :3][arrs[k][..., 3] > 0]
        if rgb.size and (rgb != 255).any():
            fails.append(f"f{k} non-white pixel")
        rows.append(r)

    # front face / sides
    st = lg._raw_alpha(SWING_PRE + SWING_POST)
    fa = np.asarray(front)[..., 3]
    settled = arrs[N - 1][..., 3]
    front_max = int(settled[fa > 0].max())
    side_only = int(((settled > 20) & (fa == 0)).sum())
    front_equal = bool(np.array_equal(settled[fa >= 180], fa[fa >= 180]))
    if abs(front_max - flat_max) > 1:
        fails.append(f"front max {front_max} != flat {flat_max}")
    # fade monotonic + still
    fades = [fade(k, B1) for k in range(B1 - FADE_PRE, B1 + 1)]
    sums = [rows[k]["sum_a"] for k in range(B1 - FADE_PRE, B1 + 1)]
    maxes = [rows[k]["max_a"] for k in range(B1 - FADE_PRE, B1 + 1)]
    mono = all(x <= y for x, y in zip(fades, fades[1:])) and all(x <= y for x, y in zip(sums, sums[1:])) \
        and all(x <= y for x, y in zip(maxes, maxes[1:]))
    still = all(np.array_equal(arrs[k], arrs[B1 + SWING_POST]) for k in range(B1 + SWING_POST, N))
    moving_before = not np.array_equal(arrs[B1 + SWING_POST - 1], arrs[B1 + SWING_POST])
    if not mono:
        fails.append("fade not monotonic")
    if not still:
        fails.append("not still from b1+10")
    if not det:
        fails.append("not deterministic")
    if dt60 >= 30:
        fails.append(f"60 frames took {dt60:.1f}s")

    # forced wide art (1060 px) -> fit() must shrink it
    src = Image.open(style_fx.LOGO).convert("RGBA")
    art = src.crop(Image.fromarray((np.asarray(src)[..., 3] > 8).astype(np.uint8) * 255).getbbox())
    s = 1060 / art.width
    art = art.resize((1060, int(round(art.height * s))), Image.LANCZOS)
    aa = art.getchannel("A").point(lambda v: int(v * 0.85))
    art = Image.merge("RGBA", (*[Image.new("L", art.size, 255)] * 3, aa))
    wide = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wx0, wy0 = (W - art.width) // 2, (H - art.height) // 2
    wide.paste(art, (wx0, wy0), art)
    wbox = (wx0, wy0, wx0 + art.width, wy0 + art.height)
    lw = Logo3D(wide, wbox)
    wscale = lw.fit(B1, N)
    wst = lw.stats()
    wmax = wst["logo_box_max"]
    wide_ok = wscale < 1.0 and wmax[0] >= 4 and wmax[1] >= 4 and wmax[2] <= 1076 and wmax[3] <= 1916
    if not wide_ok:
        fails.append(f"wide fit failed {wscale} {wmax}")
    for k in (B1 - 2, B1, B1 + 4, N - 1):
        bg = Image.new("RGBA", (W, H), (60, 60, 60, 255))           # on grey so the white art is visible
        Image.alpha_composite(bg, lw.frame(k, B1)[0]).convert("RGB").save(out / f"wide_f{k:02d}.png")

    vis = [r for r in rows if "iou_a20" in r]
    res = {
        "order": "R7P-03", "ok": not fails, "fails": fails, "b1": B1, "frames": N,
        "golden": str(gold_dir), "logo_box": list(box), "flat_front_max_alpha": flat_max,
        "stats": lg.stats(), "fit_scale": scale,
        "iou_min": min(r["iou_a20"] for r in vis), "iou_min_frame": min(vis, key=lambda r: r["iou_a20"])["k"],
        "bbox_dev_max_f18_30": max(r["bbox_dev_px"] for r in vis if 18 <= r["k"] <= 30),
        "settled_mean_abs_alpha_in_logo_max": max(r["mean_abs_alpha_in_logo"] for r in vis if r["k"] >= 30),
        "front_face_max_alpha": front_max, "front_equals_flat_where_flat_ge_180": front_equal,
        "side_only_px_a20_settled": side_only, "colour": "white only",
        "fade_b1m4_b1": fades, "sum_alpha_b1m4_b1": sums, "max_alpha_b1m4_b1": maxes, "fade_monotonic": mono,
        "still_from_b1p10": still, "moving_until_b1p9": moving_before,
        "deterministic_two_runs": det, "png_md5_all_frames": png_md5,
        "runtime_s_90_frames_incl_fit": round(dt90, 2), "runtime_s_60_frames_incl_fit": round(dt60, 2),
        "wide_test": {"art_w": 1060, "box": list(wbox), "fit_scale": wscale, "logo_box_max": wmax, "ok": wide_ok},
        "rows": rows,
    }
    (out / "golden_compare.json").write_text(json.dumps(res, indent=1))

    # contact sheet: ours vs golden, f17 / 20 / 24 / 30, alpha on grey
    ks = [17, 20, 24, 30]
    tw, th = 270, 480
    sheet = Image.new("RGB", (tw * len(ks), th * 2), (60, 60, 60))
    for j, k in enumerate(ks):
        for i, im in enumerate([Image.fromarray(arrs[k], "RGBA"),
                                Image.open(gold_dir / f"l{k:04d}.png").convert("RGBA")]):
            bg = Image.new("RGBA", (W, H), (60, 60, 60, 255))
            sheet.paste(Image.alpha_composite(bg, im).convert("RGB").resize((tw, th)), (j * tw, i * th))
    sheet.save(out / "sheet.png")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("selftest")
    s.add_argument("--out", required=True)
    a = ap.parse_args()
    raise SystemExit(_selftest(a.out))
