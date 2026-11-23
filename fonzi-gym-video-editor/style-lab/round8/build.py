#!/usr/bin/env python3
"""Style Lab round 8 (2026-11-23): the white text look (A1-A4) and the video-inside-text intro (B1-B4).

    python3 style-lab/round8/build.py all          # every card (A: ~3 min each, B: ~1 min each)
    python3 style-lab/round8/build.py A2 B3        # some cards
Outputs: output/style_lab/r8/<id>/card.mp4 (1080x1920 h264+aac), card.jpg, meta.json; style-lab/round8/cards.json.

Source: the Grind Day opener-test copy (output/white_look_test/: hook 0-4.133 s, the same cut + multicam picture,
his song in the audio). Every card is built from the CLEAN multicam picture with production code only
(style_fx.intro / layered_title helpers / Remotion Overlay / style_fx.opener / style_fx.video_text), so what he
picks is what ships. Each A card runs in its own process with FONZI_TEXT_LOOK=white and FONZI_TEXT_LOOK_JSON = the
card's layer numbers (text_look.look() reads them; production never sets that variable).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "output" / "white_look_test"
OUTR = ROOT / "output" / "style_lab" / "r8"
HERE = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
OPENER_END = 53                   # frames: 3-beat logo opener at 101 bpm = 1.767 s (as finish_fx picks)
TITLE_EX = 3                      # SEATED (behind) / CALF RAISE: bright gym ceiling behind, back word behind his head
SHADOW = {"name": "shadow", "color": "#000000", "blur": 40, "opacity": 0.35}

A_CARDS = {
    "r8-A1": {"desc": "His exact spec: tight glow 6 px / 80 %, wide glow 22 px / 45 %, dark shadow 40 px / 35 %.",
              "layers": [SHADOW, {"name": "wide_glow", "color": "#FFFFFF", "blur": 22, "opacity": 0.45},
                         {"name": "tight_glow", "color": "#FFFFFF", "blur": 6, "opacity": 0.80}]},
    "r8-A2": {"desc": "Softer glow: tight 4 px / 60 %, wide 16 px / 30 %, same shadow.",
              "layers": [SHADOW, {"name": "wide_glow", "color": "#FFFFFF", "blur": 16, "opacity": 0.30},
                         {"name": "tight_glow", "color": "#FFFFFF", "blur": 4, "opacity": 0.60}]},
    "r8-A3": {"desc": "Stronger glow: tight 8 px / 90 %, wide 30 px / 60 %, shadow 50 px / 45 %.",
              "layers": [{"name": "shadow", "color": "#000000", "blur": 50, "opacity": 0.45},
                         {"name": "wide_glow", "color": "#FFFFFF", "blur": 30, "opacity": 0.60},
                         {"name": "tight_glow", "color": "#FFFFFF", "blur": 8, "opacity": 0.90}]},
    "r8-A4": {"desc": "His spec WITHOUT the dark shadow (glows only), to show what the shadow does on bright footage.",
              "layers": [{"name": "wide_glow", "color": "#FFFFFF", "blur": 22, "opacity": 0.45},
                         {"name": "tight_glow", "color": "#FFFFFF", "blur": 6, "opacity": 0.80}]},
}
A_NOTE = ("Progress bar: a thin white line in the same glow look (done part 4 px, the rest a 2 px hairline at 35 %). "
          "Glitch intro in this look: white-only, a 2-frame burst of white ghost copies (8 / 4 px) on the letter edges "
          "+ a 2-band slice jitter, no red / cyan.")
B_CARDS = {
    "r8-B1": {"desc": "His exact spec: types on 0-1.2 s, holds with 2 cursor blinks to 1.8 s, splits 1.8-2.6 s ease-out.",
              "variant": {}},
    "r8-B2": {"desc": "Same, with a thinner cursor that blinks faster (4 blinks) and a harder expo-out split.",
              "variant": {"cursor_w": 0.05, "blinks": 4, "ease": "expo"}},
    "r8-B3": {"desc": "Same, with the footage under the letters brightened x1.5 (the only brightening allowed).",
              "variant": {"force_gain": 1.5}},
    "r8-B4": {"desc": "Same, but a thin 8 px line of video opens at the seam for 2 frames before the halves move.",
              "variant": {"seam_frames": 2, "seam_px": 8}},
}


def run(cmd, **kw):
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def env_for(card: str | None = None) -> dict:
    e = dict(os.environ, FONZI_OUTPUT=str(SRC))
    if card in A_CARDS:
        f = OUTR / card / "look.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"layers": A_CARDS[card]["layers"]}, indent=1))
        e.update(FONZI_TEXT_LOOK="white", FONZI_TEXT_LOOK_JSON=str(f))
    return e


def probe_line(p: Path) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                           "format=duration:stream=codec_name,width,height,r_frame_rate", "-of", "compact", str(p)],
                          capture_output=True, text=True).stdout.strip().replace("\n", " | ")


def grab(video: Path, t: float):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-f",
                          "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    from PIL import Image
    return Image.fromarray(np.frombuffer(raw[: W * H * 3], np.uint8).reshape(H, W, 3))


def grid(ims, labels, out: Path, cols: int):
    from PIL import Image, ImageDraw
    tw, th = 360, 640
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 30)), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * tw, (i // cols) * (th + 30)
        d.text((x + 8, y + 8), lab, fill=(235, 235, 235))
        sheet.paste(im.resize((tw, th)), (x, y + 30))
    sheet.save(out, quality=90)


# ------------------------------------------------------------------ A: the white text look
def a_child(card: str):
    """Runs inside the card's own process (env from env_for)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import numpy as np
    from PIL import Image
    import style_fx
    import layered_title as lt
    import text_look as TL
    from common import WORK
    d = OUTR / card
    tmp = d / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    base = SRC / "multicam_version.mp4"
    ic = json.loads((SRC / "work" / "intro_card.json").read_text())
    # 1. intro title (strobe, the Grind Day pick) in this look, after the opener: production style_fx.intro
    style_fx.intro(base, tmp / "s1.mp4", " ".join(ic["title"]), ic["subtitle"], "strobe", ic["beats_s"], None, None,
                   ic["dur"], piece=True, mask_src=base, report=tmp / "intro.json", start=ic["start"])
    # 2. exercise title SEATED / CALF RAISE: production layered_title helpers on its window (the full build()
    #    re-encodes the whole video; this composes the same layers on the window only)
    ex = json.loads((SRC / "work" / f"layered_title_ex{TITLE_EX}.json").read_text())
    k0, nf = int(round(ex["at"] * FPS)), int(round(ex["dur"] * FPS))
    (tmp / "in").mkdir()
    run(["ffmpeg", "-v", "error", "-y", "-i", base, "-vf", f"trim=start_frame={k0}:end_frame={k0 + nf},"
         f"setpts=PTS-STARTPTS,scale={W}:{H}", "-fps_mode", "passthrough", tmp / "in" / "f%04d.png"])
    frs = sorted((tmp / "in").glob("f*.png"))
    session, model = lt.cut_session()
    masks = lt.smooth_masks(lt.raw_masks(session, model, frs))
    big1 = lt.fit_font(lt.SERIF, ex["first"], int(W * lt.WIDTH_FRAC))
    big2 = lt.fit_font(lt.SERIF, ex["last"], int(W * lt.WIDTH_FRAC))
    from PIL import ImageFont
    small = ImageFont.truetype(str(lt.SANS), max(48, int(big2.size * 0.22)))
    small.set_variation_by_name("SemiBold")
    intro_line = ex.get("intro_line", "")
    y1, yi, y2 = ex["first_line_y"], ex["intro_y"], ex["last_line_y"]
    b0, f0, l0 = lt.text_layer(ex["first"], big1, y1), lt.text_layer(ex["last"], big2, y2), \
        (lt.text_layer(intro_line, small, yi) if intro_line else Image.new("RGBA", (W, H), (0, 0, 0, 0)))
    bl, fl, ll = TL.stack(b0), TL.stack(f0), TL.stack(l0)
    (tmp / "s2").mkdir()
    for k, f in enumerate(frs):
        img = Image.open(f).convert("RGBA")
        t = k / max(1, len(frs) - 1)
        behind = lt.depth_move(b0, y1, t, 0.03, -12)
        comp = Image.alpha_composite(img, lt.depth_move(bl, y1, t, 0.03, -12))
        person = img.copy()
        person.putalpha(lt.drop_specks(masks[k], behind))
        comp = Image.alpha_composite(comp, person)
        comp = Image.alpha_composite(comp, lt.depth_move(fl, y2, t, 0.05, 12))
        comp = Image.alpha_composite(comp, lt.depth_move(ll, yi, t, 0.05, 12))
        comp.convert("RGB").save(tmp / "s2" / f.name)
    run(["ffmpeg", "-v", "error", "-y", "-framerate", FPS, "-i", tmp / "s2" / "f%04d.png", "-c:v", "libx264", "-crf",
         "16", "-pix_fmt", "yuv420p", tmp / "s2.mp4"])
    # 3 + 4. pop-ups in Remotion (production Overlay.tsx with this card's textLook)
    props = json.loads((SRC / "work" / "overlay_props.json").read_text())
    props["textLook"] = TL.for_remotion()
    props["noTextWindows"] = []
    pf = tmp / "props.json"
    pf.write_text(json.dumps(props))
    segs = json.loads((OUTR / "_shared" / "a_segments.json").read_text())
    for name in ("s3", "s4"):
        a, b = segs[name]
        fa, fb = int(round(a * FPS)), int(round(b * FPS)) - 1
        ov = tmp / f"{name}.mov"
        exe = sorted(Path("/opt").glob("pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"))
        run(["npx", "remotion", "render", "src/index.ts", "Overlay", ov, f"--props={pf}", f"--frames={fa}-{fb}",
             "--codec=prores", "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png",
             *([f"--browser-executable={exe[-1]}"] if exe else []), "--log=error"], cwd=ROOT / "remotion")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{fa / FPS:.3f}", "-t", f"{(fb - fa + 1) / FPS:.3f}", "-i", base,
             "-i", ov, "-filter_complex", f"[0:v]fps={FPS}[b];[b][1:v]overlay=format=auto,format=yuv420p[v]",
             "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", tmp / f"{name}.mp4"])
    # assemble: picture = intro | title | pop-ups | bright frame; sound = his song from the intro's start, continuous
    parts = [tmp / "s1.mp4", tmp / "s2.mp4", tmp / "s3.mp4", tmp / "s4.mp4"]
    n = len(parts)
    fc = "".join(f"[{i}:v]fps={FPS},format=yuv420p,setsar=1[v{i}];" for i in range(n))
    fc += "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    total = sum(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                      str(p)], capture_output=True, text=True).stdout) for p in parts)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in parts:
        cmd += ["-i", p]
    cmd += ["-ss", f"{ic['start']:.3f}", "-i", base, "-filter_complex", fc + f";[{n}:a]atrim=0:{total:.3f}[a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS,
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", d / "card.mp4"]
    run(cmd)
    b1 = ic["beats_s"][0]
    ims = [grab(tmp / "s1.mp4", b1 + 0.45), grab(tmp / "s2.mp4", ex["dur"] / 2), grab(tmp / "s3.mp4", 0.8),
           grab(tmp / "s4.mp4", 0.5)]
    grid(ims, ["intro title", "exercise title", "bar + checklist + CAM", "bright frame"], d / "card.jpg", 4)
    for i, im in enumerate(ims):
        im.save(tmp / f"still_{i + 1}.png")
    meta = {"id": card, "layers": TL.look()["layers"], "intro_report": json.loads((tmp / "intro.json").read_text()),
            "segments": {"s1": "intro title (strobe)", "s2": f"exercise title {ex['first']} / {ex['last']}",
                         "s3": f"pop-ups {segs['s3']}", "s4": f"bright frame {segs['s4']} ({segs['s4_why']})"},
            "ffprobe": probe_line(d / "card.mp4")}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    for p in ("in", "s2"):
        shutil.rmtree(tmp / p, ignore_errors=True)
    for p in tmp.glob("*.mov"):
        p.unlink()
    print(f"{card}: {d / 'card.mp4'}  {meta['ffprobe']}")


def a_segments():
    """Shared A windows: s3 = a checklist + bar + CAM tag moment; s4 = the brightest pop-up moment behind the text."""
    import numpy as np
    f = OUTR / "_shared" / "a_segments.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    props = json.loads((SRC / "work" / "overlay_props.json").read_text())
    pops = props["popups"]
    base = SRC / "multicam_version.mp4"
    best = None
    cands = [(b["from"] + 0.4, b["to"] - 0.3, (b["y"], b["y"] + 160), f"exercise bar {b['title']}") for b in pops["bars"]]
    tip = pops.get("formTip")
    if tip:
        cands.append((tip["from"] + 0.4, tip["to"] - 0.3, (tip["y"] + 30, tip["y"] + 330), "form tip"))
    for a, b, (y0, y1), what in cands:
        for t in np.arange(a, b - 1.2, 0.5):
            lum = float(np.asarray(grab(base, float(t)).convert("L"))[y0:y1, 100:980].mean()) / 255
            if not best or lum > best[0]:
                best = (lum, float(t), what)
    seg = {"s3": [13.75, 15.25], "s4": [round(best[1], 2), round(best[1] + 1.2, 2)],
           "s4_why": f"{best[2]}: mean luma {best[0]:.2f} behind the text (the brightest pop-up moment)"}
    f.write_text(json.dumps(seg, indent=1))
    return seg


# ------------------------------------------------------------------ B: video-inside-text
def b_shared():
    sys.path.insert(0, str(ROOT / "scripts"))
    import style_fx
    import finish_fx
    from common import load_json
    d = OUTR / "_shared"
    d.mkdir(parents=True, exist_ok=True)
    op = d / "opener.mp4"
    if not op.exists():
        cm, sb = load_json(SRC / "work" / "cut_map.json"), load_json(SRC / "storyboard.json")
        style_fx.opener(op, SRC / "multicam_version.mp4", "wet", (OPENER_END + 0.5) / FPS,
                        [t for t in finish_fx.beat_grid(cm, sb) if 0 <= t < OPENER_END / FPS],
                        report=d / "opener.json")
    return op


def b_child(card: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    import style_fx
    d = OUTR / card
    tmp = d / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    base = SRC / "multicam_version.mp4"
    op = b_shared()
    rep = style_fx.video_text(base, tmp / "intro.mp4", "GRIND DAY", dur=2.6, piece=True, start=OPENER_END / FPS,
                              report=tmp / "intro.json", variant=B_CARDS[card]["variant"])
    ni = rep["frames"]
    after = 30
    s0 = OPENER_END + ni
    # picture: opener | intro | 1 s of the normal video; sound: his song from 0 + the opener / intro sfx under it
    fc = (f"[0:v]trim=end_frame={OPENER_END},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[a];"
          f"[1:v]fps={FPS},format=yuv420p,setsar=1[b];"
          f"[2:v]fps={FPS},trim=start_frame={s0}:end_frame={s0 + after},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[c];"
          f"[a][b][c]concat=n=3:v=1:a=0[v];"
          f"[0:a]volume=-6dB[oa];[1:a]adelay={int(OPENER_END * 1000 / FPS)}|{int(OPENER_END * 1000 / FPS)}[ia];"
          f"[2:a]atrim=0:{(s0 + after) / FPS:.3f}[sa];[sa][oa][ia]amix=inputs=3:duration=first:normalize=0,"
          f"alimiter=limit=0.89[aa]")
    run(["ffmpeg", "-v", "error", "-y", "-i", op, "-i", tmp / "intro.mp4", "-i", base, "-filter_complex", fc,
         "-map", "[v]", "-map", "[aa]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS,
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", d / "card.mp4"])
    o = OPENER_END / FPS
    ts = [0.2, 0.8, 1.5, 2.0, 2.3, 2.7]
    grid([grab(d / "card.mp4", o + t) for t in ts], [f"+{t:.1f}s after the opener" for t in ts], d / "card.jpg", 6)
    meta = {"id": card, "variant": B_CARDS[card]["variant"], "intro_report": rep, "opener_frames": OPENER_END,
            "ffprobe": probe_line(d / "card.mp4")}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{card}: {d / 'card.mp4'}  {meta['ffprobe']}")


def write_cards():
    cards = []
    for cid, c in {**A_CARDS, **B_CARDS}.items():
        d = OUTR / cid
        if not (d / "card.mp4").exists():
            continue
        sec = "A" if cid in A_CARDS else "B"
        cards.append({"id": cid, "section": sec,
                      "title": ("White text look: " if sec == "A" else "Video-inside-text intro: ") + cid[-2:],
                      "description": c["desc"] + (" " + A_NOTE if sec == "A" else " 2.6 s after the logo opener."),
                      "mp4": str((d / "card.mp4").relative_to(ROOT)), "jpg": str((d / "card.jpg").relative_to(ROOT))})
    (HERE / "cards.json").write_text(json.dumps({"round": 8, "date": "2026-11-23", "cards": cards}, indent=1))
    print(f"{HERE / 'cards.json'}: {len(cards)} cards")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--child":
        (a_child if args[1] in A_CARDS else b_child)(args[1])
        return
    want = list(A_CARDS) + list(B_CARDS) if not args or args == ["all"] else [f"r8-{a}" if not a.startswith("r8-") else a
                                                                             for a in args]
    if any(c in A_CARDS for c in want) and not (OUTR / "_shared" / "a_segments.json").exists():
        print(a_segments())
    for c in want:
        run([sys.executable, __file__, "--child", c], env=env_for(c))
    write_cards()


if __name__ == "__main__":
    main()
