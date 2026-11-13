#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Renders the animated graphics with Remotion and lays them over the cut.

    python3 scripts/render_final.py            # -> output/final_edit.mp4 (+ output/carousel/ if 2+ exercises)
    python3 scripts/render_final.py --preview 12.5 31   # just stills at those seconds, for a quick look

The cut itself is never changed: Remotion renders a transparent graphics layer and ffmpeg
composites it on top of output/cut_version.mp4. Audio is copied through untouched.
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
from common import FPS, H, OUT, REMOTION, W, WORK, brand, die, load_json, probe, rel, run, save_json  # noqa: E402


def browser_args() -> list[str]:
    exe = os.environ.get("REMOTION_BROWSER")
    if not exe:
        found = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"))
        exe = found[-1] if found else None
    return [f"--browser-executable={exe}"] if exe else []  # otherwise Remotion fetches its own


def check_text(props: dict):
    """English only, no hashtags: refuse to render anything else."""
    bad = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and not path.endswith(("color", "Color", "kind")):
            if "#" in node or re.search(r"[^\x20-\x7E]", node):
                bad.append(f"{path}: {node!r}")

    walk({k: v for k, v in props.items() if k != "brand"}, "props")
    if bad:
        die("on-screen text must be English with no hashtags:\n  " + "\n  ".join(bad))


def remotion(args: list[str]):
    if not (REMOTION / "node_modules").exists():
        die("Remotion is not installed. Run: bash scripts/setup.sh")
    run(["npx", "remotion", *args, *browser_args(), "--log=error"], cwd=REMOTION)


def render_carousel(sb: dict, cm: dict):
    items = sb.get("carousel") or []
    if len(items) < 2:
        return None
    b = brand()
    cdir, pub = OUT / "carousel", WORK / "public"
    shutil.rmtree(cdir, ignore_errors=True)
    shutil.rmtree(pub, ignore_errors=True)
    cdir.mkdir(parents=True)
    shutil.copytree(REMOTION / "public", pub)
    cut = OUT / "cut_version.mp4"

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
        save_json(pfile, {"brand": {k: b[k] for k in ("name", "handle", "color", "textColor", "darkColor")}, "slide": slide})
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


def main():
    cut = OUT / "cut_version.mp4"
    if not cut.exists():
        die("output/cut_version.mp4 is missing: the Cuts Agent has to run first")
    props_path = WORK / "overlay_props.json"
    props = load_json(props_path)
    check_text(props)
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

    overlay = WORK / "overlay.mov"
    print(f"rendering {props['duration']:.1f}s of motion graphics with Remotion (a few minutes) ...")
    remotion(["render", "src/index.ts", "Overlay", str(overlay), f"--props={props_path}",
              "--codec=prores", "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png",
              f"--concurrency={os.cpu_count() or 2}"])
    final = OUT / "final_edit.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-i", overlay, "-filter_complex",
         f"[0:v][1:v]overlay=format=auto,fps={FPS},format=yuv420p[v]", "-map", "[v]", "-map", "0:a?",
         "-t", f"{info['duration']:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart", final])
    overlay.unlink(missing_ok=True)
    out = probe(final)
    v = out["video"]
    print(f"wrote  output/final_edit.mp4  {v['width']}x{v['height']} {v['fps']}fps {v['codec']}+"
          f"{out['audio']['codec'] if out['audio'] else 'NO AUDIO'}  {out['duration']:.2f}s")

    slides = render_carousel(load_json(OUT / "storyboard.json"), load_json(WORK / "cut_map.json"))
    if slides:
        print(f"wrote  output/carousel/ ({len(slides)} slides + carousel.json)")
    if (W, H) != (v["width"], v["height"]):
        die(f"final is {v['width']}x{v['height']}, expected {W}x{H}")


if __name__ == "__main__":
    main()
