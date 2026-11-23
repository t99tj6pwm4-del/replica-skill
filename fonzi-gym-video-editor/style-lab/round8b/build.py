#!/usr/bin/env python3
"""Style Lab round 8b (2026-11-23), after Alfonso rated round 8: A2 (softer glow) KEPT, with his note "The today's
routine need a card that's like gray or back and opacity along with work out set"; B1 / B3 MAYBE with "Slower open
fine if it needs to go past 3 seconds".

    python3 style-lab/round8b/build.py all        # C1 C2 (~1 min each, Remotion only) + B5 B6 (~1 min each)
Outputs: output/style_lab/r8b/<id>/card.mp4 (1080x1920 h264 + aac, his song), card.jpg, meta.json;
style-lab/round8b/cards.json.

Same source and production code as round 8 (style-lab/round8/build.py helpers, Remotion Overlay.tsx, style_fx
video_text). C cards: A2 numbers + config-style text_look.card via FONZI_TEXT_LOOK_JSON (one process each).
B cards: the slower timeline through the same keys production reads (config intro.video_text type_end / hold_end /
dur / max_dur / force_gain), so his pick drops straight into config.yaml.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r8", HERE.parent / "round8" / "build.py")
r8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r8)
ROOT, SRC, W, H, FPS = r8.ROOT, r8.SRC, r8.W, r8.H, r8.FPS
OUTR = ROOT / "output" / "style_lab" / "r8b"
A2 = r8.A_CARDS["r8-A2"]["layers"]
SLOW = {"type_end": 1.6, "hold_end": 2.4, "dur": 3.4, "max_dur": 3.5}

C_CARDS = {
    "r8b-C1": {"desc": "A2 softer glow + a black card at 50 % (rounded, no stroke) behind the Routine Checklist and the "
                       "Exercise Bar; Form Tip, CAM tags and titles stay box-free.",
               "card": {"color": "#000000", "opacity": 0.50, "radius": 44, "behind": ["checklist", "exercise_bar"]}},
    "r8b-C2": {"desc": "A2 softer glow + a gray #333 card at 55 % (rounded, no stroke) behind the Routine Checklist and "
                       "the Exercise Bar; Form Tip, CAM tags and titles stay box-free.",
               "card": {"color": "#333333", "opacity": 0.55, "radius": 44, "behind": ["checklist", "exercise_bar"]}},
}
B_CARDS = {
    "r8b-B5": {"desc": "B1 slowed down: types 0-1.6 s, holds with 2 cursor blinks to 2.4 s, splits 2.4-3.4 s ease-out "
                       "(3.4 s); only the automatic dark-footage boost inside the letters.",
               "variant": dict(SLOW)},
    "r8b-B6": {"desc": "The same slower 3.4 s timing with B3's x1.5 brightening inside the letters only.",
               "variant": {**SLOW, "force_gain": 1.5}},
}
SEG_C = {"s3": [13.70, 16.20], "s4": None}      # s3 = checklist + bar (+ CAM 2); s4 = the round 8 bright frame


def env_for(card: str) -> dict:
    e = dict(os.environ, FONZI_OUTPUT=str(SRC))
    if card in C_CARDS:
        f = OUTR / card / "look.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"layers": A2, "card": C_CARDS[card]["card"]}, indent=1))
        e.update(FONZI_TEXT_LOOK="white", FONZI_TEXT_LOOK_JSON=str(f))
    return e


def c_child(card: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    import text_look as TL
    d = OUTR / card
    tmp = d / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    base = SRC / "multicam_version.mp4"
    props = json.loads((SRC / "work" / "overlay_props.json").read_text())
    props["textLook"] = TL.for_remotion()
    props["noTextWindows"] = []
    pf = tmp / "props.json"
    pf.write_text(json.dumps(props))
    bright = json.loads((r8.OUTR / "_shared" / "a_segments.json").read_text())
    segs = {"s3": SEG_C["s3"], "s4": [bright["s4"][0], bright["s4"][0] + 2.0]}
    exe = sorted(Path("/opt").glob("pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"))
    parts = []
    for name in ("s3", "s4"):
        a, b = segs[name]
        fa, fb = int(round(a * FPS)), int(round(b * FPS)) - 1
        ov = tmp / f"{name}.mov"
        r8.run(["npx", "remotion", "render", "src/index.ts", "Overlay", ov, f"--props={pf}", f"--frames={fa}-{fb}",
                "--codec=prores", "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png",
                *([f"--browser-executable={exe[-1]}"] if exe else []), "--log=error"], cwd=ROOT / "remotion")
        out = tmp / f"{name}.mp4"
        r8.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{fa / FPS:.3f}", "-t", f"{(fb - fa + 1) / FPS:.3f}", "-i", base,
                "-i", ov, "-filter_complex", f"[0:v]fps={FPS}[b];[b][1:v]overlay=format=auto,format=yuv420p[v];"
                "[0:a]anull[a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-c:a", "aac",
                "-b:a", "192k", out])
        parts.append(out)
        ov.unlink()
    # picture + his song of each moment (two moments, so the song jumps once at the moment change)
    r8.run(["ffmpeg", "-v", "error", "-y", "-i", parts[0], "-i", parts[1], "-filter_complex",
            f"[0:v]fps={FPS},format=yuv420p,setsar=1[v0];[1:v]fps={FPS},format=yuv420p,setsar=1[v1];"
            "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", d / "card.mp4"])
    ims = [r8.grab(parts[0], 1.0), r8.grab(parts[1], 0.6)]
    r8.grid(ims, ["checklist + bar + CAM 2 (14.7 s)", f"bright frame ({segs['s4'][0] + 0.6:.1f} s)"], d / "card.jpg", 2)
    meta = {"id": card, "layers": TL.look()["layers"], "card": TL.look().get("card"), "segments": segs,
            "bright_why": bright["s4_why"], "ffprobe": r8.probe_line(d / "card.mp4")}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{card}: {d / 'card.mp4'}  {meta['ffprobe']}")


def b_child(card: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    import style_fx
    d = OUTR / card
    tmp = d / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    base = SRC / "multicam_version.mp4"
    op = r8.b_shared()                                  # the same 3-beat logo opener as round 8 (wet drips)
    v = B_CARDS[card]["variant"]
    rep = style_fx.video_text(base, tmp / "intro.mp4", "GRIND DAY", dur=v["dur"], piece=True,
                              start=r8.OPENER_END / FPS, report=tmp / "intro.json", variant=v)
    no, ni, after = r8.OPENER_END, rep["frames"], 30
    s0 = no + ni
    fc = (f"[0:v]trim=end_frame={no},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[a];"
          f"[1:v]fps={FPS},format=yuv420p,setsar=1[b];"
          f"[2:v]fps={FPS},trim=start_frame={s0}:end_frame={s0 + after},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[c];"
          f"[a][b][c]concat=n=3:v=1:a=0[v];"
          f"[0:a]volume=-6dB[oa];[1:a]adelay={int(no * 1000 / FPS)}|{int(no * 1000 / FPS)}[ia];"
          f"[2:a]atrim=0:{(s0 + after) / FPS:.3f}[sa];[sa][oa][ia]amix=inputs=3:duration=first:normalize=0,"
          f"alimiter=limit=0.89[aa]")
    r8.run(["ffmpeg", "-v", "error", "-y", "-i", op, "-i", tmp / "intro.mp4", "-i", base, "-filter_complex", fc,
            "-map", "[v]", "-map", "[aa]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS,
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", d / "card.mp4"])
    o = no / FPS
    ts = [0.3, 1.0, 2.0, 2.7, 3.1, 3.5]
    r8.grid([r8.grab(d / "card.mp4", o + t) for t in ts], [f"+{t:.1f}s after the opener" for t in ts], d / "card.jpg", 6)
    meta = {"id": card, "variant": v, "intro_report": rep, "opener_frames": no, "ffprobe": r8.probe_line(d / "card.mp4")}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{card}: {d / 'card.mp4'}  {meta['ffprobe']}  intro {rep['dur']}s")


def write_cards():
    cards = []
    for cid, c in {**C_CARDS, **B_CARDS}.items():
        d = OUTR / cid
        if not (d / "card.mp4").exists():
            continue
        sec = "C" if cid in C_CARDS else "B"
        cards.append({"id": cid, "section": sec,
                      "title": ("Checklist + bar card: " if sec == "C" else "Video-inside-text, slower: ") + cid[-2:],
                      "description": c["desc"], "mp4": str((d / "card.mp4").relative_to(ROOT)),
                      "jpg": str((d / "card.jpg").relative_to(ROOT))})
    (HERE / "cards.json").write_text(json.dumps({"round": "8b", "date": "2026-11-23", "after": "round 8 ratings: A2 "
                                                 "keep (+ card note), B1 / B3 maybe (slower open ok past 3 s)",
                                                 "cards": cards}, indent=1))
    print(f"{HERE / 'cards.json'}: {len(cards)} cards")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--child":
        (c_child if args[1] in C_CARDS else b_child)(args[1])
        return
    want = list(C_CARDS) + list(B_CARDS) if not args or args == ["all"] else \
        [a if a.startswith("r8b-") else f"r8b-{a}" for a in args]
    for c in want:                                      # one at a time (memory)
        subprocess.run([sys.executable, __file__, "--child", c], env=env_for(c), check=True)
    write_cards()


if __name__ == "__main__":
    main()
