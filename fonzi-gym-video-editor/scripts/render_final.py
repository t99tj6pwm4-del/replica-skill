#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Renders the animated graphics with Remotion and lays them over the cut.

    python3 scripts/render_final.py            # -> output/final_edit.mp4 (+ output/carousel/ if 2+ exercises)
    python3 scripts/render_final.py --preview 12.5 31   # just stills at those seconds, for a quick look
    python3 scripts/render_final.py --title-style layered-gold   # Layered Title (Documentary Gold) only, no subtitles
    python3 scripts/render_final.py --title-style layered-gold-plus   # layered title + the usual graphics (Alfonso asks)
    python3 scripts/render_final.py --out output/intro_test/final_edit_test.mp4   # a test render, final_edit.mp4 untouched
    python3 scripts/render_final.py --intro-style glitch --logo-style 3d   # force the intro title / logo style
        # (strobe | pulse | glitch | smash, flat | 3d; passed to finish_fx.finish; default = the rotation's pick)

After the composite it ALWAYS runs scripts/finish_fx.py (Fonzi style, STYLE.md rules 0 and 3): the Rubik Dirt intro
card over the hook (props title.style "fonzi_intro"; title strobe -> pulse -> glitch -> smash and logo flat <-> 3d by
rotation, an unfit glitch / smash falls back to pulse; only a render to output/final_edit.mp4 is recorded in
posted/style_rotation.json, an --out test render never is) and the dripping logo end card
(endCard.style "logo_drip"), baked into the picture in one pass. Since 2026-11-23 the intro card is preceded by the
logo opener (~1.5 s of the end-card look on the beat grid, config intro.opener; `--no-opener` = test only). The --preview stills show only the Remotion layer:
the intro and the logo card are not in them (look at output/work/intro_card.json and the final's frames instead).

The picture itself is never changed: Remotion renders a transparent graphics layer and ffmpeg
composites it on top of output/multicam_version.mp4 (or output/cut_version.mp4 if there is no multicam pass). Audio is copied through untouched.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, REMOTION, W, WORK, base_video, brand, die, load_json, probe, rel, run, save_json  # noqa: E402


def browser_args() -> list[str]:
    exe = os.environ.get("REMOTION_BROWSER")
    if not exe:
        found = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"))
        exe = found[-1] if found else None
    return [f"--browser-executable={exe}"] if exe else []  # otherwise Remotion fetches its own


def check_text(props: dict):
    """English only, no hashtags: refuse to render anything else.
    Approved exception (Alfonso, 2026-11-17): the Spanish lines of the pop-up cards (props.popups) may use
    Spanish letters and the • separator. Still no hashtags anywhere."""
    from add_popups import popup_text_ok
    bad = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and not path.endswith(("color", "Color", "kind")):
            if path.startswith("props.popups"):
                if not popup_text_ok(node):
                    bad.append(f"{path}: {node!r}")
            elif "#" in node or re.search(r"[^\x20-\x7E]", node):
                bad.append(f"{path}: {node!r}")

    walk({k: v for k, v in props.items() if k != "brand"}, "props")
    if bad:
        die("on-screen text must be English with no hashtags:\n  " + "\n  ".join(bad))


def remotion(args: list[str]):
    if not (REMOTION / "node_modules").exists():
        die("Remotion is not installed. Run: bash scripts/setup.sh")
    run(["npx", "remotion", *args, *browser_args(), "--log=error"], cwd=REMOTION)


def render_carousel(sb: dict, cm: dict, cdir: Path | None = None):
    items = sb.get("carousel") or []
    if len(items) < 2:
        return None
    b = brand()
    cdir, pub = cdir or OUT / "carousel", WORK / "public"
    shutil.rmtree(cdir, ignore_errors=True)
    shutil.rmtree(pub, ignore_errors=True)
    cdir.mkdir(parents=True)
    shutil.copytree(REMOTION / "public", pub)
    cut = base_video()

    def still(name: str, t: float):
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", cut, "-frames:v", "1", "-q:v", "2", pub / name])
        return name

    slides = [{"kind": "cover", "title": sb["title"].upper(), "detail": f"{len(items)} EXERCISES",
               "index": 0, "total": len(items),
               "image": still("cover.jpg", min(cm["body_end"] * 0.5, cm["duration"] - 0.1))}]
    for i, it in enumerate(items, 1):
        seg = next((s for s in cm["segments"] if s.get("exercise") == it["exercise"]), None)
        t = (seg["out_start"] + seg["out_end"]) / 2 if seg else cm["body_end"] * i / (len(items) + 1)
        slides.append({"kind": "exercise", "title": it["exercise"].upper(), "detail": it.get("sets_reps", ""),
                       "cue": it.get("cue", ""), "index": i, "total": len(items), "image": still(f"ex{i}.jpg", t)})
    files = []
    for i, slide in enumerate(slides):
        pfile = WORK / f"carousel_{i}.json"
        import text_look
        save_json(pfile, {"brand": {k: b[k] for k in ("name", "handle", "color", "textColor", "darkColor")}, "slide": slide,
                          "textLook": text_look.for_remotion()})
        out = cdir / f"slide_{i + 1:02d}.png"
        remotion(["still", "src/index.ts", "CarouselSlide", str(out), f"--props={pfile}", f"--public-dir={pub}"])
        files.append(rel(out))
        pfile.unlink()
    caption = sb.get("caption") or sb["title"]
    lines = [caption, ""] + [f"{i}. {it['exercise']} - {it.get('sets_reps', '')}".rstrip(" -") for i, it in enumerate(items, 1)]
    save_json(cdir / "carousel.json", {"title": sb["title"], "slides": files, "caption": "\n".join(lines),
                                       "exercises": [{"exercise": it["exercise"], "sets_reps": it.get("sets_reps", ""),
                                                      "cue": it.get("cue", "")} for it in items]})
    shutil.rmtree(pub, ignore_errors=True)
    return files


def target_path() -> Path:
    """Where the finished video goes: output/final_edit.mp4, or --out PATH for a test render."""
    if "--out" in sys.argv:
        p = Path(sys.argv[sys.argv.index("--out") + 1])
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return OUT / "final_edit.mp4"


INTRO_STYLES = ("strobe", "pulse", "glitch", "smash")   # finish_fx.ALL_INTRO_STYLES
LOGO_STYLES = ("flat", "3d")                            # finish_fx.ALL_LOGO_STYLES


def flag(name: str, choices: tuple[str, ...]) -> str | None:
    """--name VALUE or --name=VALUE, checked against choices (None when not given)."""
    v = next((a.split("=", 1)[1] for a in sys.argv if a.startswith(name + "=")), None)
    if name in sys.argv:
        i = sys.argv.index(name)
        v = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
    if v is not None and v not in choices:
        die(f"{name} {v!r}: use one of {' | '.join(choices)}")
    return v


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__.strip())
        print("\nflags: --out PATH  --preview T [T ...]  --title-style normal|layered-gold|layered-gold-plus  "
              f"--intro-style {'|'.join(INTRO_STYLES)}  --logo-style {'|'.join(LOGO_STYLES)}  --no-opener (test only)")
        return
    intro_style, logo_style = flag("--intro-style", INTRO_STYLES), flag("--logo-style", LOGO_STYLES)
    if not (OUT / "cut_version.mp4").exists():
        die("output/cut_version.mp4 is missing: the Cuts Agent has to run first")
    cut = base_video()   # multicam_version.mp4 when the Multicam/B-Roll Agent ran
    print(f"laying graphics over {rel(cut)}")
    props_path = WORK / "overlay_props.json"
    props = load_json(props_path)
    check_text(props)
    # Alfonso 2026-11-23 (answer 24): THE text look from config.yaml text_look, the same numbers the Python titles use
    import text_look
    props["textLook"] = text_look.for_remotion()
    props.setdefault("brand", {}).update({k: v for k, v in brand().items() if k in ("color", "textColor", "darkColor")})
    props["brand"]["popupColor"] = brand().get("popup_color", "#FFFFFF")
    save_json(props_path, props)
    info = probe(cut)
    if abs(info["duration"] - props["duration"]) > 0.25:
        die("overlay_props.json was built for a different cut. Re-run scripts/build_overlay_props.py")

    if "--preview" in sys.argv:
        pdir = WORK / "preview"
        pdir.mkdir(parents=True, exist_ok=True)
        for t in sys.argv[sys.argv.index("--preview") + 1:]:
            frame = min(int(float(t) * FPS), int(props["duration"] * FPS) - 1)
            png, jpg = pdir / f"ov_{frame}.png", pdir / f"preview_{float(t):07.2f}.jpg"
            remotion(["still", "src/index.ts", "Overlay", str(png), f"--frame={frame}", f"--props={props_path}"])
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{frame / FPS:.3f}", "-i", cut, "-i", png, "-filter_complex",
                 "[0:v][1:v]overlay,scale=-2:960", "-frames:v", "1", "-q:v", "3", jpg])
            png.unlink()
            print(rel(jpg))
        return

    # CapCut-library effects (filter, video effects, transitions, velocity) on the picture, audio untouched
    import effects
    video_name = load_json(OUT / "job.json", default={}).get("video", "")
    fx_base = WORK / "effects_base.mp4"
    fx = effects.apply(cut, fx_base, video_name)
    if fx:
        print(f"effects: filter {fx['filter']}, " + ", ".join(f"{i['name']} {i['dur']}s @{i['from']:.2f}s" for i in fx["items"]))
        cut = fx_base
    if fx and fx.get("title_animation") and props.get("title"):
        props["title"]["animation"] = fx["title_animation"]
        save_json(props_path, props)

    # Layered Title (Documentary Gold): only when asked (--title-style layered-gold, or the storyboard says so).
    # Then the video gets ONLY that title: no subtitles / captions, no lower-thirds, no title or end card.
    style = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--title-style=")), None)
    if "--title-style" in sys.argv:
        style = sys.argv[sys.argv.index("--title-style") + 1]
    style = style or load_json(OUT / "storyboard.json", default={}).get("title_style") or "normal"
    if style == "layered-gold-plus":
        # Alfonso's exception: the layered title baked into the picture, then the usual graphics on top
        import layered_title
        plan = layered_title.plan_from_storyboard()
        if not plan:
            die('--title-style layered-gold-plus needs "layered_title": {"at", "dur", "intro_line"} in storyboard.json')
        lt_base = WORK / "layered_base.mp4"
        lt = layered_title.build(cut, lt_base, plan["at"], plan["dur"], plan["first"], plan["last"], plan["intro"],
                                 plan.get("ys"))
        print(f"layered title (plus the usual graphics): {lt['first']} (behind) / {lt['intro_line']} / "
              f"{lt['last']} (in front) at {lt['at']:.2f}s for {lt['dur']:.2f}s")
        effects.log_title_style(video_name, lt)
        cut = lt_base
        props["title_style"] = "layered-gold-plus"
        save_json(props_path, props)
    elif style == "layered-gold":
        import layered_title
        plan = layered_title.plan_from_storyboard()
        if not plan:
            die('--title-style layered-gold needs "layered_title": {"at", "dur", "intro_line"} in storyboard.json')
        lt_base = WORK / "layered_base.mp4"
        lt = layered_title.build(cut, lt_base, plan["at"], plan["dur"], plan["first"], plan["last"], plan["intro"],
                                 plan.get("ys"))
        print(f"layered title: {lt['first']} (behind) / {lt['intro_line']} / {lt['last']} (in front) "
              f"at {lt['at']:.2f}s for {lt['dur']:.2f}s")
        effects.log_title_style(video_name, lt)
        final = target_path()
        final.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", lt_base, "-map", "0:v", "-map", "0:a?", "-c:v", "libx264",
             "-preset", "medium", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "copy", "-movflags", "+faststart", final])
        lt_base.unlink(missing_ok=True)
        fx_base.unlink(missing_ok=True)
        props.update({"title": None, "captions": [], "lowerThirds": [], "callouts": [], "endCard": None,
                      "progress": [], "title_style": "layered-gold"})
        save_json(props_path, props)
        out = probe(final)
        print(f"wrote  {rel(final)}  {out['video']['width']}x{out['video']['height']}  {out['duration']:.2f}s "
              "(layered title only, no subtitles)")
        return
    # Per-exercise layered titles (Alfonso, 2026-11-15): replace the lower-thirds when the storyboard has them
    import layered_title as _lt
    if _lt.exercise_plans():
        ex_base = WORK / "exercise_base.mp4"
        infos = _lt.build_exercise_titles(cut, ex_base)
        for i in infos:
            where = "in front, no word behind" if i.get("front_only") else "behind"
            print(f"exercise title: {i['first']} ({where}) / {i['last']} (in front) at {i['at']:.2f}s for {i['dur']:.2f}s")
        cut = ex_base
        props["lowerThirds"] = []
        props["exercise_titles"] = [{"at": i["at"], "dur": i["dur"], "text": f"{i['first']} {i['last']}".strip()}
                                    for i in infos]
        save_json(props_path, props)
    overlay = WORK / "overlay.mov"
    print(f"rendering {props['duration']:.1f}s of motion graphics with Remotion (a few minutes) ...")
    remotion(["render", "src/index.ts", "Overlay", str(overlay), f"--props={props_path}",
              "--codec=prores", "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png",
              f"--concurrency={os.cpu_count() or 2}"])
    final = target_path()
    final.parent.mkdir(parents=True, exist_ok=True)
    # optional opener image (Alfonso's own thumbnail): full frame over everything from 0 to "to", audio untouched
    opener = props.get("opener") or {}
    extra, fc = [], f"[0:v][1:v]overlay=format=auto,fps={FPS},format=yuv420p[v]"
    if opener.get("image"):
        extra = ["-loop", "1", "-t", f"{info['duration']:.3f}", "-i", str(OUT.parent / opener["image"])]
        fc = (f"[0:v][1:v]overlay=format=auto,fps={FPS}[g];"
              f"[2:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}[op];"
              f"[g][op]overlay=enable='lt(t,{float(opener['to']):.3f})',format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-i", overlay, *extra, "-filter_complex",
         fc, "-map", "[v]", "-map", "0:a?",
         "-t", f"{info['duration']:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart", final])
    measure_text_look(overlay, props, final)
    overlay.unlink(missing_ok=True)
    out = probe(final)
    v = out["video"]
    print(f"wrote  {rel(final)}  {v['width']}x{v['height']} {v['fps']}fps {v['codec']}+"
          f"{out['audio']['codec'] if out['audio'] else 'NO AUDIO'}  {out['duration']:.2f}s")

    mute_if_rule(final)
    add_sfx(final, props)
    # Fonzi finish (intro card + logo end card), always, exactly once per render, on the clean picture `cut`
    import finish_fx
    finish_fx.finish(final, cut, props, intro_style=intro_style, logo_style=logo_style,
                     opener=False if "--no-opener" in sys.argv else None)
    fx_base.unlink(missing_ok=True)
    (WORK / "layered_base.mp4").unlink(missing_ok=True)
    (WORK / "exercise_base.mp4").unlink(missing_ok=True)
    cdir = OUT / "carousel" if final == OUT / "final_edit.mp4" else final.parent / "carousel"
    slides = render_carousel(load_json(OUT / "storyboard.json"), load_json(WORK / "cut_map.json"), cdir)
    if slides:
        print(f"wrote  {rel(cdir)}/ ({len(slides)} slides + carousel.json)")
    if (W, H) != (v["width"], v["height"]):
        die(f"final is {v['width']}x{v['height']}, expected {W}x{H}")


def measure_text_look(overlay: Path, props: dict, final: Path) -> dict:
    """Alfonso 2026-11-23 (answer 24): measure the Remotion layer itself (RGBA, before it is laid over the picture)
    at a frame inside every pop-up, CAM tag and the progress label: text pixels (alpha >= 50 %) must be white /
    neutral (R-G-B spread <= text_look.neutral_max_spread) and no dark pixel may be more opaque than
    text_look.box_alpha_max (a card / bar / panel; the look's own shadow peaks at 35 %). Log for qa_check.py:
    output/work/text_look_check.json."""
    import subprocess
    import numpy as np
    import text_look
    lk = text_look.look()
    pops = props.get("popups") or {}
    samples = [(f"bar {b['title']}", b["from"] + 1.0) for b in pops.get("bars") or []]
    samples += [(f"checklist {c['current']}", c["from"] + 1.0) for c in pops.get("checklists") or []]
    if pops.get("formTip"):
        samples.append(("form tip", pops["formTip"]["from"] + 1.5))
    samples += [(f"cam tag {e.get('label', '')}", e["from"] + 0.8) for e in props.get("events") or [] if e.get("kind") == "cam"]
    for i, lt in enumerate(props.get("lowerThirds") or []):
        samples.append((f"lower-third {lt['title']}", lt["from"] + 1.0))
    for i, c in enumerate(props.get("captions") or []):
        if i < 3:
            samples.append((f"caption page {i + 1}", (c["start"] + c["end"]) / 2))
    samples.append(("progress bar + label", min(float(props["duration"]) - 0.5, 20.0)))
    rows, ok = [], True
    for name, t in samples:
        t = min(max(0.0, float(t)), float(props["duration"]) - 0.05)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(overlay), "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
        if len(raw) < W * H * 4:
            rows.append({"what": name, "t": round(t, 2), "error": "no frame"})
            ok = False
            continue
        a = np.frombuffer(raw[: W * H * 4], np.uint8).reshape(H, W, 4)
        spread, box = text_look.tint_spread(a), text_look.box_pixels(a)
        drawn = int((a[..., 3] >= 128).sum())
        good = spread <= int(lk["neutral_max_spread"]) and box == 0
        ok &= good
        rows.append({"what": name, "t": round(t, 2), "text_px": drawn, "tint_spread": spread, "box_px": box, "ok": good})
    rep = {"final": rel(final), "ok": ok, "text_look": text_look.for_remotion(),
           "neutral_max_spread": lk["neutral_max_spread"], "box_alpha_max": lk["box_alpha_max"], "samples": rows}
    save_json(WORK / "text_look_check.json", rep)
    bad = [r for r in rows if not r.get("ok")]
    print(f"text look: {len(rows)} Remotion frames measured, "
          + ("all white / neutral, no box" if ok else f"{len(bad)} FAIL: {bad[:3]}"))
    return rep


def sfx_events(props: dict) -> list[tuple[float, str]]:
    """(time, kind) for every text move that gets a sound: hook card, layered exercise titles, pop-up cards."""
    ev = []
    t = props.get("title") or {}
    # the Fonzi intro card brings its own whoosh into beat 1 + impact on beat 1 (finish_fx.py)
    if t.get("text") and t.get("from") is not None and t.get("style") != "fonzi_intro":
        ev.append((float(t["from"]), "hook"))
    for e in props.get("exercise_titles") or []:
        ev.append((float(e["at"]), "title"))
    pops = props.get("popups") or {}
    for c in (pops.get("bars") or []) + (pops.get("checklists") or []) + ([pops["formTip"]] if pops.get("formTip") else []):
        at = c.get("from", c.get("at"))
        if at is not None:
            ev.append((float(at), "popup"))
    ev.sort()
    out, last = [], -9.0
    for at, kind in ev:          # two sounds closer than 0.25 s would smear: keep the first
        if at - last >= 0.25:
            out.append((at, kind))
            last = at
    return out


def add_sfx(final: Path, props: dict) -> int:
    """Alfonso (2026-11-19): a quiet whoosh / pop on every text move, mixed UNDER the existing sound (his voice
    or his song). Never replaces or shifts the audio; the length stays the same. config.yaml sfx:"""
    from common import ROOT, load_config, sfx_log_entry
    cfg = load_config().get("sfx") or {}
    if not cfg.get("enabled"):
        save_json(WORK / "sfx_log.json", {"volume_db": None, "events": [], "note": "config sfx.enabled is false"})
        return 0
    # Alfonso 2026-11-23: each text move -> a role (config sfx.events) -> the OpenFilm library sound (old wav fallback)
    roles = cfg.get("events") or {}
    ev = [(at, roles[kind]) for at, kind in sfx_events(props) if roles.get(kind)]
    ev = [(at, role) for at, role in ev if at < float(props["duration"]) - 0.05]
    entries = [sfx_log_entry(role, at, by="render_final") for at, role in ev]
    ev = [(at, ROOT / e["file"]) for (at, _), e in zip(ev, entries)]
    if not ev:
        save_json(WORK / "sfx_log.json", {"volume_db": None, "events": []})
        return 0
    files = sorted({f for _, f in ev})
    inputs = []
    for f in files:
        inputs += ["-i", str(f)]
    vol = float(cfg.get("volume_db", -16))
    fc, labels = [], []
    for k, (at, f) in enumerate(ev):
        idx = 1 + files.index(f)
        fc.append(f"[{idx}:a]volume={vol}dB,adelay={int(at * 1000)}|{int(at * 1000)}[s{k}]")
        labels.append(f"[s{k}]")
    # split each sfx input as many times as it is used
    uses = {}
    for k, (at, f) in enumerate(ev):
        uses.setdefault(1 + files.index(f), []).append(k)
    splits = []
    for idx, ks in uses.items():
        if len(ks) > 1:
            splits.append(f"[{idx}:a]asplit={len(ks)}" + "".join(f"[i{idx}_{j}]" for j in range(len(ks))))
            for j, k in enumerate(ks):
                fc[k] = fc[k].replace(f"[{idx}:a]", f"[i{idx}_{j}]", 1)
    graph = ";".join(splits + fc + ["[0:a]" + "".join(labels) + f"amix=inputs={len(ev) + 1}:duration=first:"
                                    "normalize=0:dropout_transition=0[a]"])
    tmp = final.with_name("final_sfx.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", final, *inputs, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp])
    if abs(probe(tmp)["duration"] - probe(final)["duration"]) > 0.05:
        die("sound effects changed the video length: not passing it on")
    tmp.replace(final)
    for e in entries:
        e["db"] = vol
    save_json(WORK / "sfx_log.json", {"volume_db": vol, "source": cfg.get("source", "library"), "events": entries})
    print(f"sound effects: {len(ev)} quiet hits under the audio ({vol} dB), log in output/work/sfx_log.json")
    return len(ev)


def mute_if_rule(final: Path) -> bool:
    """Alfonso (2026-11-15): always mute music baked into his uploads. If the cut has no speech, the final's
    sound is replaced by silence (same length, AAC). If he talks, his voice is kept (we cannot strip music
    from under it cleanly) and QA tells him. A song he picks from songs/ is never muted."""
    from common import load_config
    cfg = load_config().get("audio", {})
    if not cfg.get("mute_baked_music"):
        return False
    sb = load_json(OUT / "storyboard.json", default={})
    if sb.get("song"):
        return False
    words = load_json(WORK / "transcript.json", default={"words": []}).get("words", [])
    if len(words) >= 3:
        save_json(WORK / "audio_rule.json", {"muted": False, "reason": "he speaks in the video: voice kept"})
        return False
    tmp = final.with_name("final_muted.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", final, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
         "-movflags", "+faststart", tmp])
    tmp.replace(final)
    save_json(WORK / "audio_rule.json", {"muted": True, "reason": "no speech: baked-in music muted (Alfonso's rule)"})
    print("audio: muted (no speech; Alfonso's rule: always mute baked-in music)")
    return True


if __name__ == "__main__":
    main()
