#!/usr/bin/env python3
"""Pull single frames out of a video so an agent can look at them. Read-only on the video.

    python3 scripts/grab_frames.py <video> <outdir> <t1> [<t2> ...]

Times are seconds. Frames are written as <outdir>/frame_<seconds>.jpg (max 960px tall).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, rel, resolve, run  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 4:
        die("usage: grab_frames.py <video> <outdir> <t1> [<t2> ...]")
    video, outdir = resolve(sys.argv[1]), resolve(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    for t in sys.argv[3:]:
        out = outdir / f"frame_{float(t):07.2f}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", video, "-frames:v", "1",
             "-vf", "scale=-2:'min(960,ih)'", "-q:v", "3", out])
        print(rel(out))
