#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Our sound effects from OpenFilm's free CC0 library (Alfonso, 2026-11-23: "let's start
swapping the sound effects with the ones in the new folder").

    python3 scripts/library_sfx.py prep        # build sfx/library/fonzi/<sound>.wav from the library originals
    python3 scripts/library_sfx.py list        # role -> library id -> file (and what is missing)
    python3 scripts/library_sfx.py audition    # output/sfx_audition.mp4: each role, OLD then NEW, labelled

The picks live in config.yaml sfx.library (id, the original taken with `scripts/openfilm_library.sh take <id>` into
sfx/library/, start / dur / fade_out). `prep` trims each original, makes it 48 kHz stereo and level-matches it to the
old synthesised sound it replaces (same loudest-100 ms RMS, peak capped at -1 dBFS), so the dB levels already tuned
in render_final.py / style_fx.py / finish_fx.py still sit the sounds UNDER his song. Originals are never changed.
Scripts ask common.sfx_file(<role>); a missing prepared file falls back to the old sfx/*.wav.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import LIBRARY_SFX, OUT, ROOT, die, load_config, probe, rel, run, sfx_info  # noqa: E402

SR = 48000
PEAK_DB = -1.0


def pcm(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def loudest_rms(a: np.ndarray, win: float = 0.1) -> float:
    m = (a ** 2).mean(axis=1)
    n = max(1, int(win * SR))
    if len(m) <= n:
        return float(np.sqrt(m.mean()))
    c = np.convolve(m, np.ones(n) / n, "valid")
    return float(np.sqrt(c.max()))


def cfg() -> dict:
    return load_config().get("sfx") or {}


def prep(only: list[str] | None = None):
    LIBRARY_SFX.mkdir(parents=True, exist_ok=True)
    for name, s in (cfg().get("library") or {}).items():
        if only and name not in only:
            continue
        src = ROOT / s["original"]
        if not src.exists():
            die(f"{rel(src)} missing: run scripts/openfilm_library.sh take {s['id']}")
        a = pcm(src)
        a = a[int(s.get("start", 0) * SR):][: int(s.get("dur", len(a) / SR) * SR)].copy()
        fo = int(s.get("fade_out", 0) * SR)
        if fo:
            a[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None] ** 2
        a[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR), dtype=np.float32)[:, None]   # no click at the cut
        gain = 1.0
        if s.get("match") and (ROOT / s["match"]).exists():
            gain = loudest_rms(pcm(ROOT / s["match"])) / max(loudest_rms(a), 1e-9)
        peak = float(np.abs(a).max()) * gain
        cap = 10 ** (PEAK_DB / 20)
        if peak > cap:
            gain *= cap / peak
        a = np.clip(a * gain, -1, 1)
        out = LIBRARY_SFX / f"{name}.wav"
        p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                            "-c:a", "pcm_s16le", str(out)], input=a.astype(np.float32).tobytes())
        if p.returncode:
            die(f"ffmpeg failed writing {out}")
        print(f"wrote  {rel(out)}  ({len(a) / SR:.2f}s, gain {20 * np.log10(gain):+.1f} dB, from {s['id']})")


def listing():
    c = cfg()
    print(f"source: {c.get('source', 'library')}")
    for role in c.get("roles") or {}:
        i = sfx_info(role)
        print(f"{role:14s} {i['source']:8s} {i['library_id'] or '-':60s} {rel(i['file'])}")


def audition(out: Path):
    """Each role once: OLD (the synthesised wav) then NEW (the library sound), on a black card with the role name
    in Montserrat white. Only the roles that have their own library pick (shared ones are heard once)."""
    from PIL import Image, ImageDraw, ImageFont
    font = ROOT / "remotion" / "public" / "fonts" / "Montserrat.ttf"     # variable font (style_fx.SUB_FONT)
    if not font.exists():
        die(f"{rel(font)} missing")

    def mont(size, weight):
        f = ImageFont.truetype(str(font), size)
        f.set_variation_by_name(weight)
        return f
    c = cfg()
    lib = c.get("library") or {}
    items = []
    for role, r in (c.get("roles") or {}).items():
        if r.get("sound") == role and role in lib:       # one line per library pick (shared roles heard once)
            items.append((role, ROOT / r["fallback"], sfx_info(role)))
    tmp = OUT / "work" / "sfx_audition"
    tmp.mkdir(parents=True, exist_ok=True)
    W, H, slot = 1080, 1920, 2.0
    big, mid, small = mont(96, "ExtraBold"), mont(120, "ExtraBold"), mont(44, "Regular")

    def card(path, role, which, detail):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        for y, text, f in ((760, role.replace("_", " ").upper(), big), (900, which, mid), (1060, detail, small)):
            w = d.textlength(text, font=f)
            if w > W - 80:
                f = mont(int(f.size * (W - 80) / w), "ExtraBold" if f is not small else "Regular")
                w = d.textlength(text, font=f)
            d.text(((W - w) / 2, y), text, font=f, fill=(255, 255, 255))
        im.save(path)

    clips = []
    for k, (role, old, new) in enumerate(items):
        for j, (which, f, detail) in enumerate((("OLD", old, f"our own: {old.name}"),
                                                ("NEW", new["file"], f"library: {new['name']}"))):
            png, mp4 = tmp / f"{k:02d}_{j}.png", tmp / f"{k:02d}_{j}.mp4"
            card(png, role, which, detail)
            dur = max(slot, probe(f)["duration"] + 0.6)
            run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", png,
                 "-i", f, "-filter_complex", f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=400|400,"
                 f"apad,atrim=0:{dur:.3f}[a]", "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}", mp4])
            clips.append(mp4)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in clips))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-pix_fmt",
         "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"wrote  {rel(out)} ({len(items)} roles, OLD then NEW, {probe(out)['duration']:.1f}s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("names", nargs="*")
    sub.add_parser("list")
    a_ = sub.add_parser("audition"); a_.add_argument("--out", type=Path, default=OUT / "sfx_audition.mp4")
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(a.names or None)
    elif a.cmd == "list":
        listing()
    else:
        audition(a.out)


if __name__ == "__main__":
    main()
