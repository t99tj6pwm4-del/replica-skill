#!/usr/bin/env python3
"""Letters-smash title style for the intro card (STYLE.md rule 0, Round 7; port of Style Lab r7-05).

Python / PIL / numpy port of output/style_lab/r7/r7-05 (hf/build.py scatter solver + hf/index.html timeline),
generalised to any title and any face. All motion is relative to b1 (the first beat frame in the window):

    b1-9 .. b1-5  glyphs fade in scattered (opacity (k - (b1-10)) / 5), scale 0.82, offsets <= 180 / 120 px,
                  rotation <= 12 deg (fixed-seed search 0x0C5E2026, 3000 trials), >= 24 px between glyph boxes,
                  below his head box + 40 px, above y 1500, inside x 60-1020, off the dumbbell side (keep-out)
    b1-4          hold
    b1-3 .. b1-1  fly: back.out(1.7) on x / y / rotation toward a spaced row (40 px between ink boxes at 0.90,
                  each line centred on x 540), scale 0.82 -> 0.90 (cubic out)
    b1            land: the exact title layer tl (same pixels as strobe / pulse at rest)
    b1 .. b1+3    shake of the whole title: (+6,-3) (-4,+2) (+2,-1) (0,0)
    later beats   the locked pulse (tint toward white by 0.55 e, scale 1 + 0.06 e about the group centre), no burst

Keep-out (the dumbbell / working-arm side): auto = compare his mask pixels left vs right of the torso strip
(head-box centre x +- 0.6 head-box width) in the scatter rows over the scatter frames; the heavier side is kept
out from that frame edge to the torso strip edge - 24 px (strip union over the scattered frames b1-9 .. b1-4). Override 'left' | 'right' | 'none' | (x0, y0, x1, y1)
(storyboard intro.smash_keep_out). As in the approved r7-05 build, the keep-out binds the scattered pose
(b1-9 .. b1-4); the fly frames head for the fixed spaced row and the solver only prefers them out of it.

    python3 scripts/intro_smash.py selftest --out output/visuals/round7_prod/R7P-02/

No HyperFrames, Node or Chrome. Pure functions on PIL images; no style_fx import at module level.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
GOLD = (212, 160, 23)                         # colours.gold #D4A017
GOLD_MAX = (236, 212, 151)                    # colours.gold_highlight_max #ECD497
E = (1, 0.8, 0.55, 0.3, 0.12, 0)              # title_styles.pulse e
# title_styles.smash (style sheet) / r7-05 hf/build.py
SEED, TRIALS = 0x0C5E2026, 3000
SCATTER_SCALE = 0.82
MAX_DX, MAX_DY, MAX_ROT = 180, 120, 12
X_RANGE = (60, 1020)
SAFE_BOTTOM = 1500
FACE_MARGIN = 40
MIN_GAP, TARGET_GAP = 24, 30
SHRINK_STEPS = (1.0, 0.75, 0.5, 0.25)
S_ROW = 0.90                                  # spaced-row scale on b1-1
MIN_GAP_ROW = 40                              # MIN_GAP_F19
SCATTER_GAP = 40                              # build.py: gap while sampling the scattered pose
MARGIN = 10                                   # build.py: inner margin of the allowed box
KEEP_GAP = 24                                 # keep-out ends 24 px short of the torso strip
STRIP = 0.6                                   # torso strip half width, in head-box widths
SHAKE = ((6, -3), (-4, 2), (2, -1), (0, 0))   # b1 .. b1+3
FADE_FROM, FADE_N = 10, 5                     # opacity (k - (b1-10)) / 5 on b1-9 .. b1-5
FLY_N = 3                                     # b1-3, b1-2, b1-1


class IntroUnfit(SystemExit):
    """The title style cannot be drawn cleanly for this video (re-exported as style_fx.IntroStyleUnfit)."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"intro smash unfit: {reason}")


# ---------- geometry (r7-05 hf/build.py) ----------
def _box(g, dx, dy, rot, s):
    """Axis-aligned box of the glyph's ink box after scale s + rotation about (50 % adv, 55 % height) + shift."""
    ox, oy = g["x"] + g["adv"] * 0.5, g["y"] + g["h"] * 0.55
    l, t, r, b = g["ink"]
    pts = [(g["x"] + l, g["y"] + t), (g["x"] + r, g["y"] + t), (g["x"] + l, g["y"] + b), (g["x"] + r, g["y"] + b)]
    a = math.radians(rot)
    out = []
    for px, py in pts:
        vx, vy = (px - ox) * s, (py - oy) * s
        out.append((ox + vx * math.cos(a) - vy * math.sin(a) + dx, oy + vx * math.sin(a) + vy * math.cos(a) + dy))
    xs, ys = [p[0] for p in out], [p[1] for p in out]
    return min(xs), min(ys), max(xs), max(ys)


def _gap(a, b):
    """Gap between two axis-aligned boxes (px); negative = overlap."""
    return max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])


def _back_out(t, p=1.7):
    t -= 1
    return t * t * ((p + 1) * t + p) + 1


def _cubic_out(t):
    return 1 - (1 - t) ** 3


def _layout(lines, font, line_centres_y):
    """Glyph pen positions exactly as style_fx._line (centred line, prefix getlength); spaces skipped."""
    asc, desc = font.getmetrics()
    hb = font.getbbox("H")
    glyphs = []
    for li, (text, cy) in enumerate(zip(lines, line_centres_y)):
        bb = font.getbbox(text)
        x0 = W // 2 - (bb[2] - bb[0]) // 2 - bb[0]
        y = cy - (hb[3] + hb[1]) // 2
        for i, c in enumerate(text):
            if c.isspace():
                continue
            glyphs.append(dict(line=li, ch=c, x=x0 + font.getlength(text[:i]), y=y, adv=font.getlength(c),
                               ink=font.getbbox(c), h=asc + desc))
    return glyphs


def _row_dx(glyphs):
    """b1-1 pose: each line spread about x 540 so neighbours keep 40 px between ink boxes at scale 0.90."""
    out = {}
    for line in sorted({g["line"] for g in glyphs}):
        idx = [i for i, g in enumerate(glyphs) if g["line"] == line]
        dx = [0.0]
        for a, b in zip(idx, idx[1:]):
            ba = _box(glyphs[a], dx[-1], 0, 0, S_ROW)
            bb = _box(glyphs[b], 0, 0, 0, S_ROW)
            dx.append(ba[2] + MIN_GAP_ROW - bb[0])
        boxes = [_box(glyphs[i], d, 0, 0, S_ROW) for i, d in zip(idx, dx)]
        shift = W / 2 - (boxes[0][0] + boxes[-1][2]) / 2
        for i, d in zip(idx, dx):
            out[i] = d + shift
    return [out[i] for i in range(len(glyphs))]


def _poses(sc, xrow, b1):
    """{frame: [(dx, dy, rot, scale) per glyph]} for b1-9 .. b1-1 (b1 = home, drawn from tl)."""
    P = {}
    f0 = b1 - FADE_FROM
    for k in range(f0 + 1, b1 - FLY_N):
        P[k] = [(r[0], r[1], r[2], SCATTER_SCALE) for r in sc]
    for j, k in enumerate(range(b1 - FLY_N, b1), 1):
        t = j / FLY_N
        e = _back_out(t)
        P[k] = [(r[0] + (x9 - r[0]) * e, r[1] * (1 - e), r[2] * (1 - e),
                 SCATTER_SCALE + (S_ROW - SCATTER_SCALE) * _cubic_out(t)) for r, x9 in zip(sc, xrow)]
    return P


def _frame_boxes(glyphs, pose):
    return [_box(g, *p) for g, p in zip(glyphs, pose)]


def _min_gap(bx):
    return min((_gap(bx[i], bx[j]) for i in range(len(bx)) for j in range(i + 1, len(bx))), default=float("inf"))


def _outside(b, ko):
    return ko is None or b[0] >= ko[2] or b[2] <= ko[0] or b[1] >= ko[3] or b[3] <= ko[1]


# ---------- keep-out ----------
def _strips(heads, frames):
    out = []
    for k in frames:
        hb = heads[k] if 0 <= k < len(heads) else None
        if hb:
            cx, hw = (hb[0] + hb[2]) / 2, hb[2] - hb[0]
            out.append((k, cx - STRIP * hw, cx + STRIP * hw))
    return out


def _side_keep_out(side, strips):
    if side == "left":
        return (0, 0, int(round(max(s[1] for s in strips) - KEEP_GAP)), H)
    return (int(round(min(s[2] for s in strips) + KEEP_GAP)), 0, W, H)


def auto_side(heads, masks, frames, rows):
    """('left' | 'right' | None, left px, right px): heavier side of his mask beside the torso strip."""
    strips = _strips(heads, frames)
    lpx = rpx = 0
    y0, y1 = max(0, int(rows[0])), min(H, int(rows[1]))
    for k, sl, sr in strips:
        m = masks[k][y0:y1]
        lpx += int(m[:, :max(0, int(round(sl)))].sum())
        rpx += int(m[:, min(W, int(round(sr))):].sum())
    if not strips or lpx == rpx:
        return None, lpx, rpx
    return ("left" if lpx > rpx else "right"), lpx, rpx


# ---------- pulse maths (identical to style_fx._tint / _scaled) ----------
def _tint(layer, rgb):
    r = Image.new("RGBA", layer.size, tuple(rgb) + (0,))
    r.putalpha(layer.getchannel("A"))
    return r


def _scaled(layer, s, cx, cy):
    if abs(s - 1) < 1e-3:
        return layer
    big = layer.resize((int(round(W * s)), int(round(H * s))), Image.BICUBIC)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(big, (int(round(cx - cx * s)), int(round(cy - cy * s))), big)
    return out


def _pulse(tl, k, beats, gcx, gcy):
    """The pulse (tint 0.55 e, scale 1 + 0.06 e about the group centre) with the style_fx maths, then the RGB
    reset to that frame's one flat colour (alpha untouched, as r7-05 tools/fix_edges.py): PIL's premultiplied
    bicubic resize overshoots the RGB at the letter edges (up to (253,228,161) on a peak frame), the reset keeps
    every title pixel <= #ECD497."""
    for b in beats[1:]:
        d = k - b
        if 0 <= d < 6:
            e = E[d]
            amt, sc = 0.55 * e, 1.0 + 0.06 * e
            g = np.array(GOLD, np.float32)
            rgb = [int(v) for v in g + (255 - g) * amt] if amt else list(GOLD)
            t = _tint(tl, rgb) if amt else tl
            t = _scaled(t, sc, gcx, gcy)
            if t is tl:
                return tl
            arr = np.array(t)
            arr[..., :3] = rgb
            arr[arr[..., 3] == 0] = 0
            return Image.fromarray(arr, "RGBA")
    return tl


class SmashPlan:
    """Solved scatter for one title on one video; draws the title layer per frame."""

    def __init__(self):
        self.glyphs, self.poses, self.sc, self.xrow = [], {}, [], []
        self._tiles, self._cache = {}, {}

    # ----- solver -----
    @classmethod
    def build(cls, lines, font_path, size, line_centres_y, tl, heads, masks, b1, n, keep_out=None,
              extra_face=None) -> "SmashPlan":
        if b1 < 10:
            raise IntroUnfit(f"beat 1 is on frame {b1}; the smash needs 10 frames before it (fade b1-9..b1-5, "
                             "fly b1-3..b1-1)")
        if b1 >= n:
            raise IntroUnfit(f"beat 1 (frame {b1}) is outside the {n}-frame window")
        p = cls()
        p.lines, p.size, p.b1, p.n = list(lines), int(size), int(b1), int(n)
        p.font_path = str(font_path)
        p.font = ImageFont.truetype(p.font_path, p.size)
        cys = list(line_centres_y)
        p.gc = (W / 2, (cys[0] + cys[-1]) / 2)
        p.glyphs = _layout(p.lines, p.font, cys)
        if not p.glyphs:
            raise IntroUnfit("the title has no letters")
        frames = list(range(b1 - 9, b1))
        p.scatter_frames = frames
        faces = [heads[k] for k in frames if 0 <= k < len(heads) and heads[k]] + ([tuple(extra_face)] if extra_face else [])
        ylo = max([f[3] for f in faces], default=0) + FACE_MARGIN
        ylo = max(ylo, 110)                                        # safe top
        p.y_range = (int(ylo), SAFE_BOTTOM)
        p.faces = faces
        if p.y_range[1] - p.y_range[0] < 2 * MARGIN:
            raise IntroUnfit(f"no room for the scattered letters: his face reaches y={ylo - FACE_MARGIN}, the "
                             f"letters must stay above y={SAFE_BOTTOM}")
        # keep-out
        side, p.mask_left_px, p.mask_right_px = auto_side(heads, masks, frames, p.y_range)
        held = frames[:-FLY_N]                   # b1-9 .. b1-4: the frames the keep-out binds (scattered pose)
        if keep_out is None:
            p.keep_out_source = "auto"
            kind = side
            p.keep_out = _side_keep_out(side, _strips(heads, held) or _strips(heads, frames)) if side else None
        elif isinstance(keep_out, str):
            ko = keep_out.lower()
            if ko not in ("left", "right", "none"):
                raise ValueError(f"smash keep_out: {keep_out!r} (left | right | none | x0,y0,x1,y1)")
            p.keep_out_source = "none" if ko == "none" else "storyboard"
            kind = None if ko == "none" else ko
            if kind:
                st = _strips(heads, held) or _strips(heads, frames)
                if not st:
                    raise IntroUnfit(f"keep-out {kind!r} needs his head in the scatter frames to find the torso")
                p.keep_out = _side_keep_out(kind, st)
            else:
                p.keep_out = None
        else:
            b = tuple(int(v) for v in keep_out)
            p.keep_out_source = "storyboard"
            p.keep_out = b
            kind = "left" if (b[0] <= 0 and b[1] <= 0 and b[3] >= H) else \
                   "right" if (b[2] >= W and b[1] <= 0 and b[3] >= H) else "box"
        p.keep_out_kind = kind
        p._solve()
        return p

    def _inside(self, b):
        return (b[0] >= X_RANGE[0] + MARGIN and b[2] <= X_RANGE[1] - MARGIN and
                b[1] >= self.y_range[0] + MARGIN and b[3] <= self.y_range[1] - MARGIN)

    def _term(self, P):
        """Prefer the fly frames (b1-3, b1-2) out of the keep-out (build.py: 0.2 * min(left, SCATTER_X_MIN))."""
        ko, kind = self.keep_out, self.keep_out_kind
        if ko is None:
            return 0.0
        bx = [b for k in (self.b1 - 3, self.b1 - 2) for b in _frame_boxes(self.glyphs, P[k])]
        if kind == "left":
            return 0.2 * min(min(b[0] for b in bx), ko[2])
        if kind == "right":
            return 0.2 * min(W - max(b[2] for b in bx), W - ko[0])
        return 0.2 * min(min(_gap(b, ko) for b in bx), 0.0)

    def _solve(self):
        glyphs, ko = self.glyphs, self.keep_out
        xrow = _row_dx(glyphs)
        row = _frame_boxes(glyphs, [(x, 0, 0, S_ROW) for x in xrow])
        bad = [g["ch"] for g, b in zip(glyphs, row) if not self._inside(b)]
        if bad:
            raise IntroUnfit(f"the spaced row on b1-1 does not fit x {X_RANGE[0]}-{X_RANGE[1]} / y "
                             f"{self.y_range[0]}-{self.y_range[1]} (letters {''.join(bad)})")
        self.tried = []
        for shrink in SHRINK_STEPS:
            mdx, mdy, mrot = MAX_DX * shrink, MAX_DY * shrink, MAX_ROT * shrink
            rng = np.random.default_rng(SEED)
            best = None
            for trial in range(TRIALS):
                sc = []
                for g in glyphs:
                    for _ in range(400):
                        r = (float(rng.uniform(-mdx, mdx)), float(rng.uniform(-mdy, mdy)),
                             float(rng.uniform(-mrot, mrot)))
                        b = _box(g, r[0], r[1], r[2], SCATTER_SCALE)
                        if self._inside(b) and _outside(b, ko) and all(
                                _gap(b, _box(h, *q, SCATTER_SCALE)) >= SCATTER_GAP for h, q in zip(glyphs, sc)):
                            sc.append(r)
                            break
                    else:
                        break
                if len(sc) < len(glyphs):
                    continue
                P = _poses(sc, xrow, self.b1)
                if any(not self._inside(b) for k in P for b in _frame_boxes(glyphs, P[k])):
                    continue
                mg = {k: _min_gap(_frame_boxes(glyphs, P[k])) for k in P}
                lo = min(mg.values())
                score = min(lo, TARGET_GAP + 30) + self._term(P)
                if lo >= TARGET_GAP and (best is None or score > best[0]):
                    best = (score, sc, mg, trial)
            self.tried.append(shrink)
            if best:
                _, self.sc, self.mg, self.trial = best
                self.shrink, self.xrow = shrink, xrow
                self.poses = _poses(self.sc, xrow, self.b1)
                return
        raise IntroUnfit(f"no scatter with >= {TARGET_GAP} px between letters below his face (y "
                         f"{self.y_range[0]}-{self.y_range[1]}), inside x {X_RANGE[0]}-{X_RANGE[1]} and off the "
                         f"keep-out {self.keep_out} at shrink {SHRINK_STEPS[-1]}")

    # ----- drawing -----
    def _tile(self, i):
        """Glyph i as a gold RGBA tile drawn at its fractional pen x (like inside the full-line render)."""
        if i not in self._tiles:
            g = self.glyphs[i]
            l, t, r, b = g["ink"]
            pad = 4
            fx = math.floor(g["x"])
            frac = g["x"] - fx
            tw, th = int(math.ceil(r - l + frac)) + 2 * pad, int(b - t) + 2 * pad
            m = Image.new("L", (tw, th), 0)
            ImageDraw.Draw(m).text((pad - l + frac, pad - t), g["ch"], font=self.font, fill=255)
            tile = Image.new("RGBA", (tw, th), GOLD + (0,))
            tile.putalpha(m)
            self._tiles[i] = (tile, (fx + l - pad, g["y"] + t - pad))
        return self._tiles[i]

    def glyph_layer(self, i, pose, opacity=1.0, into=None):
        g = self.glyphs[i]
        dx, dy, rot, s = pose
        tile, (tx, ty) = self._tile(i)
        out = into if into is not None else Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ox, oy = g["x"] + g["adv"] * 0.5, g["y"] + g["h"] * 0.55
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        corners = []
        for u, v in ((0, 0), (tile.width, 0), (0, tile.height), (tile.width, tile.height)):
            vx, vy = (tx + u - ox) * s, (ty + v - oy) * s
            corners.append((ox + vx * ca - vy * sa + dx, oy + vx * sa + vy * ca + dy))
        rx0 = max(0, int(math.floor(min(c[0] for c in corners))) - 2)
        ry0 = max(0, int(math.floor(min(c[1] for c in corners))) - 2)
        rx1 = min(W, int(math.ceil(max(c[0] for c in corners))) + 2)
        ry1 = min(H, int(math.ceil(max(c[1] for c in corners))) + 2)
        if rx1 <= rx0 or ry1 <= ry0:
            return out
        vx, vy = rx0 - ox - dx, ry0 - oy - dy
        data = (ca / s, sa / s, ox - tx + (ca * vx + sa * vy) / s,
                -sa / s, ca / s, oy - ty + (-sa * vx + ca * vy) / s)
        reg = tile.transform((rx1 - rx0, ry1 - ry0), Image.AFFINE, data, resample=Image.BICUBIC)
        arr = np.array(reg)
        arr[..., :3] = GOLD
        if opacity < 1:
            arr[..., 3] = (arr[..., 3].astype(np.float32) * opacity).astype(np.uint8)
        out.alpha_composite(Image.fromarray(arr, "RGBA"), (rx0, ry0))
        return out

    def opacity(self, k):
        return min(1.0, max(0.0, (k - (self.b1 - FADE_FROM)) / FADE_N))

    def scattered(self, k):
        if k not in self._cache:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            o = self.opacity(k)
            for i, p in enumerate(self.poses[k]):
                self.glyph_layer(i, p, o, lay)
            self._cache[k] = lay
        return self._cache[k]

    def title(self, k, tl, beats):
        """Full title layer at frame k (None = nothing drawn)."""
        b1 = self.b1
        if k < b1 - 9:
            return None
        if k < b1:
            return self.scattered(k)
        lay = _pulse(tl, k, beats, *self.gc)
        d = k - b1
        if d < len(SHAKE) and SHAKE[d] != (0, 0):
            out = Image.new("RGBA", (W, H), (0, 0, 0, 0))     # exact integer shift of the whole title layer
            out.alpha_composite(lay.crop((max(0, -SHAKE[d][0]), max(0, -SHAKE[d][1]), W, H)),
                                (max(0, SHAKE[d][0]), max(0, SHAKE[d][1])))
            return out
        return lay

    # ----- report -----
    def boxes(self, k):
        return _frame_boxes(self.glyphs, self.poses[k])

    def stats(self) -> dict:
        return {"keep_out": list(self.keep_out) if self.keep_out else None,
                "keep_out_source": self.keep_out_source,
                "scatter_shrink": self.shrink,
                "min_glyph_gap_px": round(min(self.mg.values()), 1),
                "land_frame": self.b1,
                "shake_frames": [self.b1 + i for i in range(len(SHAKE))],
                "scatter_y_range": list(self.y_range)}

    def to_json(self) -> dict:
        return {"lines": self.lines, "size": self.size, "b1": self.b1, "n": self.n, "seed": SEED,
                "trial": self.trial, "shrink": self.shrink, "keep_out_kind": self.keep_out_kind,
                "mask_px_left_right": [self.mask_left_px, self.mask_right_px],
                "faces_used": [list(f) for f in self.faces],
                "glyphs": [g["ch"] for g in self.glyphs],
                "pen_x": [round(g["x"], 3) for g in self.glyphs],
                "scatter_dx_dy_rot": [[round(v, 2) for v in r] for r in self.sc],
                "row_dx": [round(v, 2) for v in self.xrow],
                "opacity": {f"f{k}": round(self.opacity(k), 3) for k in self.poses},
                "poses": {f"f{k}": [[round(v, 3) for v in p] for p in self.poses[k]] for k in self.poses},
                "boxes": {f"f{k}": [[round(v) for v in b] for b in self.boxes(k)] for k in self.poses},
                "min_gap_px": {f"f{k}": round(v, 1) for k, v in self.mg.items()},
                "stats": self.stats()}


# ---------- selftest (Locked In vs the r7-05 golden) ----------
def _selftest(out):
    import hashlib
    import json
    import sys
    import time
    from pathlib import Path
    from scipy import ndimage
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "scripts"))
    import style_fx as sf
    out = Path(out)
    (out / "frames").mkdir(parents=True, exist_ok=True)
    (out / "plans").mkdir(exist_ok=True)
    r7 = root / "output" / "style_lab" / "r7"
    n, beats = 90, [20, 40, 60, 80]
    b1 = beats[0]
    spec = sf.TitleSpec("LOCKED IN", "5 LIFTS. ONE SONG.", sf.TITLE_W)
    tl, _sub, (gcx, gcy) = spec.layers()
    cys, _ = spec.centres()
    masks = [np.asarray(Image.open(r7 / "r7-00" / "masks" / f"m{k:04d}.png").convert("L")) > 128 for k in range(n)]
    heads = [sf.head_box(m) for m in masks]
    res = {"title": spec.lines, "size": spec.size, "line_centres_y": cys, "group_centre": [gcx, gcy],
           "beats": beats, "heads_scatter_frames": {f"f{k}": heads[k] for k in range(b1 - 9, b1)}}

    def build(**kw):
        t0 = time.time()
        p = SmashPlan.build(spec.lines, sf.TITLE_FONT, spec.size, cys, tl, heads, masks, b1, n, **kw)
        return p, round(time.time() - t0, 1)

    plan, secs = build()
    res["auto"] = {"stats": plan.stats(), "side": plan.keep_out_kind, "solve_s": secs,
                   "mask_px_left_right": [plan.mask_left_px, plan.mask_right_px]}
    (out / "plan.json").write_text(json.dumps(plan.to_json(), indent=1))
    ko = plan.keep_out
    res["auto"]["keep_out_end_x_in_260_380"] = bool(ko and plan.keep_out_kind == "left" and 260 <= ko[2] <= 380)

    # overrides (storyboard intro.smash_keep_out)
    ov = {}
    for name, kw in (("right", {"keep_out": "right"}), ("none", {"keep_out": "none"}),
                     ("box", {"keep_out": (760, 1000, 1080, 1500)}), ("left", {"keep_out": "left"})):
        try:
            p, s = build(**kw)
            (out / "plans" / f"plan_{name}.json").write_text(json.dumps(p.to_json(), indent=1))
            ov[name] = {"ok": True, "stats": p.stats(), "trial": p.trial, "solve_s": s}
        except IntroUnfit as e:
            ov[name] = {"ok": False, "unfit": e.reason}
    res["overrides"] = ov

    # golden replay: the r7-05 build's own constants through the same solver (SCATTER_X_MIN 300 as a left
    # keep-out box, title band top 860 = a face box ending at 820 + 40)
    rp, s = build(keep_out=(0, 0, 300, H), extra_face=(400, 170, 900, 820))
    (out / "plans" / "plan_golden_replay.json").write_text(json.dumps(rp.to_json(), indent=1))
    ref_tab = json.loads((r7 / "r7-05" / "hf" / "scatter_table.json").read_text())
    rj = rp.to_json()
    res["golden_replay"] = {"trial": rp.trial, "ref_trial": ref_tab["trial"],
                            "scatter_equal": rj["scatter_dx_dy_rot"] == ref_tab["scatter_dx_dy_rot"],
                            "row_dx_equal": rj["row_dx"] == ref_tab["f19_dx"], "solve_s": s}

    # unfit
    unfit = {}
    for name, fn in (("b1_8", lambda: SmashPlan.build(spec.lines, sf.TITLE_FONT, spec.size, cys, tl, heads, masks,
                                                       8, n)),
                     ("face_over_band", lambda: build(extra_face=(0, 0, W, 1500)))):
        try:
            fn()
            unfit[name] = {"raised": False}
        except IntroUnfit as e:
            unfit[name] = {"raised": True, "reason": e.reason, "is_SystemExit": isinstance(e, SystemExit)}
    res["unfit"] = unfit

    # render
    def render(p):
        fr = []
        for k in range(n):
            t = p.title(k, tl, beats)
            fr.append(np.asarray(t) if t is not None else np.zeros((H, W, 4), np.uint8))
        return fr

    t0 = time.time()
    ours = render(plan)
    res["render_s_90"] = round(time.time() - t0, 1)
    for k, a in enumerate(ours):
        Image.fromarray(a, "RGBA").save(out / "frames" / f"title_{k:04d}.png")
    plan2, _ = build()
    again = render(plan2)
    res["deterministic"] = all(np.array_equal(a, b) for a, b in zip(ours, again)) and \
        plan2.to_json() == plan.to_json()
    res["md5_frames"] = hashlib.md5(b"".join(a.tobytes() for a in ours)).hexdigest()
    rep = render(rp)

    gold = [np.asarray(Image.open(r7 / "r7-05" / "overlay" / f"frame_{k + 1:06d}.png").convert("RGBA")) for k in range(n)]
    yy = np.arange(H)[:, None]

    def tmask(a, thr=20):
        return (a[..., 3] > thr) & (yy < 1260)

    def bbox(m):
        ys, xs = np.nonzero(m)
        return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None

    def iou(a, b):
        u = (a | b).sum()
        return float((a & b).sum() / u) if u else 1.0

    # 1. land / shake / rest
    tla = np.asarray(tl)[..., 3]
    land = {}
    for d, (sx, sy) in enumerate(SHAKE):
        a = ours[b1 + d][..., 3]
        back = np.roll(np.roll(a, -sy, 0), -sx, 1)
        land[f"f{b1 + d}"] = {"shake": [sx, sy], "bbox": bbox(a > 20),
                              "unshaken_alpha_equal_tl": bool(np.array_equal(back, tla))}
    res["land"] = land
    res["f19_to_f20_visible_both"] = [bool(ours[b1 - 1][..., 3].any()), bool(ours[b1][..., 3].any())]
    tref = np.asarray(Image.open(r7 / "r7-00" / "ref" / "title_ref.png"))
    refbb = bbox(tref[..., 3] > 20)
    pulse_frames = {b + d for b in beats[1:] for d in range(6) if E[d] and b + d < n}
    rest = {}
    for k in range(b1 + 3, n):
        if k in pulse_frames:
            continue
        bb = bbox(tmask(ours[k]))
        rest[k] = max(abs(u - v) for u, v in zip(bb, refbb))
    res["rest_vs_title_ref"] = {"ref_bbox": refbb, "max_dev_px_f23_on": max(rest.values()),
                                "pulse_frames_excluded": sorted(pulse_frames),
                                "frames_over_2": [k for k, v in rest.items() if v > 2]}
    res["tl_equals_title_ref"] = bool(np.array_equal(np.asarray(tl), tref))

    # 2. IoU vs golden from b1
    def sil(a):                        # alpha > 20, grit holes (< 500 px) filled (intro_glitch._silhouette)
        ink = a
        holes = ndimage.binary_fill_holes(ink) & ~ink
        lab, nl = ndimage.label(holes)
        return ink | ((np.bincount(lab.ravel()) < 500)[lab] & (lab > 0)) if nl else ink

    ious = {k: iou(tmask(ours[k]), tmask(gold[k])) for k in range(b1, n)}
    sious = {k: iou(sil(tmask(ours[k])), sil(tmask(gold[k]))) for k in range(b1, n)}
    ceil = iou(tmask(tref), tmask(gold[35]))          # rest-pose limit (as R7P-01: title_ref vs golden f35)
    # pulse frames: the limit is the unchanged production pulse layer (style_fx maths on title_ref) vs the golden
    limits = {}
    for k in range(b1, n):
        if k in pulse_frames:
            st = sf.title_state("pulse", k, beats)
            t = Image.fromarray(tref, "RGBA")
            if st[0]:
                g_ = np.array(sf.GOLD, np.float32)
                t = sf._tint(t, [int(v) for v in g_ + (255 - g_) * st[0]])
            limits[k] = iou(tmask(np.asarray(sf._scaled(t, st[1], gcx, gcy))), tmask(gold[k]))
        else:
            limits[k] = ceil
    raw_fail = [k for k in range(b1, n) if ious[k] < round(limits[k] - 0.02, 4)]
    bbd = {k: max(abs(u - v) for u, v in zip(bbox(tmask(ours[k])), bbox(tmask(gold[k])))) for k in range(b1, n)}
    res["golden_from_b1"] = {"iou_min": round(min(ious.values()), 4), "iou_min_frame": min(ious, key=ious.get),
                             "bbox_dev_max_px": max(bbd.values()),
                             "silhouette_iou_min": round(min(sious.values()), 4),
                             "silhouette_iou_min_frame": min(sious, key=sious.get),
                             "title_ref_vs_golden_f35_raw_iou": round(ceil, 4),
                             "raw_iou_floor_rest": round(ceil - 0.02, 4),
                             "raw_iou_floor_pulse_frames": {f"f{k}": round(limits[k] - 0.02, 4) for k in sorted(pulse_frames)},
                             "raw_iou_frames_below_floor": raw_fail,
                             "rule": "silhouette IoU (alpha > 20, grit holes < 500 px filled) >= 0.95 and bbox dev <= 3 px on "
                                     "every frame from b1 (title rows y < 1260); raw alpha IoU reported, must be >= "
                                     "limit - 0.02 (limit = title_ref vs golden f35 at rest; on pulse frames the "
                                     "production pulse layer of title_ref vs the golden frame)",
                             "reason": "rasteriser difference: PIL vs Chrome; rest pose must equal production title_ref",
                             "decision": "Director, R7P-02 (same method as R7P-01 Option A; replaces alpha_iou_min 0.97)",
                             "per_frame_iou_f20_30": {f"f{k}": round(ious[k], 4) for k in range(b1, b1 + 11)}}

    # 3. scattered glyph centres vs golden (identify golden glyphs with the replay plan's glyph masks)
    def centroid(a):
        w = a.astype(np.float64)
        s = w.sum()
        if not s:
            return None
        ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        return (float((xs * w).sum() / s), float((ys * w).sum() / s))

    cen = {"auto": {}, "golden_replay": {}}
    for k in range(b1 - 9, b1):
        g = gold[k][..., 3] * (yy < 1260)
        lab, nl = ndimage.label(ndimage.binary_dilation(g > 20, iterations=3))
        for name, p in (("auto", plan), ("golden_replay", rp)):
            devs = []
            for i in range(len(p.glyphs)):
                mi = np.asarray(rp.glyph_layer(i, rp.poses[k][i]))[..., 3] > 20     # identity from the replay pose
                ids = np.bincount(lab[mi], minlength=nl + 1)
                ids[0] = 0
                gc = centroid(np.where(lab == ids.argmax(), g, 0)) if ids.max() else None
                oc = centroid(np.asarray(p.glyph_layer(i, p.poses[k][i]))[..., 3])
                devs.append(round(math.hypot(gc[0] - oc[0], gc[1] - oc[1]), 2) if gc and oc else None)
            cen[name][f"f{k}"] = devs
    for name in cen:
        allv = [v for f in cen[name].values() for v in f if v is not None]
        cen[name] = {"max_dev_px": max(allv), "per_frame": cen[name]}
    res["scatter_centres_vs_golden"] = cen

    # 4. constraints on the scattered / fly frames (rendered pixels and solver boxes)
    def faces_of(p, k):
        return [h for h in ([heads[k]] + [f for f in p.faces]) if h]

    def check(p, fr, label):
        chk = {"min_gap_px_boxes": {}, "min_gap_px_rendered": {}, "outside_x": 0, "outside_y": 0,
               "keep_out_px_scattered": 0, "keep_out_px_fly": 0, "face_px": 0, "safe_px": 0}
        ko = p.keep_out
        for k in range(b1 - 9, b1):
            chk["min_gap_px_boxes"][f"f{k}"] = round(_min_gap(p.boxes(k)), 1)
            rb = [bbox(np.asarray(p.glyph_layer(i, p.poses[k][i]))[..., 3] > 0) for i in range(len(p.glyphs))]
            chk["min_gap_px_rendered"][f"f{k}"] = round(_min_gap(rb), 1)
            m = fr[k][..., 3] > 20
            ys, xs = np.nonzero(m)
            chk["outside_x"] += int(((xs < X_RANGE[0]) | (xs >= X_RANGE[1])).sum())
            chk["outside_y"] += int(((ys < p.y_range[0]) | (ys >= SAFE_BOTTOM)).sum())
            if ko:
                inko = int(m[ko[1]:ko[3], ko[0]:ko[2]].sum())
                chk["keep_out_px_fly" if k >= b1 - 3 else "keep_out_px_scattered"] += inko
        for k in range(n):
            m = fr[k][..., 3] > 20
            ys, _ = np.nonzero(m)
            chk["safe_px"] += int(((ys < 110) | (ys > SAFE_BOTTOM)).sum())
            for h in faces_of(p, k):
                chk["face_px"] += int(m[h[1]:h[3], h[0]:h[2]].sum())
        chk["min_gap_rendered_px"] = min(chk["min_gap_px_rendered"].values())
        chk["min_gap_boxes_px"] = min(chk["min_gap_px_boxes"].values())
        return chk

    res["checks_auto"] = check(plan, ours, "auto")
    res["checks_golden_replay"] = check(rp, rep, "replay")

    # 5. pulse / brightness / equality with the style_fx pulse layer
    mx, peaks = {}, []
    for k in range(n):
        a = ours[k]
        sel = a[..., 3] > 128
        mx[k] = a[sel][:, :3].max(0).tolist() if sel.any() else None
    over = [k for k, v in mx.items() if v and any(c > m for c, m in zip(v, GOLD_MAX))]
    for b in beats[1:]:
        seq = [sum(mx[k]) for k in range(b - 2, min(n, b + 6))]
        peaks.append(b - 2 + int(np.argmax(seq)))
    nongold = [k for k, v in mx.items() if v and v != list(GOLD)]
    pulse_eq = []
    for k in range(b1 + 8, n):
        st = sf.title_state("pulse", k, beats)
        t = tl
        if st[0]:
            g = np.array(sf.GOLD, np.float32)
            t = sf._tint(tl, [int(v) for v in g + (255 - g) * st[0]])
        pulse_eq.append(np.array_equal(np.asarray(sf._scaled(t, st[1], gcx, gcy))[..., 3], ours[k][..., 3]))
    sfp = []                           # the unchanged style_fx pulse layer on the peak frames (for the report)
    for b in beats[1:]:
        st = sf.title_state("pulse", b, beats)
        g = np.array(sf.GOLD, np.float32)
        a = np.asarray(sf._scaled(sf._tint(tl, [int(v) for v in g + (255 - g) * st[0]]), st[1], gcx, gcy))
        sel = a[..., 3] > 128
        sfp.append({"frame": b, "max_rgb": a[sel][:, :3].max(0).tolist(),
                    "px_over_ECD497": int((sel & (a[..., :3] > np.array(GOLD_MAX)).any(-1)).sum())})
    res["pulse"] = {"peak_frames": peaks, "frames_not_pure_gold": nongold, "frames_brighter_than_ECD497": over,
                    "brightest_rgb": max((v for v in mx.values() if v), key=sum),
                    "alpha_equals_style_fx_pulse_from_b1_8": all(pulse_eq),
                    "style_fx_pulse_unmodified_peaks": sfp}
    # glyph pen positions vs the full-line render (home pose, opacity 1)
    home = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(len(plan.glyphs)):
        plan.glyph_layer(i, (0, 0, 0, 1.0), 1.0, home)
    res["home_glyphs_vs_tl_iou"] = round(iou(np.asarray(home)[..., 3] > 20, tla > 20), 4)

    # 6. contact sheet f10-23: ours (with head box + keep-out) over the plate, golden below
    cells, row2 = [], []
    x0c, y0c, x1c, y1c = 0, 120, W, 1520
    sc_ = 0.25
    for k in range(b1 - 10, b1 + 4):
        plate = Image.open(r7 / "r7-00" / "plate" / f"p{k:04d}.png").convert("RGBA")
        for arr, dst, draw_boxes in ((ours[k], cells, True), (gold[k], row2, False)):
            c = Image.alpha_composite(plate, Image.fromarray(arr, "RGBA"))
            d = ImageDraw.Draw(c)
            if draw_boxes:
                if heads[k]:
                    d.rectangle(heads[k], outline=(255, 0, 0, 255), width=5)
                if plan.keep_out:
                    d.rectangle(plan.keep_out, outline=(0, 200, 255, 255), width=5)
                d.line([(0, plan.y_range[0]), (W, plan.y_range[0])], fill=(255, 0, 255, 255), width=3)
            c = c.crop((x0c, y0c, x1c, y1c)).resize((int(W * sc_), int((y1c - y0c) * sc_)), Image.LANCZOS)
            ImageDraw.Draw(c).text((6, 6), f"f{k}" + ("" if draw_boxes else " golden"), fill=(255, 255, 0, 255))
            dst.append(c)
    cw, ch = cells[0].size
    sheet = Image.new("RGB", (cw * len(cells), ch * 2 + 4), (40, 40, 40))
    for i, (a, b) in enumerate(zip(cells, row2)):
        sheet.paste(a.convert("RGB"), (i * cw, 0))
        sheet.paste(b.convert("RGB"), (i * cw, ch + 4))
    sheet.save(out / "sheet.png")

    acc = {
        "auto_left_end_260_380": res["auto"]["keep_out_end_x_in_260_380"],
        "overrides_no_crash": all(("ok" in v) for v in ov.values()),
        "gaps_ge_24": res["checks_auto"]["min_gap_boxes_px"] >= MIN_GAP and res["checks_auto"]["min_gap_rendered_px"] >= MIN_GAP,
        "inside_x_y_face_safe": not any(res["checks_auto"][k] for k in ("outside_x", "outside_y", "face_px", "safe_px")),
        "scattered_off_keep_out": res["checks_auto"]["keep_out_px_scattered"] == 0,
        "land_exact": all(v["unshaken_alpha_equal_tl"] for v in land.values()),
        "rest_bbox_le_2": res["rest_vs_title_ref"]["max_dev_px_f23_on"] <= 2,
        "golden_silhouette_iou_ge_095_from_b1": res["golden_from_b1"]["silhouette_iou_min"] >= 0.95,
        "golden_raw_iou_ge_floor_from_b1": not raw_fail,
        "golden_bbox_le_3_from_b1": res["golden_from_b1"]["bbox_dev_max_px"] <= 3,
        "scatter_centres_le_6_golden_replay": cen["golden_replay"]["max_dev_px"] <= 6,
        "pulse_peaks_40_60_80": peaks == beats[1:] and not over,
        "unfit_raises": all(v["raised"] for v in unfit.values()),
        "deterministic": res["deterministic"],
    }
    res["acceptance"] = acc
    res["acceptance_notes"] = {
        "scatter_centres": "Director R7P-02: per-video scatter accepted; the golden replay plan (r7-05 constants through "
                           "the same solver) must be within 6 px of the r7-05 golden on f11-19; the auto plan's "
                           "deviation is reported only (scatter_centres_vs_golden.auto)",
        "keep_out": "Director R7P-02: keep-out enforced on the scattered frames b1-9..b1-4 (0 px asserted); the fly "
                    "frames follow the approved r7-05 build (keep_out_px_fly reported only)"}
    res["ok"] = all(acc.values())
    (out / "golden_compare.json").write_text(json.dumps(res, indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o)))
    print(json.dumps(acc, indent=1))
    if not res["ok"]:
        raise SystemExit("selftest FAILED: " + ", ".join(k for k, v in acc.items() if not v))
    return res


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    st = sp.add_parser("selftest", help="Locked In vs the r7-05 golden")
    st.add_argument("--out", required=True)
    a = ap.parse_args()
    _selftest(a.out)
