#!/usr/bin/env python3
"""FINAL APPROVAL AGENT tool, step 1 of 2. Measures the final video. Edits nothing, posts nothing.

    python3 scripts/qa_check.py

Checks output/final_edit.mp4 with ffprobe (streams, size, fps, codecs, length), audio level,
on-screen text rules, duplicate-of-a-posted-video, and where the footage came from.
Saves 3 frames to output/qa/frame_1.jpg .. frame_3.jpg for the agent to look at,
and the measurements to output/qa/tech.json. Then run scripts/qa_verdict.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (FPS, H, INPUT, OUT, W, WORK, find_duplicate, load_json, probe, rel, resolve, run,  # noqa: E402
                    save_json, sha256)


def main():
    final = OUT / "final_edit.mp4"
    checks = []

    def add(name: str, ok: bool, detail: str, owner: str):
        checks.append({"check": name, "pass": bool(ok), "detail": detail, "owner": owner})

    if not final.exists():
        add("final video exists", False, "output/final_edit.mp4 is missing", "text_visuals")
        save_json(OUT / "qa" / "tech.json", {"checks": checks, "frames": []})
        print("FAIL: output/final_edit.mp4 is missing")
        sys.exit(0)

    sb = load_json(OUT / "storyboard.json", default={})
    job = load_json(OUT / "job.json", default={})
    props = load_json(WORK / "overlay_props.json", default={})
    cut = OUT / "cut_version.mp4"
    info = probe(final)
    v, a = info["video"], info["audio"]
    cut_info = probe(cut) if cut.exists() else None

    def owner(cut_ok: bool) -> str:  # a fault already present in the cut belongs to the Cuts Agent
        return "text_visuals" if cut_ok else "cuts"

    add("video stream present", v is not None, f"{v['codec']}" if v else "none", "text_visuals")
    add("audio stream present", a is not None, f"{a['codec']} {a['sample_rate']}Hz" if a else "none",
        owner(bool(cut_info and cut_info["audio"])))
    if v:
        cv = cut_info["video"] if cut_info else None
        add("1080x1920 vertical", (v["width"], v["height"]) == (W, H), f"{v['width']}x{v['height']}",
            owner(bool(cv and (cv["width"], cv["height"]) == (W, H))))
        add("30 fps", abs(v["fps"] - FPS) < 0.01, f"{v['fps']} fps", owner(bool(cv and abs(cv["fps"] - FPS) < 0.01)))
        add("H.264 video", v["codec"] == "h264", v["codec"], "text_visuals")
    if a:
        add("AAC audio", a["codec"] == "aac", a["codec"], "cuts")
        vol = run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                  check=False).stderr
        m = re.search(r"mean_volume: ([-\d.]+) dB", vol)
        mean = float(m.group(1)) if m else -91.0
        add("audio is not silent", mean > -50, f"mean {mean:.1f} dB", "cuts")
    lo, hi = sb.get("min_duration", 60), sb.get("max_duration", 90)
    add(f"length {lo}-{hi}s", lo <= info["duration"] <= hi, f"{info['duration']:.2f}s", "cuts")
    if cut_info:
        add("same length as the cut", abs(cut_info["duration"] - info["duration"]) < 0.2,
            f"cut {cut_info['duration']:.2f}s, final {info['duration']:.2f}s", "text_visuals")

    # on-screen text rules
    texts = []

    def walk(n):
        if isinstance(n, dict):
            for k, x in n.items():
                if k not in ("brand", "kind"):
                    walk(x)
        elif isinstance(n, list):
            for x in n:
                walk(x)
        elif isinstance(n, str):
            texts.append(n)

    walk(props)
    bad = [t for t in texts if "#" in t or re.search(r"[^\x20-\x7E]", t)]
    add("English only, no hashtags on screen", not bad and bool(props), f"{len(texts)} text items checked" if not bad else f"bad: {bad[:5]}",
        "text_visuals")
    need = {"title card": props.get("title"), "lower-thirds": props.get("lowerThirds"),
            "progress bar": props.get("progress"), "end card": props.get("endCard")}
    missing = [k for k, x in need.items() if not x]
    add("title card, lower-thirds, progress bar, end card present", not missing,
        "all present" if not missing else f"missing: {', '.join(missing)}", "text_visuals")
    n_words = sum(len(p["words"]) for p in props.get("captions", []))
    add("word-by-word captions present", n_words > 0, f"{n_words} caption words", "text_visuals")

    # duplicate + footage origin
    src = resolve(sb["source"]) if sb.get("source") else None
    src_sha = sha256(src) if src and src.exists() else None
    dup = find_duplicate(final, src_sha)
    add("not a duplicate of a posted video", dup is None,
        "no match in posted/ledger.json" if dup is None else f"{dup['match']}: posted {dup.get('posted_at')}", "director")
    in_input = bool(src and src.exists() and INPUT.resolve() in src.resolve().parents)
    add("footage comes from input/ only", in_input, sb.get("source", "unknown"), "director")
    confirmed = job.get("own_footage_confirmed", "unknown")
    add("Alfonso confirmed it is his own footage", confirmed == "yes",
        {"yes": "confirmed in the brief", "no": "brief says this is NOT his footage",
         "unknown": "not confirmed yet: ask Alfonso at approval"}.get(confirmed, confirmed), "director")

    # 3 frames: a lower-third moment, a punch-in, a caption mid-lift
    dur = info["duration"]
    body_end = (props.get("endCard") or {}).get("from", dur)
    picks = []
    lts = props.get("lowerThirds") or []
    if lts:
        picks.append(("lower-third on screen", lts[0]["from"] + 1.6))
    punches = [e for e in props.get("events", []) if e["kind"] == "punch_in"]
    if punches:
        p = punches[len(punches) // 2]
        picks.append(("punch-in (zoomed)", (p["from"] + p["to"]) / 2))
    caps = [c for c in props.get("captions", []) if c["start"] > dur * 0.35]
    if caps:
        c = caps[len(caps) // 2]
        picks.append(("captions on screen", min(c["words"][-1]["start"] + 0.15, c["end"] - 0.05)))
    for frac in (0.3, 0.55, 0.8):
        if len(picks) < 3:
            picks.append(("mid-video", body_end * frac))
    qdir = OUT / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, (what, t) in enumerate(picks[:3], 1):
        out = qdir / f"frame_{i}.jpg"
        t = max(0.0, min(t, dur - 0.1))
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", final, "-frames:v", "1", "-q:v", "2", out])
        frames.append({"file": rel(out), "time": round(t, 2), "shows": what})

    save_json(qdir / "tech.json", {"final": rel(final), "sha256": sha256(final), "source_sha256": src_sha,
                                   "probe": info, "checks": checks, "frames": frames})
    for c in checks:
        print(f"{'PASS' if c['pass'] else 'FAIL'}  {c['check']:<52} {c['detail']}")
    print("\nNow LOOK at these 3 frames, then run scripts/qa_verdict.py:")
    for f in frames:
        print(f"  {f['file']}  ({f['time']}s, {f['shows']})")


if __name__ == "__main__":
    main()
