#!/usr/bin/env python3
"""STORYBOARD AGENT tool. Looks at the raw video and writes the facts the plan is built on.

    python3 scripts/analyze_video.py input/<video>

Writes:
  output/work/analysis.json      ffprobe facts, black + silent + still ranges, motion curve,
                                 transcript of what is said, songs in songs/ with BPM
  output/work/frames/sheet_*.jpg time-stamped contact sheets of sampled frames
Changes nothing in input/.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import SONGS, WORK, die, probe, rel, resolve, run, save_json, sha256  # noqa: E402


def detect(path: Path, vf: str | None, af: str | None, pattern: str) -> list[tuple[float, float]]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path]
    cmd += ["-vf", vf, "-an"] if vf else ["-af", af, "-vn"]
    cmd += ["-f", "null", "-"]
    err = run(cmd, check=False).stderr
    return [(float(a), float(b)) for a, b in re.findall(pattern, err)]


def motion_curve(path: Path, step: float = 0.25) -> list[float]:
    """Mean frame-to-frame change on a tiny grey copy. High = movement, ~0 = nothing happening."""
    w, h = 64, 36
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={1/step},scale={w}:{h},format=gray",
         "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(a) // (w * h)
    if n < 2:
        return []
    a = a[: n * w * h].reshape(n, h, w).astype(np.float32)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    return [round(float(x), 2) for x in np.concatenate([[d[0]], d])]


def ranges_where(values: list[float], step: float, pred, min_len: float) -> list[list[float]]:
    out, start = [], None
    for i, v in enumerate(values + [None]):
        ok = v is not None and pred(v)
        if ok and start is None:
            start = i
        if not ok and start is not None:
            if (i - start) * step >= min_len:
                out.append([round(start * step, 2), round(i * step, 2)])
            start = None
    return out


def intersect(a: list, b: list, min_len: float) -> list[list[float]]:
    out = []
    for a0, a1 in a:
        for b0, b1 in b:
            lo, hi = max(a0, b0), min(a1, b1)
            if hi - lo >= min_len:
                out.append([round(lo, 2), round(hi, 2)])
    return out


def song_tempo(path: Path) -> dict:
    """Rough BPM + first-beat offset from an energy-onset autocorrelation."""
    sr, hop = 11025, 256
    p = subprocess.run(["ffmpeg", "-v", "error", "-t", "90", "-i", str(path), "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(p.stdout, dtype=np.float32)
    if len(x) < sr * 5:
        return {"bpm": None, "beat_offset": 0.0}
    frames = len(x) // hop
    e = np.sqrt((x[: frames * hop].reshape(frames, hop) ** 2).mean(axis=1))
    onset = np.maximum(np.diff(np.log1p(e * 100)), 0)
    onset -= onset.mean()
    fr = sr / hop
    best, best_lag = -1.0, None
    for bpm in np.arange(70, 180.5, 0.5):
        lag = 60.0 / bpm * fr
        idx = (np.arange(1, 9) * lag).astype(int)
        score = sum(float(np.dot(onset[:-i], onset[i:])) / (len(onset) - i) for i in idx if i < len(onset))
        if score > best:
            best, best_lag = score, lag
    # refine: slide a beat comb over the whole clip so the grid does not drift by the end of the video
    coarse, best, bpm, offset = 60.0 * fr / best_lag, -1e9, None, 0.0
    for cand in np.arange(coarse - 1.5, coarse + 1.5, 0.02):
        lag = 60.0 / cand * fr
        for ph in np.arange(0, lag, 2.0):
            idx = (ph + np.arange(0, len(onset) - lag - 1, lag)).astype(int)
            score = float(onset[idx].sum() + onset[idx + 1].sum())
            if score > best:
                best, bpm, offset = score, cand, ph / fr
    return {"bpm": round(float(bpm), 2), "beat_offset": round(float(offset), 3)}


def contact_sheets(path: Path, duration: float, outdir: Path) -> tuple[list[str], float]:
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("sheet_*.jpg"):
        old.unlink()
    every = max(1.0, round(duration / 48, 1))  # at most ~48 frames, 12 per sheet
    vf = (f"fps=1/{every},scale=-2:480,"
          "drawtext=text='%{pts\\:hms}':fontcolor=yellow:fontsize=34:x=8:y=8:box=1:boxcolor=black@0.7,"
          "tile=4x3:padding=4")
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", vf, "-q:v", "4", outdir / "sheet_%02d.jpg"])
    return sorted(rel(p) for p in outdir.glob("sheet_*.jpg")), every


def main():
    if len(sys.argv) != 2:
        die("usage: analyze_video.py input/<video>")
    src = resolve(sys.argv[1])
    if not src.exists():
        die(f"video not found: {sys.argv[1]}")
    info = probe(src)
    if not info["video"]:
        die("no video stream in this file")
    dur = info["duration"]

    black = detect(src, "blackdetect=d=0.3:pix_th=0.10", None,
                   r"black_start:([\d.]+) black_end:([\d.]+)")
    silence = []
    if info["audio"]:
        silence = detect(src, None, "silencedetect=noise=-35dB:d=0.5",
                         r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)")
    step = 0.25
    motion = motion_curve(src, step)
    active = [m for m in motion if m > 0.3] or [1.0]
    still_thr = max(0.35, 0.15 * float(np.median(active)))
    still = ranges_where(motion, step, lambda v: v < still_thr, 0.5)
    silent = [[round(a, 2), round(b, 2)] for a, b in silence] if info["audio"] else [[0.0, round(dur, 2)]]
    dead = intersect(silent, still, 0.5)

    # usable range = everything except black/dead head and tail
    start, end = 0.0, dur
    for a, b in sorted(black):
        if a <= start + 0.1:
            start = max(start, b)
    for a, b in sorted(black, reverse=True):
        if b >= end - 0.1:
            end = min(end, a)

    transcript = {"segments": [], "words": [], "text": ""}
    if info["audio"]:
        from transcribe import transcribe
        wav = WORK / "raw_audio.wav"
        WORK.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
        transcript = transcribe(wav)

    sheets, every = contact_sheets(src, dur, WORK / "frames")
    songs = []
    for s in sorted(SONGS.glob("*.mp3")):
        songs.append({"file": rel(s), "duration": round(probe(s)["duration"], 1), **song_tempo(s)})

    analysis = {
        "source": rel(src),
        "source_sha256": sha256(src),
        "probe": info,
        "is_vertical": info["video"]["height"] > info["video"]["width"],
        "usable_range": [round(start, 2), round(end, 2)],
        "black_ranges": [[round(a, 2), round(b, 2)] for a, b in black],
        "silent_ranges": silent if info["audio"] else [],
        "still_ranges": still,
        "dead_ranges": dead,
        "motion": {"step_seconds": step, "values": motion},
        "transcript": {"text": transcript["text"], "segments": transcript["segments"]},
        "raw_words": transcript["words"],
        "frame_sheets": sheets,
        "frame_sheet_interval_seconds": every,
        "songs": songs,
    }
    save_json(WORK / "analysis.json", analysis)

    v = info["video"]
    print(f"source      {rel(src)}")
    print(f"video       {v['width']}x{v['height']} {v['fps']}fps {v['codec']}  {dur:.1f}s  "
          f"audio={'yes' if info['audio'] else 'NO'}")
    print(f"usable      {start:.2f}s -> {end:.2f}s")
    print(f"black       {analysis['black_ranges']}")
    print(f"dead (silent + nothing moving, >0.5s)  {dead}")
    print(f"speech      {len(transcript['words'])} words")
    for s in transcript["segments"]:
        print(f"   {s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
    print(f"songs       {[(s['file'], s['bpm']) for s in songs] or 'none in songs/'}")
    print(f"frames      {len(sheets)} contact sheets (one frame every {every}s): {sheets}")
    print("wrote       output/work/analysis.json")


if __name__ == "__main__":
    main()
