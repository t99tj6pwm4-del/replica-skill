#!/usr/bin/env python3
"""CUTS AGENT tool. "Cut on motion" (Alfonso, 2026-11-23, Director standing answer 26).

Finds where something moves in a raw gym video (the bar, his arms, his body, the camera), which way it
moves (up / down), where each movement starts, and its first third, so every cut can land on motion.

    # (a) propose motion-safe cut points near a planned raw time
    python3 scripts/motion_cuts.py propose input/<video>.mp4 44.0 [--radius 0.5] [--crop-x 0.5]

    # (b) score an existing cut list (cut_map.json from cut_video.py) and write an audit
    python3 scripts/motion_cuts.py score [output/work/cut_map.json] [--source input/<video>.mp4]
                                         [--storyboard output/storyboard.json] [--out <audit>.md]

    # debug: per-frame motion for a raw window
    python3 scripts/motion_cuts.py track input/<video>.mp4 40.0 46.0

How it works (numpy only, low memory):
  - ffmpeg streams ONLY the window asked for, cropped to the same 9:16 frame the cut shows, scaled to
    180x320 grey; frames are read one at a time from the pipe and dropped (never a whole video in RAM).
    One ffmpeg at a time, 2 threads.
  - motion energy = mean absolute frame difference (lightly blurred), per frame and per cell (3x5 grid).
  - flow = phase correlation per cell between consecutive frames -> (dx, dy) per cell. The dominant
    vertical flow is the energy-weighted median dy of the cells that move. Most cells moving the same way
    = the camera is moving.
  - direction: dy < 0 = up, dy > 0 = down (image y grows downward). A "movement" is a run of frames with
    one direction; its start is where the rep / walk-in / grab begins and its first third is the cut zone
    (rule 5). Still stretches = energy under the still threshold for >= 0.25 s.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, OUT, WORK, die, load_json, probe, rel, resolve  # noqa: E402

AW, AH = 180, 320          # analysis size (portrait, after the 9:16 crop)
COLS, ROWS = 3, 5          # flow cells
STILL_E = 2.2              # busiest cell's mean |diff| (0-255 grey) under this = nothing moving
                           # (Grind Day: compression noise ~1.2, standing / breathing 1.5-2.0, reps 2.5-5)
NOISE_MULT = 1.7           # ...or under 1.7x the window's own noise floor (10th percentile), if that is higher
CELL_E = 2.0               # a cell moves when its own energy is over this
V_DIR = 0.35               # px/frame (at 180x320) of smoothed vertical flow to call a direction
MIN_RUN = 4                # frames: shortest movement
MIN_STILL = 0.25           # seconds: shortest still stretch
BEAT_SNAP_FRAMES = 3       # rule 6
FRAME = 1.0 / FPS

# what usually moves, by exercise name (labels only; the pixels decide moving / still / direction)
PART_HINTS = [("squat", "bar"), ("deadlift", "bar"), ("bench", "bar"), ("barbell", "bar"), ("row", "arms"),
              ("press", "arms"), ("curl", "arms"), ("pulldown", "arms"), ("pull", "arms"), ("raise", "body"),
              ("calf", "body"), ("lunge", "body"), ("fly", "arms"), ("extension", "arms"), ("dip", "body")]


def part_for(exercise: str | None) -> str:
    name = (exercise or "").lower()
    return next((p for k, p in PART_HINTS if k in name), "body")


# ---------------------------------------------------------------- frame stream + per-frame measures

def crop_filter(sw: int, sh: int, crop_x: float = 0.5, crop_y: float = 0.5) -> str:
    """The same 9:16 crop cut_video.video_filter uses, so we measure what the viewer sees."""
    target = 1080 / 1920
    if sw / sh > target + 1e-3:
        return f"crop=ih*{target:.6f}:ih:(iw-ih*{target:.6f})*{crop_x}:0"
    if sw / sh < target - 1e-3:
        return f"crop=iw:iw/{target:.6f}:0:(ih-iw/{target:.6f})*{crop_y}"
    return "null"


def stream_frames(src: Path, t0: float, t1: float, sw: int, sh: int, crop_x=0.5, crop_y=0.5):
    """Yield (raw_time, grey float32 AHxAW) one frame at a time. Only [t0, t1] is decoded."""
    t0 = max(0.0, t0)
    vf = f"{crop_filter(sw, sh, crop_x, crop_y)},fps={FPS},scale={AW}:{AH}:flags=area,format=gray"
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-threads", "2", "-ss", f"{t0:.4f}", "-i", str(src),
           "-t", f"{max(t1 - t0, FRAME):.4f}", "-an", "-sn", "-vf", vf, "-f", "rawvideo", "-"]
    size = AW * AH
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=size * 4)
    try:
        k = 0
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            yield t0 + k * FRAME, np.frombuffer(buf, dtype=np.uint8).reshape(AH, AW).astype(np.float32)
            k += 1
    finally:
        p.stdout.close()
        p.wait()


def _blur(g: np.ndarray) -> np.ndarray:
    p = np.pad(g, 1, mode="edge")
    return (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 1:-1] + p[1:-1, 2:]
            + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9.0


_CH, _CW = AH // ROWS, AW // COLS
_WIN = np.outer(np.hanning(_CH), np.hanning(_CW)).astype(np.float32)


def _phase_shift(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Translation (dy, dx) that moves cell a onto cell b, with the correlation peak (confidence)."""
    fa = np.fft.rfft2((a - a.mean()) * _WIN)
    fb = np.fft.rfft2((b - b.mean()) * _WIN)
    r = fb * np.conj(fa)
    r /= np.abs(r) + 1e-6
    c = np.fft.irfft2(r, s=a.shape)
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    peak = float(c[iy, ix])

    def sub(v_m, v_0, v_p):   # parabolic sub-pixel refinement
        d = v_m - 2 * v_0 + v_p
        return 0.0 if abs(d) < 1e-9 else 0.5 * (v_m - v_p) / d
    h, w = c.shape
    dy = iy + sub(c[iy - 1, ix], c[iy, ix], c[(iy + 1) % h, ix])
    dx = ix + sub(c[iy, ix - 1], c[iy, ix], c[iy, (ix + 1) % w])
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return float(dy), float(dx), peak


def frame_measures(prev: np.ndarray, cur: np.ndarray) -> dict:
    d = np.abs(cur - prev)
    energy = float(d.mean())
    cells = []
    for r in range(ROWS):
        for c in range(COLS):
            sl = (slice(r * _CH, (r + 1) * _CH), slice(c * _CW, (c + 1) * _CW))
            e = float(d[sl].mean())
            if e < CELL_E:
                cells.append((r, c, e, 0.0, 0.0, 0.0))
                continue
            dy, dx, pk = _phase_shift(prev[sl], cur[sl])
            cells.append((r, c, e, dy, dx, pk))
    moving = [x for x in cells if x[2] >= CELL_E and x[5] > 0.05]
    vy = vx = 0.0
    camera = False
    rows = []
    if moving:
        w = np.array([x[2] for x in moving])
        dys = np.array([x[3] for x in moving])
        dxs = np.array([x[4] for x in moving])
        order = np.argsort(dys)
        cw = np.cumsum(w[order])
        vy = float(dys[order][np.searchsorted(cw, cw[-1] / 2)])     # energy-weighted median
        vx = float(np.average(dxs, weights=w))
        rows = sorted({x[0] for x in moving})
        # camera: most of the frame moves, and the same way
        if len(moving) >= 0.7 * len(cells):
            if np.std(dys) < 1.0 and np.std(dxs) < 1.0 and (abs(np.median(dys)) > 0.4 or abs(np.median(dxs)) > 0.4):
                camera = True
    return {"energy": energy, "peak": max(x[2] for x in cells), "vy": vy, "vx": vx, "cells": len(moving), "camera": camera,
            "rows": (rows[0], rows[-1]) if rows else None}


# ---------------------------------------------------------------- a motion track for one raw window

@dataclass
class Move:
    start: int            # frame index in the track
    end: int              # exclusive
    dir: str              # "up" | "down"
    partial_start: bool   # began before the window (its real start is unknown)

    @property
    def third(self) -> int:
        return self.start + max(1, round((self.end - self.start) / 3))


@dataclass
class Track:
    src: str
    t0: float
    times: np.ndarray
    energy: np.ndarray    # smoothed, busiest cell per frame
    vy: np.ndarray        # smoothed, px/frame at 180x320, negative = up
    vx: np.ndarray
    camera: np.ndarray
    rows: list
    moves: list = field(default_factory=list)
    stills: list = field(default_factory=list)
    part: str = "body"
    still_e: float = STILL_E

    def idx(self, t: float) -> int:
        return int(min(len(self.times) - 1, max(0, round((t - self.t0) * FPS))))

    def covers(self, t: float) -> bool:
        return self.t0 - 1e-6 <= t <= self.t0 + (len(self.times) - 1) * FRAME + 1e-6

    def at(self, t: float) -> dict:
        """Everything a cut needs to know about raw time t in this window."""
        i = self.idx(t)
        e = float(self.energy[i])
        still = any(a <= i < b for a, b in self.stills) or e < self.still_e
        mv = next((m for m in self.moves if m.start <= i < m.end), None)
        dir_ = mv.dir if mv else None
        phase = None
        early = False
        if mv:
            phase = (i - mv.start) / max(1, mv.end - mv.start)
            early = (not mv.partial_start) and i < mv.third
        what = self.label(i, dir_, still)
        return {"t": round(float(self.times[i]), 3), "energy": round(e, 2), "still": bool(still),
                "moving": bool(not still), "dir": dir_, "phase": None if phase is None else round(phase, 2),
                "first_third": bool(early), "move_start": None if not mv else round(float(self.times[mv.start]), 3),
                "move_end": None if not mv else round(float(self.times[min(mv.end, len(self.times)) - 1]), 3),
                "camera": bool(self.camera[i]), "what": what}

    def label(self, i: int, dir_: str | None, still: bool) -> str:
        if still:
            return "still"
        if self.camera[i]:
            return "camera " + ("tilt " + dir_ if dir_ else "pan")
        rows = self.rows[i]
        part = self.part
        if rows and rows[1] - rows[0] >= 4 and part != "bar":
            part = "body"
        if not dir_:
            return f"{part} (side / small move)"
        return f"{part} {dir_}"


def _smooth(x: np.ndarray, k: int = 5) -> np.ndarray:
    if len(x) < k:
        return x.copy()
    pad = np.pad(x, k // 2, mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def track(src: Path, t0: float, t1: float, crop_x=0.5, crop_y=0.5, exercise: str | None = None,
          info: dict | None = None) -> Track:
    info = info or probe(src)
    sw, sh = info["video"]["width"], info["video"]["height"]
    t1 = min(t1, info["duration"] - FRAME)
    times, en, vy, vx, cam, rows = [], [], [], [], [], []
    prev = None
    for t, g in stream_frames(src, t0, t1, sw, sh, crop_x, crop_y):
        g = _blur(g)
        if prev is None:
            m = {"energy": 0.0, "peak": 0.0, "vy": 0.0, "vx": 0.0, "camera": False, "rows": None}
        else:
            m = frame_measures(prev, g)
        prev = g
        times.append(t)
        en.append(m["peak"])
        vy.append(m["vy"])
        vx.append(m["vx"])
        cam.append(m["camera"])
        rows.append(m["rows"])
    if len(times) > 1:
        en[0], vy[0], vx[0] = en[1], vy[1], vx[1]
    times = np.array(times)
    tr = Track(rel(src), float(times[0]) if len(times) else t0, times, _smooth(np.array(en)), _smooth(np.array(vy)),
               _smooth(np.array(vx)), np.array(cam, dtype=bool), rows, part=part_for(exercise))
    _segment(tr)
    return tr


def _segment(tr: Track) -> None:
    n = len(tr.times)
    if n:
        tr.still_e = max(STILL_E, NOISE_MULT * float(np.percentile(tr.energy, 10)))
    moving = tr.energy >= tr.still_e
    lab = np.where(~moving, 0, np.where(tr.vy <= -V_DIR, -1, np.where(tr.vy >= V_DIR, 1, 2)))
    # fill 1-2 frame gaps inside a direction run
    for i in range(1, n - 1):
        if lab[i] in (0, 2):
            j = i
            while j < n and lab[j] == lab[i] and j - i < 3:
                j += 1
            if j < n and j - i <= 2 and lab[i - 1] == lab[j] and lab[j] in (-1, 1):
                lab[i:j] = lab[j]
    i = 0
    while i < n:
        j = i
        while j < n and lab[j] == lab[i]:
            j += 1
        if lab[i] in (-1, 1) and j - i >= MIN_RUN:
            tr.moves.append(Move(i, j, "up" if lab[i] == -1 else "down", partial_start=(i == 0)))
        if lab[i] == 0 and (j - i) * FRAME >= MIN_STILL:
            tr.stills.append((i, j))
        i = j


# ---------------------------------------------------------------- cut scoring + planning

def cut_kind(a_seg: dict | None, b_seg: dict | None) -> str:
    """match = same exercise, other angle (rule 3); same_angle = same exercise + angle (rule 7);
    new = different exercise / hook (rule 8)."""
    if not a_seg or not b_seg:
        return "new"
    ea, eb = (a_seg.get("exercise") or "").strip().lower(), (b_seg.get("exercise") or "").strip().lower()
    if not ea or ea != eb or "hook" in (a_seg.get("type"), b_seg.get("type")):
        return "new"
    return "same_angle" if a_seg.get("angle", "main") == b_seg.get("angle", "main") else "match"


def score_pair(a: dict, b: dict, kind: str) -> tuple[float, dict]:
    """Penalty for cutting from outgoing frame state a to incoming frame state b (lower = better)."""
    p, why = 0.0, []
    if not a["moving"]:
        p += 100
        why.append("outgoing still")
    if not b["moving"]:
        p += 100
        why.append("incoming still")
    same_dir = bool(a["dir"] and b["dir"] and a["dir"] == b["dir"])
    opposite = bool(a["dir"] and b["dir"] and a["dir"] != b["dir"])
    if kind in ("match", "same_angle"):
        if opposite:
            p += 60
            why.append("direction flips (rule 4)")
        elif not same_dir:
            p += 15
        if not b["first_third"]:
            p += 25
            why.append("incoming not in first third (rule 5)" if kind == "match" else "not on the start of the next rep (rule 7)")
        if kind == "match":
            if a["phase"] is not None and b["phase"] is not None:
                p += 80 * abs(a["phase"] - b["phase"])
            else:
                p += 30
            if not a["first_third"]:
                p += 20
    else:
        if opposite:
            p += 12
        if not b["first_third"]:
            p += 8
    return p, {"same_dir": same_dir, "opposite": opposite, "why": why}


def hard_rules_ok(a: dict, b: dict, kind: str) -> bool:
    """Rules 1-2 (both sides move), 4 (no up -> down inside one exercise), 3 (two angles: matched)."""
    if not (a["moving"] and b["moving"]):
        return False
    if kind in ("match", "same_angle") and a["dir"] and b["dir"] and a["dir"] != b["dir"]:
        return False
    return matched(a, b, kind) if kind == "match" else True


def matched(a: dict, b: dict, kind: str) -> bool:
    if not (a["moving"] and b["moving"]):
        return False
    if kind == "match":
        return (a["dir"] is not None and a["dir"] == b["dir"] and a["phase"] is not None and b["phase"] is not None
                and abs(a["phase"] - b["phase"]) <= 0.2)
    if kind == "same_angle":
        return a["dir"] == b["dir"] and a["dir"] is not None and b["first_third"]
    # different exercises: matched = both sides move the same way (walk-in -> walk-in, grab -> grab)
    return a["dir"] is not None and a["dir"] == b["dir"]


def motion_text(a: dict, b: dict) -> str:
    def one(x):
        s = x["what"]
        if x["first_third"]:
            s += ", first third"
        elif x["phase"] is not None and not x["still"]:
            s += f", {round(x['phase'] * 100)}% into the move"
        return s
    return f"out: {one(a)} / in: {one(b)}"


def stillness_reason(a: dict, b: dict, dead_time: bool = False, locked: str | None = None) -> str:
    if not (a["still"] or b["still"] or not a["moving"] or not b["moving"]):
        return ""
    if dead_time:
        return "dead time removed"
    side = " and ".join(s for s, x in (("outgoing", a), ("incoming", b)) if not x["moving"])
    if locked:
        return f"{side} still: cut locked by storyboard ({locked})"
    return f"{side} still: no motion-safe frame inside the allowed shift"


def beat_snap(t_out: float, period: float | None, phase: float | None) -> tuple[float | None, int | None]:
    """Nearest beat to t_out on the output timeline and the distance in frames."""
    if not period:
        return None, None
    beat = phase + round((t_out - phase) / period) * period
    return beat, round((beat - t_out) * FPS)


def propose(tr: Track, t: float, radius: float = 0.5, n: int = 5) -> list[dict]:
    """Mode (a): motion-safe raw times near t, best first (moving, first third of a move, near t)."""
    out = []
    for k in range(-round(radius * FPS), round(radius * FPS) + 1):
        tt = t + k * FRAME
        if not tr.covers(tt):
            continue
        s = tr.at(tt)
        pen = abs(k) * 1.0 + (0 if s["moving"] else 100) + (0 if s["first_third"] else 15) + (0 if s["dir"] else 10)
        out.append((pen, k, s))
    out.sort(key=lambda x: (x[0], abs(x[1])))
    res, seen = [], set()
    for pen, k, s in out:
        key = s["move_start"] if s["move_start"] is not None else s["t"]
        if key in seen:
            continue
        seen.add(key)
        res.append({**s, "shift_frames": k, "penalty": round(pen, 1)})
        if len(res) >= n:
            break
    return res


class Tracks:
    """Small cache of analysed windows so a cut never decodes the same stretch twice."""

    def __init__(self, src: Path, info: dict | None = None):
        self.src, self.info, self.cache = src, info or probe(src), []

    def get(self, t0: float, t1: float, crop_x=0.5, crop_y=0.5, exercise=None) -> Track:
        for (a, b, cx, cy, ex), tr in self.cache:
            if a <= t0 and t1 <= b and cx == crop_x and cy == crop_y and ex == exercise:
                return tr
        tr = track(self.src, t0, t1, crop_x, crop_y, exercise, self.info)
        self.cache.append(((tr.t0, tr.t0 + (len(tr.times) - 1) * FRAME, crop_x, crop_y, exercise), tr))
        self.cache = self.cache[-12:]
        return tr


ROLL = 0.4         # s: normal search each side of the planned cut
ROLL_WIDE = 1.0    # s: only when nothing moves inside ROLL
SLIP_MATCH = 1.0   # s: how far the incoming angle may slide to line up the same rep point (rule 3)


def cut_limits(a_seg: dict, b_seg: dict, locked: str | None = None, cfg: dict | None = None) -> dict:
    """How far one clip-to-clip cut may move. Hook end stays put (the logo opener + intro are timed on the
    hook), so the cut after the hook only slips the incoming clip. A locked cut is scored but never moved."""
    if locked:
        return {"roll": (0.0, 0.0), "slip": (0.0, 0.0), "wide": None, "locked": locked}
    cfg = cfg or {}
    ROLL, ROLL_WIDE, SLIP_MATCH = (float(cfg.get(k, d)) for k, d in (("roll", globals()["ROLL"]),
                                   ("roll_wide", globals()["ROLL_WIDE"]), ("slip_match", globals()["SLIP_MATCH"])))
    kind = cut_kind(a_seg, b_seg)
    if a_seg.get("type") == "hook":
        return {"roll": (0.0, 0.0), "slip": (-ROLL, ROLL), "wide": ((0.0, 0.0), (-ROLL_WIDE, ROLL_WIDE)), "locked": None}
    slip = (-SLIP_MATCH, SLIP_MATCH) if kind == "match" else (0.0, 0.0)
    return {"roll": (-ROLL, ROLL), "slip": slip, "wide": ((-ROLL_WIDE, ROLL_WIDE), slip), "locked": None}


def clamp(rng: tuple, lo: float, hi: float) -> tuple:
    """Intersect a (min, max) shift range with hard limits (effects, clip ends)."""
    a, b = max(rng[0], lo), min(rng[1], hi)
    return (a, b) if a <= b else (0.0, 0.0)


def plan_cut(tracks: Tracks, a_seg: dict, a_t: float, b_seg: dict, b_t: float, *, roll=(-0.4, 0.4),
             slip=(0.0, 0.0), out_t: float | None = None, beat=(None, None), speed_a=1.0,
             locked: str | None = None, wide: tuple | None = None, allowed=None) -> dict:
    """Pick the motion-safe frame for one cut between two clips.

    a_t = outgoing raw time (its src_out), b_t = incoming raw time (its src_in).
    roll moves both sides together (cut point moves, total length kept); slip moves only the incoming clip
    (its whole range, so the timeline stays). wide = (roll, slip) tried only if the normal range finds no
    motion on one side. Returns the chosen roll / slip, beat snap and the report row.
    """
    res = _plan_cut(tracks, a_seg, a_t, b_seg, b_t, roll=roll, slip=slip, out_t=out_t, beat=beat,
                    speed_a=speed_a, locked=locked, allowed=allowed)
    if res["stillness_flag"] and wide and not locked:
        res2 = _plan_cut(tracks, a_seg, a_t, b_seg, b_t, roll=wide[0], slip=wide[1], out_t=out_t, beat=beat,
                         speed_a=speed_a, locked=None, allowed=allowed)
        if not res2["stillness_flag"] or res2["score"] + 50 < res["score"]:
            res2["widened"] = True
            return res2
    return res


def _plan_cut(tracks, a_seg, a_t, b_seg, b_t, *, roll, slip, out_t, beat, speed_a, locked, allowed=None) -> dict:
    """allowed(roll_frames, slip_frames) -> bool keeps effects inside their clips (cut_video passes it)."""
    allowed = allowed or (lambda r, s: True)
    kind = cut_kind(a_seg, b_seg)
    if locked:
        roll, slip = (0.0, 0.0), (0.0, 0.0)
    margin = 1.6
    ta = tracks.get(a_t + roll[0] - margin, a_t + roll[1] + 0.4, a_seg.get("crop_x", 0.5), a_seg.get("crop_y", 0.5), a_seg.get("exercise"))
    tb = tracks.get(b_t + roll[0] + slip[0] - margin, b_t + roll[1] + slip[1] + margin, b_seg.get("crop_x", 0.5),
                    b_seg.get("crop_y", 0.5), b_seg.get("exercise"))
    best = None
    r_lo, r_hi = round(roll[0] * FPS), round(roll[1] * FPS)
    s_lo, s_hi = round(slip[0] * FPS), round(slip[1] * FPS)
    s_step = 1 if s_hi - s_lo <= 30 else 2
    for r in range(r_lo, r_hi + 1):
        sa = ta.at(a_t + r * FRAME - FRAME)          # last outgoing frame
        for s in range(s_lo, s_hi + 1, s_step):
            if not allowed(r, s) and (r, s) != (0, 0):
                continue
            sb_ = tb.at(b_t + (r + s) * FRAME)       # first incoming frame
            pen, _ = score_pair(sa, sb_, kind)
            pen += abs(r) * 0.6 + abs(s) * 0.15
            if best is None or pen < best[0]:
                best = (pen, r, s, sa, sb_)
    pen, r, s, sa, sb_ = best
    planned = {"a": ta.at(a_t - FRAME), "b": tb.at(b_t)}
    beat_note = "no song"
    snapped = False
    if out_t is not None and beat[0]:
        t_new = out_t + r * FRAME / speed_a
        bt, off = beat_snap(t_new, *beat)
        if off is not None and abs(off) <= BEAT_SNAP_FRAMES and not locked:
            r2 = r + round(off * speed_a)
            if roll[0] * FPS - 1e-6 <= r2 <= roll[1] * FPS + 1e-6 and allowed(r2, s):
                sa2, sb2 = ta.at(a_t + r2 * FRAME - FRAME), tb.at(b_t + (r2 + s) * FRAME)
                if (sa2["moving"] or not sa["moving"]) and (sb2["moving"] or not sb_["moving"]):
                    r, sa, sb_, snapped = r2, sa2, sb2, True
                    beat_note = f"snapped to beat ({off:+d} fr)"
                else:
                    beat_note = f"beat {off:+d} fr away, kept motion (beat frame is still)"
        elif off is not None:
            beat_note = f"off beat by {off:+d} fr (motion first, rule 6)"
    reason = stillness_reason(sa, sb_, locked=locked)
    return {"kind": kind, "score": round(pen, 1), "roll_frames": r, "slip_frames": s, "roll": r * FRAME, "slip": s * FRAME,
            "out": sa, "in": sb_, "planned": planned, "beat": beat_note, "beat_snapped": snapped,
            "motion": motion_text(sa, sb_), "matched": "yes" if matched(sa, sb_, kind) else "no",
            "direction": f"{sa['dir'] or '-'} -> {sb_['dir'] or '-'}", "stillness_flag": reason}


def plan_zoom_edge(tracks: Tracks, seg: dict, t: float, dur: float, lo: float, hi: float, *, radius=0.4,
                   out_t: float | None = None, beat=(None, None), speed=1.0) -> dict:
    """Punch-in: both zoom edges sit on continuous footage; pick the start in the first third of a move,
    the end on motion, keep its length; rule 6 beat snap within 3 frames."""
    tr = tracks.get(t - radius - 1.6, t + dur + radius + 0.4, seg.get("crop_x", 0.5), seg.get("crop_y", 0.5), seg.get("exercise"))
    best = None
    for k in range(-round(radius * FPS), round(radius * FPS) + 1):
        a = t + k * FRAME
        if a < lo or a + dur > hi:
            continue
        s0, s1 = tr.at(a), tr.at(a + dur)
        pen = abs(k) * 0.6 + (0 if s0["moving"] else 100) + (0 if s1["moving"] else 60) + (0 if s0["first_third"] else 20)
        if best is None or pen < best[0]:
            best = (pen, k, s0, s1)
    if best is None:
        s0, s1 = tr.at(t), tr.at(t + dur)
        best = (0, 0, s0, s1)
    _, k, s0, s1 = best
    beat_note, snapped = "no song", False
    if out_t is not None and beat[0]:
        bt, off = beat_snap(out_t + k * FRAME / speed, *beat)
        k2 = k + round(off * speed)
        a2 = t + k2 * FRAME
        if abs(off) <= BEAT_SNAP_FRAMES and lo <= a2 and a2 + dur <= hi:
            n0 = tr.at(a2)
            if n0["moving"] or not s0["moving"]:
                k, s0, s1, snapped = k2, n0, tr.at(a2 + dur), True
                beat_note = f"snapped to beat ({off:+d} fr)"
            else:
                beat_note = f"beat {off:+d} fr away, kept motion"
        else:
            beat_note = f"off beat by {off:+d} fr (motion first, rule 6)"
    return {"at": round(t + k * FRAME, 3), "shift_frames": k, "start": s0, "end": s1, "beat": beat_note,
            "beat_snapped": snapped}


# ---------------------------------------------------------------- report helpers (cut_list.md)

COLUMNS = ["#", "cut time", "type", "from -> to (raw)", "motion", "matched", "direction", "beat", "moved", "stillness_flag"]


def cut_list_md(title: str, rows: list[dict], intro: list[str] | None = None) -> str:
    L = [f"# Cut list: {title}", ""]
    L += intro or []
    L += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['cut_time']:.3f}s | {r['type']} | {r['from_to']} | {r['motion']} | {r['matched']} | "
                 f"{r.get('direction', '')} | {r.get('beat', '')} | {r.get('moved', '')} | {r['stillness_flag'] or '-'} |")
    flagged = [(i, r) for i, r in enumerate(rows, 1) if r["stillness_flag"]]
    L += ["", "## Stillness cuts", ""]
    L += [f"- Cut {i} at {r['cut_time']:.3f}s: {r['stillness_flag']}" for i, r in flagged] or ["- none"]
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- mode (b): score a cut_map

def cuts_from_map(cmap: dict, sb: dict | None) -> list[dict]:
    """Every visible cut in a cut_map: clip changes (raw jumps) and punch-in zoom edges."""
    segs = {s.get("id"): s for s in (sb or {}).get("segments", [])}
    seg_by_out = cmap.get("segments", [])
    pieces = cmap.get("pieces", [])

    def seg_at(out_t):
        for s in seg_by_out:
            if s["out_start"] - 1e-3 <= out_t < s["out_end"] - 1e-3:
                return segs.get(s.get("id"), s)
        return None
    cuts = []
    for p, n in zip(pieces, pieces[1:]):
        jump = abs(n["src_a"] - p["src_b"]) > 0.02
        zoom = abs(n["zoom"] - p["zoom"]) > 1e-3
        if not (jump or zoom):
            continue
        a_seg, b_seg = seg_at(p["out_a"]), seg_at(n["out_a"])
        if jump and a_seg is b_seg:
            typ = "dead time"
        elif jump:
            typ = "clip"
        else:
            typ = "punch in" if n["zoom"] > p["zoom"] else "punch out"
        cuts.append({"type": typ, "out_t": n["out_a"], "a_t": p["src_b"], "b_t": n["src_a"], "a_seg": a_seg or {},
                     "b_seg": b_seg or {}, "speed_a": p["speed"], "speed_b": n["speed"]})
    return cuts


def _locked_in_map(cmap: dict, out_t: float) -> str | None:
    """A style_fx cut-out freezes A's last frame for its mask: that cut is meant to sit on stillness."""
    for f in cmap.get("style_fx") or []:
        if str(f.get("tool", "")).startswith("cutout") and abs(float(f.get("b_start", -99)) - out_t) < 0.05:
            return "style_fx cutout: freezes the outgoing frame for a clean mask"
    return None


def score_map(cmap: dict, sb: dict | None, src: Path) -> list[dict]:
    info = probe(src)
    tracks = Tracks(src, info)
    beat = (None, None)
    if cmap.get("beat"):
        beat = (cmap["beat"]["period"], cmap["beat"]["phase"])
    cuts = cuts_from_map(cmap, sb)
    rows = []
    name = lambda s: s.get("id") or s.get("label") or "?"  # noqa: E731
    for i, c in enumerate(cuts):
        a_seg, b_seg = c["a_seg"], c["b_seg"]
        ft = f"{name(a_seg)} {c['a_t']:.2f} -> {name(b_seg)} {c['b_t']:.2f}"
        bt, off = beat_snap(c["out_t"], *beat)
        beat_now = "-" if off is None else f"{off:+d} fr from beat"
        if c["type"] in ("punch in", "punch out"):
            tr = tracks.get(c["a_t"] - 1.6, c["a_t"] + 0.8, a_seg.get("crop_x", 0.5), a_seg.get("crop_y", 0.5), a_seg.get("exercise"))
            sa, sb_ = tr.at(c["a_t"] - FRAME), tr.at(c["a_t"])
            row = {"cut_time": c["out_t"], "type": c["type"], "from_to": ft, "kind": "zoom", "speed_a": c["speed_a"],
                   "motion": sb_["what"] + (", first third" if sb_["first_third"] else ""),
                   "matched": "yes" if sb_["moving"] else "no",   # same footage on both sides of a zoom cut
                   "direction": f"{sa['dir'] or '-'} -> {sb_['dir'] or '-'}", "beat": beat_now,
                   "stillness_flag": "" if sb_["moving"] else "zoom cut on a still frame",
                   "pass": bool(sb_["moving"])}
            if c["type"] == "punch in":
                out_c = next((x for x in cuts[i + 1:] if x["type"] == "punch out"), None)
                dur = (out_c["a_t"] - c["a_t"]) if out_c else 1.0
                lo = max(p["src_a"] for p in cmap["pieces"] if p["src_a"] <= c["a_t"] and p["out_a"] >= next(
                    sg["out_start"] for sg in cmap["segments"] if sg["out_start"] - 1e-3 <= c["out_t"] < sg["out_end"]) - 1e-3)
                hi = c["a_t"] + dur + 0.4
                z = plan_zoom_edge(tracks, a_seg, c["a_t"], dur, lo, hi, out_t=c["out_t"], beat=beat, speed=c["speed_a"])
                row["zoom_plan"] = z
                if out_c:
                    out_c["zoom_plan"] = z
            else:
                row["zoom_plan"] = c.get("zoom_plan")
            rows.append(row)
            continue
        dead = c["type"] == "dead time"
        locked = _locked_in_map(cmap, c["out_t"])
        lim = cut_limits(a_seg, b_seg, locked)
        res = plan_cut(tracks, a_seg, c["a_t"], b_seg, c["b_t"], roll=lim["roll"], slip=lim["slip"], wide=lim["wide"],
                       out_t=c["out_t"], beat=beat, speed_a=c["speed_a"], locked=locked)
        now_a, now_b = res["planned"]["a"], res["planned"]["b"]
        kind = res["kind"]
        pen_now, _ = score_pair(now_a, now_b, kind)
        rows.append({"cut_time": c["out_t"], "type": c["type"], "from_to": ft, "kind": kind, "speed_a": c["speed_a"],
                     "motion": motion_text(now_a, now_b), "matched": "yes" if matched(now_a, now_b, kind) else "no",
                     "direction": f"{now_a['dir'] or '-'} -> {now_b['dir'] or '-'}", "beat": beat_now,
                     "stillness_flag": stillness_reason(now_a, now_b, dead_time=dead, locked=locked),
                     "pass": hard_rules_ok(now_a, now_b, kind), "penalty_now": round(pen_now, 1),
                     "plan": res})
    return rows


def audit_md(title: str, src: Path, rows: list[dict]) -> str:
    L = [f"# Motion-cut audit: {title}", "",
         f"Source `{rel(src)}`. Each shipped cut scored under Alfonso's cut-on-motion rules (2026-11-23,",
         "Director answer 26) by `scripts/motion_cuts.py score`. Analysis only: nothing was re-rendered.", "",
         "Kinds: `new` = between exercises (rule 8), `same_angle` = same exercise, same camera (rule 7: cut only",
         "on the start of the next rep), `match` = same exercise, other angle (rules 3-4), `zoom` = punch-in edge.", ""]
    passed = sum(1 for r in rows if r["pass"])
    moves = []
    for i, r in enumerate(rows, 1):
        if "plan" in r:
            p = r["plan"]
            if p["roll_frames"] or p["slip_frames"]:
                moves.append(f"cut {i} ({r['cut_time']:.2f}s, {r['type']}): " + (f"roll {p['roll_frames']:+d} fr ({p['roll']:+.2f}s)" if p["roll_frames"] else "")
                             + (f"{', ' if p['roll_frames'] else ''}slip incoming {p['slip_frames']:+d} fr ({p['slip']:+.2f}s)" if p["slip_frames"] else "")
                             + (" -- still flagged: " + p["stillness_flag"] if p["stillness_flag"] else ""))
        elif r.get("zoom_plan") and r["zoom_plan"]["shift_frames"]:
            k = r["zoom_plan"]["shift_frames"]
            moves.append(f"cut {i} ({r['cut_time']:.2f}s, {r['type']}): {k:+d} fr ({k * FRAME:+.2f}s)")
    L += [f"**{passed} of {len(rows)} cuts pass as shipped** (pass = both sides moving, no up -> down flip inside one",
          "exercise, two-angle cuts matched; first third and beat are scored but not a fail).", "",
          f"**{len(moves)} of {len(rows)} would move** under the new rules (each cut on its own, from the shipped times):", ""]
    L += [f"- {m}" for m in moves] + [""]
    L += ["## Shipped cuts, as they are", ""]
    L += ["| # | cut time | type | kind | from -> to (raw) | motion | matched | direction | beat | stillness_flag | pass |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['cut_time']:.3f}s | {r['type']} | {r['kind']} | {r['from_to']} | {r['motion']} | {r['matched']} | "
                 f"{r['direction']} | {r['beat']} | {r['stillness_flag'] or '-'} | {'yes' if r['pass'] else 'NO'} |")
    L += ["", "## What the new rules would do", "",
          "| # | cut time | move | new cut time | new motion | matched | direction | beat | stillness_flag |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        if "plan" in r:
            p = r["plan"]
            fr = p["roll_frames"]
            mv = "stays" if fr == 0 and p["slip_frames"] == 0 else f"roll {fr:+d} fr ({fr * FRAME:+.2f}s)" + (
                f", slip incoming {p['slip_frames']:+d} fr" if p["slip_frames"] else "")
            L.append(f"| {i} | {r['cut_time']:.3f}s | {mv} | {r['cut_time'] + fr * FRAME / r.get('speed_a', 1.0):.3f}s | {p['motion']} | "
                     f"{p['matched']} | {p['direction']} | {p['beat']} | {p['stillness_flag'] or '-'} |")
        else:
            z = r.get("zoom_plan")
            if not z:
                L.append(f"| {i} | {r['cut_time']:.3f}s | stays | {r['cut_time']:.3f}s | {r['motion']} | {r['matched']} | {r['direction']} | - | {r['stillness_flag'] or '-'} |")
                continue
            k = z["shift_frames"]
            st = z["start"] if r["type"] == "punch in" else z["end"]
            mv = "stays" if k == 0 else f"{k:+d} fr ({k * FRAME:+.2f}s), punch-in keeps its length"
            L.append(f"| {i} | {r['cut_time']:.3f}s | {mv} | {r['cut_time'] + k * FRAME / r.get('speed_a', 1.0):.3f}s | {st['what']}"
                     f"{', first third' if st['first_third'] else ''} | {'yes' if st['moving'] else 'no'} | - | {z['beat']} | "
                     f"{'' if st['moving'] else 'zoom cut on a still frame'} |")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("propose", help="mode (a): motion-safe cut points near a raw time")
    a.add_argument("src")
    a.add_argument("t", type=float)
    a.add_argument("--radius", type=float, default=0.5)
    a.add_argument("--crop-x", type=float, default=0.5)
    a.add_argument("--exercise", default=None)
    b = sub.add_parser("score", help="mode (b): score an existing cut list")
    b.add_argument("cut_map", nargs="?", default=str(WORK / "cut_map.json"))
    b.add_argument("--source", default=None)
    b.add_argument("--storyboard", default=str(OUT / "storyboard.json"))
    b.add_argument("--out", default=None, help="write a markdown audit here (default: print only)")
    t = sub.add_parser("track", help="debug: per-frame motion of a raw window")
    t.add_argument("src")
    t.add_argument("t0", type=float)
    t.add_argument("t1", type=float)
    t.add_argument("--crop-x", type=float, default=0.5)
    args = ap.parse_args()

    if args.cmd == "propose":
        src = resolve(args.src)
        radius = args.radius
        tr = track(src, args.t - max(radius, ROLL_WIDE) - 1.6, args.t + max(radius, ROLL_WIDE) + 0.6, args.crop_x,
                   exercise=args.exercise)
        props = [p for p in propose(tr, args.t, radius, 8) if p["moving"]]
        if not props and radius < ROLL_WIDE:
            print(f"nothing moves within {radius}s of {args.t}s; widening to {ROLL_WIDE}s")
            props = [p for p in propose(tr, args.t, ROLL_WIDE, 8) if p["moving"]]
        if not props:
            print(f"no motion-safe frame within {max(radius, ROLL_WIDE)}s: a cut here is on stillness (flag it, say why)")
        for p in props[:5]:
            print(f"{p['t']:.3f}s ({p['shift_frames']:+d} fr)  {p['what']:<28} first_third={p['first_third']}  "
                  f"moving={p['moving']}  energy={p['energy']}")
    elif args.cmd == "track":
        tr = track(resolve(args.src), args.t0, args.t1, args.crop_x)
        for i, tt in enumerate(tr.times):
            s = tr.at(tt)
            print(f"{tt:8.3f}  e={tr.energy[i]:5.2f}  vy={tr.vy[i]:+5.2f}  {s['what']:<22} phase={s['phase']}  "
                  f"{'FIRST3' if s['first_third'] else ''}{' CAM' if s['camera'] else ''}")
        print("moves:", [(round(float(tr.times[m.start]), 2), round(float(tr.times[m.end - 1]), 2), m.dir) for m in tr.moves])
        print("stills:", [(round(float(tr.times[x]), 2), round(float(tr.times[y - 1]), 2)) for x, y in tr.stills])
    else:
        cmap = load_json(resolve(args.cut_map))
        sb = load_json(resolve(args.storyboard), default={}) if args.storyboard else {}
        src_path = args.source or sb.get("source")
        if not src_path:
            die("no source video: pass --source")
        src = resolve(src_path)
        rows = score_map(cmap, sb, src)
        md = audit_md(sb.get("title", rel(src)), src, rows)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(md)
            print(f"wrote {rel(Path(args.out))}: {sum(r['pass'] for r in rows)}/{len(rows)} cuts pass")
        else:
            print(md)


if __name__ == "__main__":
    main()
