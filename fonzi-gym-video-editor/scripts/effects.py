#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Applies the CapCut-library effects plan to the picture with ffmpeg.

    python3 scripts/effects.py suggest   # writes a starting output/work/effects_plan.json from the cut map
    python3 scripts/effects.py check     # validates the plan against docs/capcut_effects_library.md rules
    (render_final.py runs the plan automatically before it lays the Remotion graphics on top)

The editor is ffmpeg + Remotion, not the CapCut app: every effect is named from the library and rendered
as the closest ffmpeg equivalent in the SAME category. Names are never invented; a library name this
editor cannot render maps to the closest renderable one in its category, and the log says so.

effects_plan.json:
{
  "filter": "Cinematic",                                   # ONE filter, whole video
  "video_effects": [{"name": "Camera Shake", "at": 31.0, "dur": 0.3, "why": "hardest rep"}],
  "transitions":   [{"name": "Pull In", "at": 22.1, "dur": 0.3, "why": "new exercise"}],   # at = the join
  "velocity_effects": [{"name": "Flash", "at": 31.0, "dur": 0.2}],
  "body_effects": [],                                      # not renderable here: keep empty
  "title_animation": "Flash In",                           # Animation > In on the hook title (Remotion)
  "pro_approved": false
}
The original audio is never touched: effects change the picture only, frame-exact.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, ROOT, W, WORK, die, load_json, probe, rel, run, save_json  # noqa: E402

LIBRARY = ROOT / "docs" / "capcut_effects_library.md"
LOG = OUT / "effects_log.md"
PLAN = WORK / "effects_plan.json"

# ---- filters (Part C / F8): one per video -----------------------------------------------------------
FILTERS = {
    "Cinematic": "eq=contrast=1.08:saturation=0.92:gamma=0.97,colorbalance=rs=0.04:bs=-0.03:rh=-0.03:bh=0.04",
    "Teal and Orange": "colorbalance=rs=0.08:gs=0.0:bs=-0.08:rh=-0.06:gh=0.0:bh=0.08,eq=contrast=1.1:saturation=1.05",
    "Teal Orange": "colorbalance=rs=0.08:bs=-0.08:rh=-0.06:bh=0.08,eq=contrast=1.1:saturation=1.05",
    "Warm": "colorbalance=rs=0.06:gs=0.02:bs=-0.06:rm=0.04:bm=-0.03,eq=saturation=1.05",
    "Golden": "colorbalance=rs=0.08:gs=0.04:bs=-0.08,eq=saturation=1.08:brightness=0.02",
    "Inception": "colorbalance=rs=0.07:gs=0.03:bs=-0.07,eq=contrast=1.05",
    "Cool": "colorbalance=rs=-0.05:bs=0.06,eq=saturation=0.95",
    "Moody": "eq=contrast=1.12:saturation=0.8:brightness=-0.03:gamma=0.95",
    "Dark": "eq=contrast=1.15:saturation=0.85:brightness=-0.05",
    "B&W": "hue=s=0,eq=contrast=1.1",
    "Mono": "hue=s=0,eq=contrast=1.1",
    "Vintage": "curves=preset=vintage",
    "Retro": "curves=preset=vintage,noise=alls=6:allf=t",
    "Film": "eq=contrast=1.05:saturation=0.9,noise=alls=5:allf=t",
    "Vivid": "eq=saturation=1.25:contrast=1.05",
    "Fresh": "eq=saturation=1.1:brightness=0.03,colorbalance=gs=0.02",
    "Red Tea": "colorbalance=rs=0.05:gs=-0.01:bs=-0.03,eq=saturation=1.05:contrast=1.04",
    "Orange Blue": "colorbalance=rs=0.07:bs=-0.06:rh=-0.04:bh=0.07,eq=saturation=1.1",
    "Night Scene": "eq=brightness=-0.04:contrast=1.1:saturation=0.85,colorbalance=bs=0.05",
    "Vlog": "eq=saturation=1.03:contrast=1.02",
    "Life": "eq=saturation=1.03:contrast=1.02",
}
NO_FILTER = {"Food", "Style"}   # Part C: do NOT use for gym

# ---- effects: library name -> (kind, renderable). kind decides the ffmpeg recipe ----------------------
EFFECTS = {
    # shake (A1 / F3 / F6)
    "Shake": "shake", "Camera Shake": "shake", "Repeat Shake": "shake", "Shake Impact": "shake",
    "Zoom Shake": "zoomshake", "Blur Shake": "blurshake", "Screen Shake": "shake", "Flash Shake": "flashshake",
    # flash / light (A1 / D6 / F3 / F5)
    "White Flash": "whiteflash", "Flash": "whiteflash", "Black Flash": "darkflash", "Dark Flash": "darkflash",
    "Glare II": "glare", "Heartwarming Flash": "warmflash", "Light Leak Flash": "warmflash", "Leak 1": "warmflash",
    "BW Flash Snap": "bwflash",
    # glitch (A8 / D7 / F3)
    "RGB Split": "rgbsplit", "Digital Glitch": "rgbsplit", "Signal Glitch 2": "rgbsplit", "Signal Glitch": "rgbsplit",
    "Glitch": "rgbsplit", "Chromatic": "rgbsplit", "Snap Hack": "rgbsplit",
    # blur (A10 / D4 / F3)
    "Blur": "blur", "Simple Blur": "blur", "Motion blur": "blur", "Vertical Blur": "blur", "Blur Dissolve": "blur",
    "Radial Blur": "blur", "Blur Focus": "blur",
    # camera / zoom transitions (D2 / F3 / F7)
    "Pull In": "pullin", "Zoom In": "pullin", "Delay Zoom": "pullin", "Dive & Bounce": "divebounce",
    "Rebound Zoom": "divebounce", "Shaky Inhale": "shakyinhale", "Velocity Zoom": "pullin", "Zoom Out": "pullout",
    "Pull Out": "pullout",
    # basic (D1 / F3)
    "Hard Cut": "none", "Match Cut": "none", "Fade": "dip", "Dissolve": "dip", "Cross Fade": "dip",
    "Overlap Fade": "dip", "Fade to Black": "blackfade", "Black Fade": "blackfade", "Film Fade": "blackfade",
    # velocity effects (F5)
    "Fade blur": "blur", "Retro zoom": "pullin",
}
NEVER = {"Comic Cut", "Cartoon", "Sketch", "Comic book", "Laser Eyes", "Funny Faces", "Rainbow", "Anime Punch",
         "Blood Drops", "Horror Q Exit", "Hair Salon", "Slim", "Smooth Skin", "Big Eyes", "Face Reshape",
         "Portrait", "Selfie", "Mask", "Role"}
PRO = {"Neon Silhouette"}
TITLE_ANIMATIONS = {"Flash In", "Fade In", "Zoom 1", "Focus"}   # renderable Animation > In for the hook
TRANSITION_DUR = {"blackfade": (0.5, 1.0), "none": (0.0, 0.0)}


def library_names() -> str:
    if not LIBRARY.exists():
        die("docs/capcut_effects_library.md is missing")
    return LIBRARY.read_text()


def in_library(name: str, lib: str) -> bool:
    return re.search(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])", lib) is not None


def recipe(kind: str, d: float) -> str:
    """ffmpeg filter chain for one effect window of length d (t starts at 0 inside the window)."""
    if kind == "shake":
        return (f"crop=w=iw/1.06:h=ih/1.06:x='(iw-ow)/2+22*sin(t*75)*(1-t/{d})':"
                f"y='(ih-oh)/2+16*cos(t*61)*(1-t/{d})',scale={W}:{H}")
    if kind == "zoomshake":
        return recipe("pullin", d) + "," + recipe("shake", d)
    if kind == "blurshake":
        return recipe("shake", d) + ",gblur=sigma=6:steps=1"
    if kind == "flashshake":
        return recipe("shake", d) + "," + recipe("whiteflash", d)
    if kind == "whiteflash":
        return f"eq=brightness='0.7*max(0,1-t/{d})':eval=frame"
    if kind == "warmflash":
        return f"eq=brightness='0.45*max(0,1-t/{d})':eval=frame,colorbalance=rs=0.15:gs=0.06:bs=-0.12"
    if kind == "glare":
        return f"eq=brightness='0.35*sin(PI*min(1,t/{d}))':eval=frame,gblur=sigma=3:steps=1"
    if kind == "darkflash":
        return f"eq=brightness='-0.85*max(0,1-t/{d})':eval=frame"
    if kind == "bwflash":
        return "hue=s=0,eq=contrast=1.6:brightness=0.06"
    if kind == "rgbsplit":
        return "rgbashift=rh=-14:bh=14:rv=4:bv=-4,noise=alls=10:allf=t"
    if kind == "blur":
        return "gblur=sigma=8:steps=2"
    if kind in ("pullin", "pullout", "divebounce", "shakyinhale"):
        # zoom curve z(t) over the window: pull in = up then settle; dive & bounce = overshoot and bounce
        z = {"pullin": f"1+0.16*sin(PI*min(1,t/{d}))",
             "pullout": f"1.16-0.16*sin(PI/2*min(1,t/{d}))",
             "divebounce": f"1+0.18*sin(PI*min(1,t/{d}))*exp(-1.5*t/{d})+0.04*sin(3*PI*min(1,t/{d}))",
             "shakyinhale": f"1+0.12*sin(PI*min(1,t/{d}))"}[kind]
        chain = (f"scale=w='trunc({W}*({z})/2)*2':h='trunc({H}*({z})/2)*2':eval=frame,"
                 f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2")
        if kind == "divebounce":
            chain = (f"scale=w='trunc({W}*({z})/2)*2':h='trunc({H}*({z})/2)*2':eval=frame,"
                     f"crop={W}:{H}:(iw-{W})/2:'(ih-{H})/2+40*sin(PI*min(1,t/{d}))'")
        if kind == "shakyinhale":
            chain += "," + recipe("shake", d)
        return chain
    if kind == "dip":
        return f"eq=brightness='-0.6*sin(PI*min(1,t/{d}))':eval=frame"
    if kind == "blackfade":
        return f"eq=brightness='-1*sin(PI*min(1,t/{d}))':eval=frame"
    return "null"


def validate(plan: dict, cm: dict, video: str, strict: bool = True) -> tuple[list, list, list]:
    """Returns (errors, notes, timeline entries)."""
    lib = library_names()
    errors, notes, items = [], [], []
    filt = plan.get("filter")
    if isinstance(filt, list):
        errors.append("ONE filter per video (Part C)")
    elif filt:
        if filt in NO_FILTER:
            errors.append(f"filter {filt!r}: Food / Style filters are not for gym")
        elif not in_library(filt, lib):
            errors.append(f"filter {filt!r} is not in the library: never invent a name")
        elif filt not in FILTERS:
            notes.append(f"filter {filt!r} has no ffmpeg recipe here: closest in category is 'Cinematic'")
    if plan.get("body_effects"):
        errors.append("body effects (Part B) need person tracking this editor does not have: leave body_effects empty")
    body_end = cm["end_card"]["out_start"]
    shakes = 0
    for group, cat in (("video_effects", "video effect"), ("transitions", "transition"),
                       ("velocity_effects", "velocity effect")):
        for e in plan.get(group, []):
            name, at, d = e.get("name", ""), float(e.get("at", -1)), float(e.get("dur", 0))
            if name in NEVER or any(n.lower() in name.lower() for n in ("cartoon", "comic", "anime", "horror", "blood")):
                errors.append(f"{name!r}: never for gym (cartoon / joke / reshape / horror)")
                continue
            if name in PRO and not plan.get("pro_approved"):
                errors.append(f"{name!r} is Pro: needs Alfonso's yes (pro_approved) or the closest free one")
                continue
            if not in_library(name, lib):
                errors.append(f"{name!r} is not in docs/capcut_effects_library.md: never invent an effect name")
                continue
            kind = EFFECTS.get(name)
            if kind is None:
                errors.append(f"{name!r} is in the library but this editor cannot render it: pick the closest "
                              f"renderable one in its category ({', '.join(sorted(EFFECTS)[:0]) or 'see effects.py'})")
                continue
            if group == "transitions":
                lo, hi = TRANSITION_DUR.get(kind, (0.2, 0.5))
                if kind != "none" and not lo - 1e-6 <= d <= hi + 1e-6:
                    errors.append(f"transition {name!r} is {d}s: must be {lo}-{hi}s")
                start = at - d / 2                       # centred on the join
            else:
                if kind in ("shake", "zoomshake", "blurshake", "flashshake", "shakyinhale"):
                    shakes += 1
                    if d > 0.35:
                        errors.append(f"{name!r} is {d}s: shake is 0.3s max")
                if kind in ("rgbsplit",) and d > 0.4:
                    errors.append(f"{name!r} is {d}s: glitch is under 0.4s")
                start = at
            if start < 0 or start + d > body_end + 1e-6:
                errors.append(f"{name!r} at {at}s falls outside the video body (0-{body_end:.2f}s)")
                continue
            if kind != "none":
                items.append({"group": group, "name": name, "kind": kind, "from": round(start, 3),
                              "to": round(start + d, 3), "dur": d, "why": e.get("why", "")})
    if shakes > 3:
        errors.append(f"{shakes} shake moments: max 2-3 per video")
    trans = [i for i in items if i["group"] == "transitions"]
    cuts = len(cm.get("pieces", [])) - 1 + len(load_json(WORK / "multicam_map.json", default={}).get("inserts", [])) * 2
    if trans and len(trans) > max(1, cuts // 3):
        errors.append(f"{len(trans)} transitions for ~{cuts} cuts: max 1 transition per 3 cuts")
    srt = sorted(trans, key=lambda i: i["from"])
    for a, b in zip(srt, srt[1:]):
        if b["from"] - a["to"] < 1.0 and a["name"] != b["name"]:
            errors.append(f"{a['name']} and {b['name']} back-to-back: never two different fancy transitions in a row")
    per_clip = {}
    for i in items:
        if i["group"] == "video_effects":
            seg = next((s["id"] for s in cm["segments"] if s["out_start"] <= i["from"] < s["out_end"]), None)
            per_clip[seg] = per_clip.get(seg, 0) + 1
    for seg, n in per_clip.items():
        if n > 1:
            errors.append(f"{n} video effects in segment {seg}: 1 video effect max per clip")
    ta = plan.get("title_animation")
    if ta and ta not in TITLE_ANIMATIONS:
        errors.append(f"title_animation {ta!r}: use one of {sorted(TITLE_ANIMATIONS)} (Animation > In, hook only)")
    # never the same effect + transition combo as the previous video
    combo = combo_key(plan)
    prev = previous_combo(video)
    if strict and combo and prev == combo and not plan.get("allow_repeat"):
        errors.append(f"same effect + transition combo as the previous video ({combo}): change one, "
                      "or set allow_repeat if Alfonso asked")
    overlaps = sorted(items, key=lambda i: i["from"])
    for a, b in zip(overlaps, overlaps[1:]):
        if b["from"] < a["to"] - 1e-6:
            errors.append(f"{a['name']} and {b['name']} overlap in time")
    return errors, notes, items


def combo_key(plan: dict) -> str:
    v = sorted(e["name"] for e in plan.get("video_effects", []))
    t = sorted(e["name"] for e in plan.get("transitions", []))
    return f"{'+'.join(v)} / {'+'.join(t)}" if (v or t) else ""


def previous_combo(video: str) -> str:
    if not LOG.exists():
        return ""
    rows = [r for r in LOG.read_text().splitlines() if r.startswith("| 20")]
    rows = [r for r in rows if r.split("|")[2].strip() != video]
    return rows[-1].split("|")[3].strip() if rows else ""


def log(video: str, plan: dict, items: list) -> None:
    if not LOG.exists():
        LOG.write_text("# Effects log\n\nEvery effect / transition / animation / velocity curve used (ffmpeg equivalents "
                       "of the named CapCut library entries).\n\n"
                       "| Date | Video | Combo | Filter | Title animation | Effects (time, name, category, duration) |\n"
                       "|---|---|---|---|---|---|\n")
    cat = {"video_effects": "video effect", "transitions": "transition", "velocity_effects": "velocity effect"}
    eff = "; ".join(f"{i['from']:.2f}s {i['name']} ({cat[i['group']]}) {i['dur']}s" for i in items) or "hard cuts only"
    cmap = load_json(WORK / "cut_map.json", default={})
    curves = [f"{e['out_start']:.2f}-{e['out_end']:.2f}s Hero curve" for e in cmap.get("events", [])
              if e["kind"] == "hero"]
    if curves:
        eff += "; speed: " + ", ".join(curves)
    line = (f"| {time.strftime('%Y-%m-%d %H:%M')} | {video} | {combo_key(plan) or '-'} | {plan.get('filter') or '-'} | "
            f"{plan.get('title_animation') or '-'} | {eff} |")
    lines = LOG.read_text().rstrip("\n").split("\n")
    if lines[-1].startswith("| 20") and lines[-1].split("|")[2].strip() == video:
        lines[-1] = line
    else:
        lines.append(line)
    LOG.write_text("\n".join(lines) + "\n")


def apply(base: Path, out: Path, video: str) -> dict | None:
    """Render the plan onto `base` (picture only, audio copied). Returns a summary, or None if no plan."""
    if not PLAN.exists():
        return None
    plan = load_json(PLAN)
    cm = load_json(WORK / "cut_map.json")
    errors, notes, items = validate(plan, cm, video)
    if errors:
        die("effects_plan.json breaks the library rules:\n  - " + "\n  - ".join(errors))
    for n in notes:
        print(f"note: {n}")
    dur = probe(base)["duration"]
    fchain = FILTERS.get(plan.get("filter") or "", FILTERS["Cinematic"] if plan.get("filter") else "null")
    # split the timeline at every effect edge (frame-exact), filter each piece, concat
    snap = lambda t: round(round(t * FPS) / FPS, 3)  # noqa: E731  frame grid
    for i in items:          # snap first, so the "is this effect active here" test uses the same edges
        i["f0"], i["f1"] = snap(i["from"]), snap(i["to"])
    edges = sorted({0.0, round(dur, 3)} | {i["f0"] for i in items} | {i["f1"] for i in items})
    tmp = WORK / "fx_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    listing = []
    for k, (a, b) in enumerate(zip(edges, edges[1:])):
        if b - a < 0.5 / FPS:
            continue
        active = [i for i in items if i["f0"] - 1e-6 <= a and b <= i["f1"] + 1e-6]
        # t must start at 0 inside each window, or the time-based recipes (flash, shake, zoom) do nothing
        chain = ",".join(["setpts=PTS-STARTPTS"] + [recipe(i["kind"], b - a) for i in active]
                         + [fchain, f"fps={FPS}", "format=yuv420p"])
        piece = tmp / f"p{k:03d}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", base, "-t", f"{b - a:.4f}", "-an",
             "-vf", chain, "-c:v", "libx264", "-preset", "medium", "-crf", "15", piece])
        listing.append(f"file '{piece}'")
    (tmp / "list.txt").write_text("\n".join(listing) + "\n")
    pic = tmp / "picture.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", pic])
    run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", base, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "copy", "-t", f"{dur:.3f}", out])
    shutil.rmtree(tmp, ignore_errors=True)
    if abs(probe(out)["duration"] - dur) > 0.1:
        die("effects pass changed the video length: not passing it on")
    for i in items:
        i.pop("f0", None), i.pop("f1", None)
    log(video, plan, items)
    summary = {"filter": plan.get("filter"), "title_animation": plan.get("title_animation"),
               "items": items, "notes": notes, "combo": combo_key(plan)}
    save_json(WORK / "effects_applied.json", summary)
    return summary


def suggest(cm: dict) -> dict:
    """A starting plan: Cinematic filter, a shake on the slow-mo (hardest rep), a Pull In at the first
    exercise / section change, Flash In on the hook. The agent edits it to fit the actual moments."""
    plan = {"filter": "Cinematic", "video_effects": [], "transitions": [], "velocity_effects": [],
            "body_effects": [], "title_animation": "Flash In", "pro_approved": False}
    slow = next((e for e in cm["events"] if e["kind"] in ("slow_mo", "hero")), None)
    if slow:
        plan["video_effects"].append({"name": "Camera Shake", "at": round(slow["out_start"] + 0.2, 2), "dur": 0.3,
                                      "why": "hardest rep"})
    names = [s.get("exercise") for s in cm["segments"]]
    join = next((s["out_start"] for i, s in enumerate(cm["segments"][1:], 1)
                 if s.get("exercise") and names[i - 1] and s["exercise"] != names[i - 1]), None)
    if join is None:
        join = next((s["out_start"] for s in cm["segments"] if s["type"] != "hook"), None)
    if join:
        plan["transitions"].append({"name": "Pull In", "at": round(join, 2), "dur": 0.3, "why": "new section"})
    return plan


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    cm = load_json(WORK / "cut_map.json")
    video = load_json(OUT / "job.json", default={}).get("video", "")
    if cmd == "suggest":
        save_json(PLAN, suggest(cm))
        print(json.dumps(load_json(PLAN), indent=2))
        print("wrote output/work/effects_plan.json (a starting point: fit it to the real moments, then check)")
    elif cmd == "check":
        errs, notes, items = validate(load_json(PLAN), cm, video)
        for n in notes:
            print(f"note: {n}")
        for i in items:
            print(f"  {i['from']:6.2f}-{i['to']:6.2f}s  {i['name']:<16} {i['group'][:-1].replace('_', ' ')}  {i['dur']}s")
        if errs:
            die("effects plan breaks the rules:\n  - " + "\n  - ".join(errs))
        print("effects plan OK")
    else:
        die("usage: effects.py suggest|check")
