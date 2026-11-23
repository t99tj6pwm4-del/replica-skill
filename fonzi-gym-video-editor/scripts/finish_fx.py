#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. The Fonzi-style finish, baked into the picture AFTER the Remotion composite.
render_final.py calls it automatically, so it cannot be forgotten; it refuses a file it already finished, so it
cannot run twice.

    python3 scripts/finish_fx.py                       # finish output/final_edit.mp4 in place (normally not needed)
    python3 scripts/finish_fx.py --final F.mp4 --base CLEAN.mp4 [--out G.mp4] [--intro strobe|pulse|glitch|smash]
                                 [--logo flat|3d] [--drips slow|heavy|wet] [--no-record]

What it does (STYLE.md "Rules for every video"):
  - overlay_props title.style == "fonzi_intro": the intro card (rule 0) over the first seconds, via
    style_fx.py intro: Rubik Dirt gold title below his face, Fonzi logo behind him, title flickering to the
    song's beat (cut_map.json "beat"), whoosh into beat 1 + impact on beat 1. Window = from 0 to the end of the
    hook (props title.to), never into the first gold exercise title / end card, at most config intro.max_dur.
  - overlay_props endCard.style == "logo_drip": the dripping logo end card (rule 3, style_fx.py logo) over the
    end-card window, on the clean picture of those seconds.
  - one splice + one encode: picture = intro | the rendered final | logo card; audio = the final's own track
    with the intro sfx and the logo sfx (-6 dB) mixed UNDER it (peak limiter at -1 dBFS, nothing below it changes).
Rotation (Round 7, 2026-11-22): the intro title style cycles strobe -> pulse -> glitch -> smash per video (config
intro.title_styles), the intro logo alternates flat <-> 3d on its own (config intro.logo_styles) and the logo drips
rotate slow -> heavy -> wet, recorded per video in posted/style_rotation.json (a re-render of the same video keeps
its picks; no history = strobe / flat; entries from before round 7 without a logo count as flat). A glitch / smash
that cannot be drawn cleanly (style_fx.IntroStyleUnfit) is rendered as pulse instead; the entry keeps
intro_planned = the planned style + fallback_reason, and the next video continues the cycle after the planned one.
Storyboard overrides: "intro": {"style", "logo", "smash_keep_out", "face_box", "title", "subtitle", "dur"},
"end_card": {"drips"}. Only the real render (out = output/final_edit.mp4) is recorded.
Every finish is logged in output/work/finish_fx.json by the finished file's sha256 (qa_check.py reads it).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (FPS, OUT, POSTED, ROOT, WORK, base_video, die, load_config, load_json, probe, rel,  # noqa: E402
                    run, save_json, sha256)

LOG = WORK / "finish_fx.json"
ROTATION = POSTED / "style_rotation.json"
ALL_INTRO_STYLES = ["strobe", "pulse", "glitch", "smash"]   # style_fx.TITLE_STYLES
ALL_LOGO_STYLES = ["flat", "3d"]                            # style_fx.LOGO_STYLES
DRIPS = ["slow", "heavy", "wet"]
FALLBACK = "pulse"          # style_sheet title_styles.fallback: an unfit glitch / smash is rendered as pulse


def cfg() -> dict:
    return {"max_dur": 3.0, "min_dur": 1.2, "logo_sfx_db": -6, "title_styles": ALL_INTRO_STYLES,
            "logo_styles": ALL_LOGO_STYLES, **(load_config().get("intro") or {})}


def _cycle(key: str, known: list[str]) -> list[str]:
    got = [str(v) for v in (cfg().get(key) or known)]
    bad = [v for v in got if v not in known]
    if bad or len(set(got)) != len(got):
        die(f"config.yaml intro.{key}: {got} (allowed: {', '.join(known)}, each once)")
    return got


INTRO_STYLES = _cycle("title_styles", ALL_INTRO_STYLES)    # fixed cycle: strobe -> pulse -> glitch -> smash
LOGO_STYLES = _cycle("logo_styles", ALL_LOGO_STYLES)       # flat <-> 3d


def _planned(e: dict) -> str | None:
    """The style the cycle asked for in a rotation entry (intro_planned; entries before round 7: intro)."""
    v = e.get("intro_planned") or e.get("intro")
    return v if v in INTRO_STYLES else None


def picks(video: str, sb: dict) -> tuple[str, str, str]:
    """(intro style, intro logo, logo drips) for this video (style_sheet rotation rules): the storyboard's word
    wins (intro.style / intro.logo / end_card.drips), then this video's earlier entry (intro_planned, so a re-render
    keeps its picks even after a fallback), else the next one after the last OTHER video's; no history = strobe /
    flat; an entry without a logo key counts as flat (every video before round 7 shipped flat)."""
    hist = load_json(ROTATION, default={"videos": []})["videos"]
    mine = next((e for e in hist if e.get("video") == video), None)
    others = [e for e in hist if e.get("video") != video]
    last = others[-1] if others else {}
    last_intro = next((e for e in reversed(others) if _planned(e)), None)    # last other video WITH an intro card
    ov = sb.get("intro") or {}
    intro = ov.get("style") or (mine and _planned(mine))
    if not intro:
        intro = INTRO_STYLES[(INTRO_STYLES.index(_planned(last_intro)) + 1) % len(INTRO_STYLES)] if last_intro \
            else INTRO_STYLES[0]
    logo = ov.get("logo") or (mine and _planned(mine) and (mine.get("logo") or "flat"))
    if not logo:
        prev = (last_intro.get("logo") or "flat") if last_intro else None
        logo = LOGO_STYLES[(LOGO_STYLES.index(prev) + 1) % len(LOGO_STYLES)] if prev in LOGO_STYLES \
            else LOGO_STYLES[0]
    drips = (sb.get("end_card") or {}).get("drips") or (mine or {}).get("drips")
    if not drips:
        drips = DRIPS[(DRIPS.index(last["drips"]) + 1) % 3] if last.get("drips") in DRIPS else "heavy"
    if intro not in INTRO_STYLES or logo not in LOGO_STYLES or drips not in DRIPS:
        die(f"finish: unknown intro style {intro!r} ({' | '.join(INTRO_STYLES)}) / logo {logo!r} "
            f"({' | '.join(LOGO_STYLES)}) / drips {drips!r} ({' | '.join(DRIPS)})")
    return intro, logo, drips


def record(video: str, intro: str | None, drips: str | None, planned: str | None = None, logo: str | None = None,
           fallback_reason: str | None = None):
    """One entry per video, in render order: intro = rendered, intro_planned = what the cycle asked for."""
    data = load_json(ROTATION, default={"videos": []})
    data["note"] = ("Fonzi style rotation (finish_fx.py, Round 7): intro title strobe -> pulse -> glitch -> smash "
                    "(intro = rendered, intro_planned = what the cycle asked for; an unfit glitch / smash renders "
                    "pulse with fallback_reason), intro logo flat <-> 3d (no logo key = flat), logo drips slow -> "
                    "heavy -> wet; one entry per video, in render order")
    hist = [e for e in data["videos"] if e.get("video") != video]
    e = {"video": video, "intro": intro, "intro_planned": (planned or intro) if intro else None,
         "logo": logo if intro else None, "drips": drips}
    if intro and e["intro_planned"] != intro:
        e["fallback_reason"] = fallback_reason or f"{e['intro_planned']} unfit"
    e["updated"] = time.strftime("%Y-%m-%d %H:%M")
    hist.append(e)
    data["videos"] = hist
    save_json(ROTATION, data)


def beats(cm: dict, sb: dict) -> tuple[list[float] | None, float | None, float]:
    b = cm.get("beat") or {}
    if b.get("period"):
        return None, 60.0 / float(b["period"]), float(b.get("phase", 0.0)) % float(b["period"])
    if sb.get("song_bpm"):
        print("note: no beat in cut_map.json, using the storyboard's song_bpm from 0.5 s")
        return None, float(sb["song_bpm"]), 0.5
    print("note: no song beat known, flickering the title on a 100 bpm grid from 0.6 s")
    return None, 100.0, 0.6


def intro_window(props: dict, sb: dict) -> float:
    c = cfg()
    t = props.get("title") or {}
    dur = min(float(c["max_dur"]), float((sb.get("intro") or {}).get("dur") or t.get("to") or c["max_dur"]))
    for e in props.get("exercise_titles") or []:          # never into the first gold exercise title
        if float(e["at"]) > 0.3:
            dur = min(dur, float(e["at"]))
    if props.get("endCard"):
        dur = min(dur, float(props["endCard"]["from"]))
    if dur < float(c["min_dur"]):
        die(f"finish: only {dur:.2f}s before the first title; the intro card needs at least {c['min_dur']}s. "
            "Ask the Director to give the hook more room.")
    return round(round(dur * FPS) / FPS, 3)


def _box(v, what: str):
    """Storyboard [x0,y0,x1,y1] -> tuple (or None)."""
    if v is None:
        return None
    try:
        b = tuple(int(x) for x in v)
    except (TypeError, ValueError):
        b = ()
    if len(b) != 4:
        die(f"finish: storyboard intro.{what} {v!r} must be [x0, y0, x1, y1]")
    return b


def _keep_out(v):
    """Storyboard intro.smash_keep_out: left | right | none | [x0,y0,x1,y1] (None = auto)."""
    if v is None or (isinstance(v, str) and v.lower() in ("left", "right", "none")):
        return v.lower() if isinstance(v, str) else None
    if isinstance(v, str):
        if v.count(",") == 3:
            return _box(v.split(","), "smash_keep_out")
        die(f"finish: storyboard intro.smash_keep_out {v!r} (left | right | none | [x0, y0, x1, y1])")
    return _box(v, "smash_keep_out")


def finish(final: Path, base: Path, props: dict, out: Path | None = None, intro_style: str | None = None,
           drips: str | None = None, rec: bool | None = None, logo_style: str | None = None) -> dict:
    import style_fx
    out = out or final
    sb = load_json(OUT / "storyboard.json", default={})
    cm = load_json(WORK / "cut_map.json", default={})
    video = load_json(OUT / "job.json", default={}).get("video", "")
    log = load_json(LOG, default={"finished": []})
    fsha = sha256(final)
    done = next((e for e in log["finished"] if e["sha256"] == fsha), None)
    if done:
        die(f"finish: {rel(final)} was already finished on {done['at']} (intro / end card baked in). "
            "Re-run render_final.py for a fresh render instead of finishing twice.")
    want_intro = (props.get("title") or {}).get("style") == "fonzi_intro"
    want_logo = (props.get("endCard") or {}).get("style") == "logo_drip"
    if want_intro and props.get("opener"):
        print("note: Alfonso's own opener image covers the start: no intro card on top of it")
        want_intro = False
    if not (want_intro or want_logo):
        print("finish: nothing to bake (no fonzi_intro title, no logo_drip end card)")
        return {}
    style, logo, drp = picks(video, sb)
    style, logo, drp = intro_style or style, logo_style or logo, drips or drp
    if style not in ALL_INTRO_STYLES or logo not in ALL_LOGO_STYLES:
        die(f"finish: unknown intro style {style!r} / logo {logo!r}")
    planned, fallback = style, None
    info = probe(final)
    nf = int(round(info["duration"] * FPS))
    total = nf / FPS          # the picture's exact length (the container can carry a few ms of AAC tail)
    tmp = WORK / "finish_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    entry = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "source": rel(final), "base": rel(base)}
    ni, f0 = 0, nf
    inputs, vparts, aparts, alabels = ["-i", str(final)], [], [], ["[0:a]"]
    sounds: list[dict] = []     # every library / fallback sound baked in here -> output/work/sfx_log.json
    if want_intro:
        t = props["title"]
        ov = sb.get("intro") or {}
        dur = intro_window(props, sb)
        bts, bpm, phase = beats(cm, sb)
        piece = tmp / "intro_piece.mp4"
        args = (final, piece, ov.get("title") or t["text"], ov.get("subtitle", t.get("subtitle", "")))
        kw = dict(piece=True, mask_src=base, report=WORK / "intro_card.json", face_box=_box(ov.get("face_box"),
                  "face_box"), logo=logo, smash_keep_out=_keep_out(ov.get("smash_keep_out")))
        try:
            style_fx.SOUNDS_USED.clear()
            rep = style_fx.intro(*args, style, bts, bpm, phase, dur, **kw)
        except style_fx.IntroStyleUnfit as e:
            if style == FALLBACK:
                raise
            fallback = f"{getattr(e, 'style', style)} unfit: {getattr(e, 'reason', e)}"
            print(f"finish: intro {style} cannot be drawn cleanly for this video ({getattr(e, 'reason', e)}); "
                  f"rendering {FALLBACK} instead (recorded: intro {FALLBACK}, planned {style})")
            style = FALLBACK
            style_fx.SOUNDS_USED.clear()
            rep = style_fx.intro(*args, style, bts, bpm, phase, dur, **kw)
        sounds += [dict(e, piece="intro") for e in style_fx.SOUNDS_USED]
        ni = rep["frames"]
        inputs += ["-i", str(piece)]
        k = len(inputs) // 2 - 1
        vparts.append(f"[{k}:v]trim=start_frame=0:end_frame={ni},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[vi]")
        aparts.append(f"[{k}:a]anull[ai]")
        alabels.append("[ai]")
        entry["intro"] = rep
    if want_logo:
        ec = props["endCard"]
        f0 = int(round(float(ec["from"]) * FPS))
        n_logo = nf - f0
        if n_logo < FPS:
            die(f"finish: end card window is only {n_logo} frames")
        bg = tmp / "logo_bg.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{f0 / FPS:.3f}", "-i", base, "-t", f"{(n_logo + 2) / FPS:.3f}",
             "-an", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", bg])
        card = tmp / "logo_card.mp4"
        style_fx.SOUNDS_USED.clear()
        style_fx.logo(card, bg, drp, (n_logo + 0.5) / FPS)
        sounds += [dict(e, piece="logo_card", at=round(e["at"] + f0 / FPS, 3), db=e["db"] + cfg()["logo_sfx_db"])
                   for e in style_fx.SOUNDS_USED]
        got = probe(card)
        if int(round(got["duration"] * FPS)) < n_logo:
            die(f"finish: logo card is {got['duration']:.2f}s, the end card window needs {n_logo / FPS:.2f}s")
        inputs += ["-i", str(card)]
        k = len(inputs) // 2 - 1
        vparts.append(f"[{k}:v]trim=start_frame=0:end_frame={n_logo},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[vl]")
        ms = int(f0 * 1000 / FPS)
        aparts.append(f"[{k}:a]volume={cfg()['logo_sfx_db']}dB,adelay={ms}|{ms}[al]")
        alabels.append("[al]")
        entry["end_card"] = {"style": "logo_drip", "drips": drp, "from": round(f0 / FPS, 3), "frames": n_logo}
    mid = f"[0:v]trim=start_frame={ni}:end_frame={f0},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[vm]"
    order = (["[vi]"] if want_intro else []) + ["[vm]"] + (["[vl]"] if want_logo else [])
    fc = ";".join(vparts + [mid, "".join(order) + f"concat=n={len(order)}:v=1:a=0[v]"] + aparts +
                  ["".join(alabels) + f"amix=inputs={len(alabels)}:duration=first:normalize=0:dropout_transition=0,"
                   "alimiter=limit=0.89:level=0:latency=1[a]"])
    res = tmp / "finished.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", res])
    got = probe(res)
    if abs(got["duration"] - total) > 0.02:
        die(f"finish: the finished file is {got['duration']:.3f}s, the render was {total:.3f}s: not passing it on")
    out.parent.mkdir(parents=True, exist_ok=True)
    res.replace(out)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    entry.update(output=rel(out), sha256=sha256(out), intro_style=style if want_intro else None,
                 intro_planned=planned if want_intro else None, logo_style=logo if want_intro else None,
                 drips=drp if want_logo else None)
    if want_intro and fallback:
        entry["fallback_reason"] = fallback
    log_sounds(sounds, out)
    log["finished"] = (log["finished"] + [entry])[-30:]
    save_json(LOG, log)
    real = out.resolve() == (OUT / "final_edit.mp4").resolve()
    if rec if rec is not None else real:
        record(video, style if want_intro else None, drp if want_logo else None, planned, logo, fallback)
        import effects
        name = f"Fonzi intro card ({style} title, {logo} logo" + (f", planned {planned}: fell back" if fallback
                                                                   else "") + ")"
        effects.log_title_style(video, {"style": name if want_intro else "no intro card", "at": 0.0, "dur": ni / FPS})
    print(f"finish: {'intro ' + style + ' / logo ' + logo + f' 0-{ni / FPS:.2f}s' if want_intro else 'no intro'}"
          f"{f' (planned {planned}, fell back to {FALLBACK})' if want_intro and fallback else ''}; "
          f"{'logo end card (' + drp + f' drips) {f0 / FPS:.2f}s-end' if want_logo else 'no logo card'}; "
          f"wrote {rel(out)} ({got['duration']:.3f}s), logged in {rel(LOG)}")
    return entry


def log_sounds(sounds: list[dict], out: Path):
    """Add the intro / logo-card sounds to output/work/sfx_log.json (render_final.add_sfx wrote the text-move hits
    just before; an older finish_fx block is replaced, never doubled). Only for the real final."""
    if out.resolve() != (OUT / "final_edit.mp4").resolve():
        return
    p = WORK / "sfx_log.json"
    d = load_json(p) if p.exists() else {"events": []}
    d["events"] = sorted([e for e in d.get("events") or [] if e.get("by") != "style_fx"] + sounds,
                         key=lambda e: e["at"])
    d["library_ids"] = sorted({e["library_id"] for e in d["events"] if e.get("library_id")})
    d["fallbacks"] = sorted({e["role"] for e in d["events"] if e.get("source") == "fallback"})
    save_json(p, d)


def main():
    ap = argparse.ArgumentParser(description="Bake the Fonzi intro card + logo end card into a rendered final "
                                 "(normally run by render_final.py).")
    ap.add_argument("--final", type=Path, default=OUT / "final_edit.mp4")
    ap.add_argument("--base", type=Path, help="the clean picture the graphics were laid over (default: the cut)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--intro", choices=ALL_INTRO_STYLES, help="intro title style (default: the rotation's pick)")
    ap.add_argument("--logo", choices=ALL_LOGO_STYLES, help="intro logo style (default: the rotation's pick)")
    ap.add_argument("--drips", choices=DRIPS)
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args()
    finish(a.final, a.base or base_video(), load_json(WORK / "overlay_props.json"), a.out, a.intro, a.drips,
           False if a.no_record else None, logo_style=a.logo)


if __name__ == "__main__":
    main()
