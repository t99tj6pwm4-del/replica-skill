#!/usr/bin/env python3
"""Make the team's own sound effects from plain synthesis (no stock sounds, no AI): sfx/whoosh.wav, sfx/pop.wav.

    python3 scripts/make_sfx.py            # writes sfx/whoosh.wav and sfx/pop.wav (48 kHz stereo)

Alfonso can drop his own files in sfx/ with the same names (or change config.yaml sfx:) to use them instead.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import re  # noqa: E402
import subprocess  # noqa: E402

from common import run  # noqa: E402

SFX = Path(__file__).resolve().parent.parent / "sfx"

# whoosh: pink noise through a band-pass whose centre sweeps up then down, with a soft swell and tail
WHOOSH = ("anoisesrc=d=0.55:c=pink:r=48000:a=0.9,"
          "bandpass=f=900:width_type=o:w=1.4,"
          "afade=t=in:st=0:d=0.22:curve=qsin,afade=t=out:st=0.24:d=0.31:curve=exp,"
          "aphaser=type=t:speed=1.6:decay=0.4,highpass=f=180,lowpass=f=7000,"
          "volume=1.6,aformat=channel_layouts=stereo")
# pop: a short sine blip that drops in pitch, plus a tiny click of noise, very fast decay
POP = ("aevalsrc='0.9*sin(2*PI*(520+900*exp(-t*40))*t)*exp(-t*28)|0.9*sin(2*PI*(520+900*exp(-t*40))*t)*exp(-t*28)'"
       ":s=48000:d=0.16,afade=t=out:st=0.10:d=0.06,highpass=f=120")


def main():
    SFX.mkdir(exist_ok=True)
    for name, graph in (("whoosh", WHOOSH), ("pop", POP)):
        out = SFX / f"{name}.wav"
        raw = SFX / f"{name}_raw.wav"
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", graph, "-ar", "48000", "-ac", "2", raw])
        # peak-normalise to -1 dBFS so config sfx.volume_db alone sets how loud they sit in the mix
        det = subprocess.run(["ffmpeg", "-i", str(raw), "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        peak = float(re.search(r"max_volume: (-?[\d.]+) dB", det).group(1))
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"volume={-1.0 - peak:.2f}dB", out])
        raw.unlink()
        print(f"wrote  sfx/{name}.wav")


if __name__ == "__main__":
    main()
