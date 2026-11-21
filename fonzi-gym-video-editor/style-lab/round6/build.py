#!/usr/bin/env python3
"""Style Lab round 6 (from his round 5 notes): r5-02 kept (logo behind him), no drips on the title ever,
the logo as big as the frame allows, the title flickers to the beat.

    python3 style-lab/round6/build.py [r6-01 r6-02 r6-03]

Fixed in every option (reuses round 5's helpers):
  - base: first 3.0 s of output/multicam_version.mp4, his song for those 3 s + our sfx/*.wav, no grade, no scrim
  - Fonzi logo, white 85 %, the art fitted to 1000 px wide, centred in the frame, WHOLE logo inside the frame,
    layered BEHIND HIM (rembg cut-out, same masks as r5-02); fades up under beat 1
  - "LOCKED IN" Rubik Dirt gold #D4A017 in front of him, no drips, same place as r5; subtitle as r5 (steady)
Section "Title flickers to the beat" (only the flicker changes; the flicker itself brings the title on, at beat 1):
  r6-01  strobe: off for 2 frames on every beat after it lands, solid in between
  r6-02  colour: white for 2 frames on every beat (beat 1 included), then back to gold
  r6-03  burst + pulse: the locked round-2 flicker (first 8 frames) on beat 1, then on each later beat a pulse
         brighter + bigger (1.0 -> 1.06 -> 1.0 over 6 frames)
Beats from output/work/cut_map.json (period 0.6676 s, phase 0.6672 s).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r5", HERE.parent / "round5" / "build.py")
r5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r5)
W, H, FPS, N = r5.W, r5.H, r5.FPS, r5.N
r5.OUT = r5.ROOT / "output" / "style_lab" / "r6"
r5.TMP = r5.OUT / "tmp"
OUT = r5.OUT

cm = json.loads((r5.ROOT / "output" / "work" / "cut_map.json").read_text())["beat"]
BEAT_T = [cm["phase"] + i * cm["period"] for i in range(10) if cm["phase"] + i * cm["period"] < N / FPS]
BEATS = [int(round(t * FPS)) for t in BEAT_T]          # [20, 40, 60, 80]
B1 = BEATS[0]

LOGO_ART_W = 1000                                       # art width on screen (the png has margins round the art)
BURST = r5.FLICKER[:8]                                  # the locked round-2 flicker-on, first 8 frames
WHITE = (255, 255, 255)


def big_logo():
    """Logo art fitted to 1000 px wide (or the frame height, whichever is the limit), centred, all of it in frame."""
    src = Image.open(r5.LOGO).convert("RGBA")
    ax0, ay0, ax1, ay1 = Image.fromarray((np.asarray(src)[..., 3] > 8).astype(np.uint8) * 255).getbbox()
    art = src.crop((ax0, ay0, ax1, ay1))
    s = min(LOGO_ART_W / art.width, (H - 40) / art.height)
    art = art.resize((int(round(art.width * s)), int(round(art.height * s))), Image.LANCZOS)
    a = art.getchannel("A").point(lambda v: int(v * 0.85))            # white at 85 %, as r5
    art = Image.merge("RGBA", (*[Image.new("L", art.size, 255)] * 3, a))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0 = (W - art.width) // 2, (H - art.height) // 2
    layer.paste(art, (x0, y0), art)
    box = (x0, y0, x0 + art.width, y0 + art.height)
    assert box[0] >= 0 and box[1] >= 0 and box[2] <= W and box[3] <= H, f"logo clipped: {box}"
    return layer, box


def recolor(layer, rgb):
    r = Image.new("RGBA", layer.size, rgb + (0,))
    r.putalpha(layer.getchannel("A"))
    return r


def brighten(layer, amt):
    """Gold pushed toward white by amt (0-1), alpha kept."""
    g = np.array(r5.GOLD, np.float32)
    c = tuple(int(v) for v in g + (255 - g) * amt)
    return recolor(layer, c)


def title_state(kind, k):
    """(visible, colour/brightness, scale) of the title at frame k for each flicker kind."""
    if k < B1:
        return None
    if kind == "strobe":
        off = any(b > B1 and 0 <= k - b < 2 for b in BEATS)
        return None if off else ("gold", 0.0, 1.0)
    if kind == "colour":
        white = any(0 <= k - b < 2 for b in BEATS)
        return ("white", 1.0, 1.0) if white else ("gold", 0.0, 1.0)
    if kind == "pulse":
        i = k - B1
        if i < len(BURST):
            return ("gold", 0.0, 1.0) if BURST[i] else None
        for b in BEATS[1:]:
            d = k - b
            if 0 <= d < 6:
                e = (1, 0.8, 0.55, 0.3, 0.12, 0)[d]        # snaps up on the beat, eases back
                return ("gold", 0.55 * e, 1.0 + 0.06 * e)
        return ("gold", 0.0, 1.0)
    raise ValueError(kind)


def option(cid, srcs, kind):
    title, sub, _, _ = r5.build_layers()
    logo, box = big_logo()
    logo_a = np.asarray(logo)[..., 3]
    art_px = float((logo_a > 20).sum())
    masks, model = r5.person_masks(srcs)
    chk = r5.Checker(cid)
    gcx, gcy = W / 2, (r5.Y1 + r5.Y2) / 2
    vis_pct, edge_px, on_face = {}, 0, 0
    out = []
    for k, p in enumerate(srcs):
        img = Image.open(p).convert("RGBA")
        la = min(1.0, max(0.0, (k - (B1 - 4)) / 4))       # logo fades up under beat 1 (as r5-02)
        comp = img
        if la > 0:
            comp = Image.alpha_composite(comp, r5.with_alpha(logo, la))
            person = img.copy()
            person.putalpha(masks[k])
            comp = Image.alpha_composite(comp, person)
            ma = np.array(masks[k]) > 128
            vis = (logo_a * la > 20) & ~ma
            if k in (24, 40, 59, 75, 89):
                vis_pct[f"f{k}"] = round(100 * float(vis.sum()) / art_px, 1)
            # the logo must never be clipped by the frame edge
            edge_px += int(vis[0].sum() + vis[-1].sum() + vis[:, 0].sum() + vis[:, -1].sum())
            # logo drawn ON his face: visible logo inside the face box where he is (mask > 0.25)
            if k < r5.SHOT_CUT:
                x0, y0, x1, y1 = r5.FACE
                m = np.array(masks[k])[y0:y1, x0:x1] > 64
                on_face += int(((logo_a[y0:y1, x0:x1] * la > 20) & m & ~ma[y0:y1, x0:x1]).sum())
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        st = title_state(kind, k)
        if st:
            colour, amt, s = st
            t = recolor(title, WHITE) if colour == "white" else (brighten(title, amt) if amt else title)
            txt = Image.alpha_composite(txt, r5.scaled(t, s, gcx, gcy))
        sd = k - (B1 + 8)
        if sd >= 0:
            e = r5.ease_out(sd / 6)
            sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sl.paste(sub, (0, int(18 * (1 - e))), sub)
            txt = Image.alpha_composite(txt, r5.with_alpha(sl, e))
        if txt.getbbox():
            comp = Image.alpha_composite(Image.alpha_composite(comp, r5.shadow_of(txt)), txt)
        chk(k, np.array(txt.getchannel("A")))              # text: safe area + face box, every frame
        out.append(comp)
    res = chk.result()
    res.update(logo_box=list(box), logo_size=[box[2] - box[0], box[3] - box[1]], logo_visible_pct=vis_pct,
               logo_edge_px=edge_px, logo_on_face_px=on_face, cut_model=model,
               beats_s=[round(t, 3) for t in BEAT_T], beat_frames=BEATS)
    print(f"[{cid}] logo {res['logo_size']} at {box}; visible around him {vis_pct}; "
          f"edge px {edge_px}; logo px on his face (soft mask edge) {on_face}")
    sounds = [("whoosh", B1 / FPS - 0.30, -14), ("impact", B1 / FPS - 0.02, -5)]
    return out, sounds, res


OPTIONS = {"r6-01": "strobe", "r6-02": "colour", "r6-03": "pulse"}
STILL = 50          # 1.67 s: between beats, title steady, his head in front of the logo


def main():
    r5.TMP.mkdir(parents=True, exist_ok=True)
    srcs = r5.load_frames()
    report_p = OUT / "check_report.json"
    report = json.loads(report_p.read_text()) if report_p.exists() else {}
    for cid in [a for a in sys.argv[1:] if not a.startswith("--")] or OPTIONS:
        frames, sounds, res = option(cid, srcs, OPTIONS[cid])
        assert len(frames) == N
        r5.encode(frames, cid, sounds)
        frames[STILL].convert("RGB").save(OUT / f"{cid}.jpg", quality=90)
        report[cid] = res
    report_p.write_text(json.dumps(report, indent=1))
    if "--keep-tmp" not in sys.argv:
        shutil.rmtree(r5.TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
