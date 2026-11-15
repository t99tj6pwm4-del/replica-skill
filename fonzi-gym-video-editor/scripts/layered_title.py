#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Layered Title (Documentary Gold): ONE giant two-line gold title with the
person sandwiched in the middle: "FONZI" BEHIND him, "STAYS FIT" and the small intro line IN FRONT
(lines set in config/brand.json: layered_title_top / layered_title_bottom).

Only when it seems right (story / intro / documentary video, Alfonso introducing himself or a big idea,
a clean standing shot). Never on fast gym reels, song videos or quick cuts. Used through
`render_final.py --title-style layered-gold` (or storyboard "title_style": "layered-gold").

storyboard.json:
  "title_style": "layered-gold",
  "layered_title": {"at": 3.2, "dur": 3.5, "intro_line": "i'm a content creator"}   # times in the cut
  optional: "first_y" / "intro_y" / "last_y" (pixels from the top of 1920) to place the lines by hand,
  e.g. for a chest-up shot where the automatic layout lands on his face

The window is rebuilt frame by frame (bottom to top): the shot's background, the first name, the
person cut out of the same frame (rembg human segmentation), the last name, the intro line.
Still, no animation: it appears as one finished title, holds, cuts away. Gold, no box / shadow / outline.
Picture only: the audio is copied untouched.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, REMOTION, W, WORK, brand, die, load_json, probe, rel, run, save_json  # noqa: E402

GOLD = (205, 162, 32)                       # within #C9A227-#D4A017
SERIF = REMOTION / "public" / "fonts" / "AbrilFatface-Regular.ttf"
SANS = REMOTION / "public" / "fonts" / "Montserrat.ttf"
WIDTH_FRAC = 0.90


def fit_font(path: Path, text: str, width: int) -> ImageFont.FreeTypeFont:
    """Largest font size whose rendered text is `width` pixels wide."""
    lo, hi = 10, 1200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = ImageFont.truetype(str(path), mid)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= width:
            lo = mid
        else:
            hi = mid - 1
    return ImageFont.truetype(str(path), lo)


def text_layer(text: str, font: ImageFont.FreeTypeFont, cy: int, color=GOLD) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = font.getbbox(text)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y = cy - (bb[3] - bb[1]) // 2 - bb[1]
    d.text((x, y), text, font=font, fill=color + (255,))
    return layer


def person_mask(session, frame: Image.Image) -> Image.Image:
    from rembg import remove
    m = remove(frame, session=session, only_mask=True)        # L image, 255 = person
    # hard matte: rembg leaves half-transparent areas on dark clothes in low light, which shows the back word
    # through his body as a gold ghost. Binarise first, then only a ~1px soft edge.
    m = m.point(lambda v: 255 if v >= 128 else 0)
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))   # no halo, thin soft edge
    return m


def layout(mask: Image.Image) -> tuple[int, int, int]:
    """Where the lines go, from the person's outline: first name over the head/shoulders (so his head
    covers part of it), last name across the chest, the small line between them on the chest."""
    a = np.array(mask) > 128
    rows = np.where(a.any(axis=1))[0]
    if len(rows) < 50:
        die("layered title: no clear person in this shot. Pick a clean standing / waist-up shot.")
    top, bottom = int(rows[0]), int(rows[-1])
    hgt = bottom - top
    y1 = top + int(0.10 * hgt)          # first name: behind the head / shoulders
    y2 = top + int(0.42 * hgt)          # last name: in front, across the chest
    yi = (y1 + y2) // 2 + int(0.04 * hgt)
    return max(y1, int(0.16 * H)), min(y2, int(0.72 * H)), yi


def build(base: Path, out: Path, at: float, dur: float, first: str, last: str, intro: str,
          ys: dict | None = None, tag: str = "") -> dict:
    try:
        from rembg import new_session
    except ImportError:
        die("rembg is not installed. Run: pip install 'rembg[cpu]'")
    for t in (first, last, intro):
        if "#" in t:
            die("layered title: no hashtags")
    total = probe(base)["duration"]
    if at < 0 or at + dur > total - 0.1:
        die(f"layered title window {at}-{at + dur}s is outside the video (0-{total:.2f}s)")
    tmp = WORK / "layered_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "in").mkdir(parents=True)
    (tmp / "out").mkdir()
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", base, "-t", f"{dur:.3f}",
         "-vf", f"scale={W}:{H},fps={FPS}", tmp / "in" / "f%04d.png"])
    frames = sorted((tmp / "in").glob("f*.png"))
    if not frames:
        die("layered title: could not read frames from the video")
    session = new_session("u2net_human_seg")
    first_mask = person_mask(session, Image.open(frames[0]).convert("RGB"))
    y1, y2, yi = layout(first_mask)
    ys = ys or {}   # optional fixed line positions (pixels from the top), e.g. for a chest-up shot
    y1, yi, y2 = int(ys.get("first_y") or y1), int(ys.get("intro_y") or yi), int(ys.get("last_y") or y2)
    big1 = fit_font(SERIF, first.upper(), int(W * WIDTH_FRAC))
    big2 = fit_font(SERIF, last.upper(), int(W * WIDTH_FRAC))
    small = ImageFont.truetype(str(SANS), max(34, int(big2.size * 0.16)))
    try:
        small.set_variation_by_name("SemiBold")
    except Exception:
        pass
    behind = text_layer(first.upper(), big1, y1)
    front = text_layer(last.upper(), big2, y2)
    line = text_layer(intro, small, yi) if intro.strip() else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    covered = []
    for k, f in enumerate(frames):
        img = Image.open(f).convert("RGBA")
        mask = first_mask if k == 0 else person_mask(session, img.convert("RGB"))
        person = img.copy()
        person.putalpha(mask)
        comp = Image.alpha_composite(img, behind)        # 1 background + 2 first name (behind)
        comp = Image.alpha_composite(comp, person)       # 3 the person, cut out of the same frame
        comp = Image.alpha_composite(comp, front)        # 4 last name in front
        comp = Image.alpha_composite(comp, line)         # 5 intro line in front
        comp.convert("RGB").save(tmp / "out" / f.name)
        if k == len(frames) // 2:
            ma, ba = np.array(mask) > 128, np.array(behind)[:, :, 3] > 0
            covered.append(round(float((ma & ba).sum()) / max(1, ba.sum()), 3))
    seg = tmp / "seg.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", tmp / "out" / "f%04d.png",
         "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", seg])
    seg_len = probe(seg)["duration"]
    # splice the rebuilt window back in, picture only; audio copied from the base untouched
    parts = []
    for name, a, b in (("pre", 0.0, at), ("post", at + seg_len, total)):
        if b - a > 0.5 / FPS:
            p = tmp / f"{name}.mp4"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", base, "-t", f"{b - a:.4f}", "-an",
                 "-vf", f"setpts=PTS-STARTPTS,fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                 "-crf", "15", p])
            parts.append((name, p))
    order = [p for n, p in parts if n == "pre"] + [seg] + [p for n, p in parts if n == "post"]
    (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in order))
    pic = tmp / "pic.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", pic])
    run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", base, "-map", "0:v", "-map", "1:a", "-c", "copy",
         "-t", f"{total:.3f}", out])
    frame_png = WORK / f"layered_title{tag}_frame.png"
    shutil.copy(tmp / "out" / frames[len(frames) // 2].name, frame_png)
    shutil.rmtree(tmp, ignore_errors=True)
    if abs(probe(out)["duration"] - total) > 0.1:
        die("layered title changed the video length: not passing it on")
    info = {"style": "Layered Title (Documentary Gold)", "at": round(at, 3), "dur": round(seg_len, 3),
            "first": first.upper(), "last": last.upper(), "intro_line": intro, "gold": "#CDA220",
            "first_line_y": y1, "last_line_y": y2, "intro_y": yi,
            "first_name_covered_by_person": covered[0] if covered else None,
            "frame": rel(frame_png)}
    save_json(WORK / f"layered_title{tag}.json", info)
    return info


def exercise_plans() -> list[dict]:
    """Per-exercise layered titles (Alfonso, 2026-11-15): each exercise name in the same gold layered style,
    first word BEHIND him, the rest IN FRONT. storyboard.json:
      "exercise_titles": [{"at": 2.2, "dur": 1.8, "first": "DUMBBELL", "last": "CURL", "intro_line": "",
                           "first_y": 307, "intro_y": 1010, "last_y": 1130}, ...]   # *_y optional"""
    sb = load_json(OUT / "storyboard.json", default={})
    out = []
    for it in sb.get("exercise_titles") or []:
        out.append({"at": float(it["at"]), "dur": float(it.get("dur", 1.8)), "first": it["first"],
                    "last": it.get("last", ""), "intro": it.get("intro_line", ""),
                    "ys": {k: it[k] for k in ("first_y", "intro_y", "last_y") if it.get(k)}})
    return sorted(out, key=lambda x: x["at"])


def build_exercise_titles(base: Path, out: Path) -> list[dict]:
    """Bake every per-exercise layered title into the picture, one after the other. Audio untouched."""
    plans = exercise_plans()
    if not plans:
        return []
    for a, b in zip(plans, plans[1:]):
        if a["at"] + a["dur"] > b["at"]:
            die(f"exercise titles overlap: {a['first']} {a['last']} and {b['first']} {b['last']}")
    infos, cur = [], base
    for n, p in enumerate(plans, 1):
        nxt = WORK / f"exercise_title_{n}.mp4"
        info = build(cur, nxt, p["at"], p["dur"], p["first"], p["last"], p["intro"], p["ys"], tag=f"_ex{n}")
        infos.append(info)
        if cur != base:
            cur.unlink(missing_ok=True)
        cur = nxt
    shutil.move(str(cur), str(out))
    save_json(WORK / "exercise_titles.json", infos)
    return infos


def plan_from_storyboard() -> dict | None:
    sb = load_json(OUT / "storyboard.json", default={})
    lt = sb.get("layered_title")
    if not lt:
        return None
    b = brand()
    return {"at": float(lt["at"]), "dur": float(lt.get("dur", 3.5)),
            "first": lt.get("first") or b.get("layered_title_top", "FONZI"),
            "last": lt.get("last") or b.get("layered_title_bottom", "STAYS FIT"),
            "intro": lt.get("intro_line", ""),
            "ys": {k: lt[k] for k in ("first_y", "intro_y", "last_y") if lt.get(k)}}


if __name__ == "__main__":
    p = plan_from_storyboard()
    if not p:
        die('storyboard.json needs "layered_title": {"at": <cut time>, "dur": 3.5, "intro_line": "..."}')
    print(json.dumps(p))
