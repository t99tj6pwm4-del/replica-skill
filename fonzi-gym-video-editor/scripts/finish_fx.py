#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. The Fonzi-style finish, baked into the picture AFTER the Remotion composite.
render_final.py calls it automatically, so it cannot be forgotten; it refuses a file it already finished, so it
cannot run twice.

    python3 scripts/finish_fx.py                       # finish output/final_edit.mp4 in place (normally not needed)
    python3 scripts/finish_fx.py --final F.mp4 --base CLEAN.mp4 [--out G.mp4] [--intro strobe|pulse]
                                 [--drips slow|heavy|wet] [--no-record]

What it does (STYLE.md "Rules for every video"):
  - overlay_props title.style == "fonzi_intro": the intro card (rule 0) over the first seconds, via
    style_fx.py intro: Rubik Dirt gold title below his face, Fonzi logo behind him, title flickering to the
    song's beat (cut_map.json "beat"), whoosh into beat 1 + impact on beat 1. Window = from 0 to the end of the
    hook (props title.to), never into the first gold exercise title / end card, at most config intro.max_dur.
  - overlay_props endCard.style == "logo_drip": the dripping logo end card (rule 3, style_fx.py logo) over the
    end-card window, on the clean picture of those seconds.
  - one splice + one encode: picture = intro | the rendered final | logo card; audio = the final's own track
    with the intro sfx and the logo sfx (-6 dB) mixed UNDER it (peak limiter at -1 dBFS, nothing below it changes).
Rotation: the intro style alternates strobe <-> pulse per video and the logo drips rotate slow -> heavy -> wet,
recorded per video in posted/style_rotation.json (a re-render of the same video keeps its picks). Storyboard
overrides: "intro": {"style", "title", "subtitle", "dur"}, "end_card": {"drips"}.
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
INTRO_STYLES = ["strobe", "pulse"]
DRIPS = ["slow", "heavy", "wet"]


def cfg() -> dict:
    return {"max_dur": 3.0, "min_dur": 1.2, "logo_sfx_db": -6, **(load_config().get("intro") or {})}


def picks(video: str, sb: dict) -> tuple[str, str]:
    """(intro style, logo drips) for this video: the storyboard's word wins, then this video's earlier pick
    (re-renders stay the same), else the next one after the last video's."""
    hist = load_json(ROTATION, default={"videos": []})["videos"]
    mine = next((e for e in hist if e.get("video") == video), None)
    others = [e for e in hist if e.get("video") != video]
    last = others[-1] if others else {}
    intro = (sb.get("intro") or {}).get("style") or (mine or {}).get("intro")
    if not intro:
        intro = INTRO_STYLES[(INTRO_STYLES.index(last["intro"]) + 1) % 2] if last.get("intro") in INTRO_STYLES \
            else INTRO_STYLES[0]
    drips = (sb.get("end_card") or {}).get("drips") or (mine or {}).get("drips")
    if not drips:
        drips = DRIPS[(DRIPS.index(last["drips"]) + 1) % 3] if last.get("drips") in DRIPS else "heavy"
    if intro not in INTRO_STYLES or drips not in DRIPS:
        die(f"finish: unknown intro style {intro!r} / drips {drips!r}")
    return intro, drips


def record(video: str, intro: str | None, drips: str | None):
    data = load_json(ROTATION, default={"videos": []})
    data["note"] = ("Fonzi style rotation (finish_fx.py): intro strobe <-> pulse, logo drips slow -> heavy -> wet; "
                    "one entry per video, in render order")
    hist = [e for e in data["videos"] if e.get("video") != video]
    hist.append({"video": video, "intro": intro, "drips": drips, "updated": time.strftime("%Y-%m-%d %H:%M")})
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


def finish(final: Path, base: Path, props: dict, out: Path | None = None, intro_style: str | None = None,
           drips: str | None = None, rec: bool | None = None) -> dict:
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
    style, drp = picks(video, sb)
    style, drp = intro_style or style, drips or drp
    info = probe(final)
    nf = int(round(info["duration"] * FPS))
    total = nf / FPS          # the picture's exact length (the container can carry a few ms of AAC tail)
    tmp = WORK / "finish_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    entry = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "source": rel(final), "base": rel(base)}
    ni, f0 = 0, nf
    inputs, vparts, aparts, alabels = ["-i", str(final)], [], [], ["[0:a]"]
    if want_intro:
        t = props["title"]
        ov = sb.get("intro") or {}
        dur = intro_window(props, sb)
        bts, bpm, phase = beats(cm, sb)
        piece = tmp / "intro_piece.mp4"
        rep = style_fx.intro(final, piece, ov.get("title") or t["text"], ov.get("subtitle", t.get("subtitle", "")),
                             style, bts, bpm, phase, dur, piece=True, mask_src=base, report=WORK / "intro_card.json")
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
        style_fx.logo(card, bg, drp, (n_logo + 0.5) / FPS)
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
                 drips=drp if want_logo else None)
    log["finished"] = (log["finished"] + [entry])[-30:]
    save_json(LOG, log)
    real = out.resolve() == (OUT / "final_edit.mp4").resolve()
    if rec if rec is not None else real:
        record(video, style if want_intro else None, drp if want_logo else None)
        import effects
        effects.log_title_style(video, {"style": f"Fonzi intro card ({style})" if want_intro else "no intro card",
                                        "at": 0.0, "dur": ni / FPS})
    print(f"finish: {'intro ' + style + f' 0-{ni / FPS:.2f}s' if want_intro else 'no intro'}; "
          f"{'logo end card (' + drp + f' drips) {f0 / FPS:.2f}s-end' if want_logo else 'no logo card'}; "
          f"wrote {rel(out)} ({got['duration']:.3f}s), logged in {rel(LOG)}")
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", type=Path, default=OUT / "final_edit.mp4")
    ap.add_argument("--base", type=Path, help="the clean picture the graphics were laid over (default: the cut)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--intro", choices=INTRO_STYLES)
    ap.add_argument("--drips", choices=DRIPS)
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args()
    finish(a.final, a.base or base_video(), load_json(WORK / "overlay_props.json"), a.out, a.intro, a.drips,
           False if a.no_record else None)


if __name__ == "__main__":
    main()
