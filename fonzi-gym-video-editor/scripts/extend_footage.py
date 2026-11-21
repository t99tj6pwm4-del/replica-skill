#!/usr/bin/env python3
"""MULTICAM / B-ROLL AGENT tool, generator job: EXTEND a too-short clip ("missing shots").
Only when Alfonso asked for it. It runs BEFORE the Storyboard Agent, because the plan needs the footage.

    python3 scripts/extend_footage.py input/<video> --to 60                          # free-local, $0 (default)
    python3 scripts/extend_footage.py input/<video> --to 60 --provider ltx-cheap \\
        --describe "<what he is doing, the room, the light>" --yes-spend             # AI, about $0.02/s
    python3 scripts/extend_footage.py input/<video> --to 60 --provider seedance-2.5 \\
        --describe "..." --yes-spend                                                  # AI, about $0.47/s

free-local ($0, no AI): replays of the real reps at different speeds and virtual camera framings.
ltx-cheap / seedance-2.5 (AI): the generator continues the same take: same person, room, light, camera.

Never touches input/. Never Sora; no Omni here (Omni is only for Flow multicam reframes). Never adds AI audio. Writes:
  output/extended/<name>_extended.mp4   1080x1920, 30fps, original audio then silence
  output/extended/extend.json           which seconds are real, replayed or AI-made, and the cost
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, ROOT, W, WORK, check_generator, die, probe, rel, resolve, run, save_json, sha256  # noqa: E402
from multicam_generate import env_key, fal_generate  # noqa: E402

PROMPT = """Continue the video seamlessly from its last frame as one continuous take. This is the same moment carrying on: the same person, the same face, identity, clothing, body proportions and build, the same room, equipment, lighting, colour and shadows, and the same locked-off camera position, framing, lens and angle. Do not cut, do not move the camera, do not change the scene.

{describe}

Keep the movement real and natural at normal speed: controlled reps with a short pause between them. Do not add new people, text, captions, logos, graphics or music. Do not replace, redesign or hallucinate any part of the scene.
"""

# free-local replay plan: (speed, zoom, focus_x, focus_y, label). Real footage only, varied so it does not
# read as a plain loop. Zoom 1.0 = the original framing.
REPLAYS = [
    (0.5, 1.15, 0.45, 0.40, "slow-mo 0.5x, tighter"),
    (1.0, 1.35, 0.35, 0.45, "1x, close on the working arm"),
    (0.75, 1.0, 0.5, 0.5, "0.75x, original framing"),
    (1.0, 1.25, 0.6, 0.30, "1x, close on face and shoulders"),
    (0.6, 1.10, 0.5, 0.55, "slow-mo 0.6x, slight push-in"),
    (1.0, 1.0, 0.5, 0.5, "1x, original framing"),
]


def conform(inp: Path, out: Path, start: float = 0.0, dur: float | None = None, speed: float = 1.0,
            zoom: float = 1.0, fx: float = 0.5, fy: float = 0.5):
    vf = [f"setpts=(PTS-STARTPTS)/{speed}"]
    if speed < 1:
        vf.append(f"minterpolate=fps={FPS}:mi_mode=blend")
    vf.append(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
    if zoom > 1.001:
        vf.append(f"crop=iw/{zoom}:ih/{zoom}:(iw-iw/{zoom})*{fx}:(ih-ih/{zoom})*{fy},scale={W}:{H}:flags=lanczos")
    vf += ["setsar=1", f"fps={FPS}", "format=yuv420p"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", inp]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    run(cmd + ["-an", "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", "16", out])


def ltx_generate(pcfg: dict, key: str, ref: Path, prompt: str, ref_len: float, new_len: float, out: Path):
    """LTX-Video extend: the output holds the reference frames followed by the continuation."""
    import os
    import fal_client
    import requests
    os.environ["FAL_KEY"] = key
    url = fal_client.upload_file(str(ref))
    frames = min(1441, int(round((ref_len + new_len) * 24)) + 1)
    result = fal_client.subscribe(pcfg["model"], arguments={
        "prompt": prompt, "video": {"video_url": url, "start_frame_num": 0, "strength": 1.0},
        "num_frames": frames, "frame_rate": 24, "resolution": pcfg.get("resolution", "720p"),
        "aspect_ratio": pcfg.get("aspect_ratio", "9:16"), "expand_prompt": False})
    video = (result.get("video") or {}).get("url")
    if not video:
        die(f"the generator returned no video: {str(result)[:300]}")
    with requests.get(video, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--to", type=float, default=60.0, help="total length wanted, seconds")
    ap.add_argument("--provider", help="free-local (default, $0), ltx-cheap, or seedance-2.5")
    ap.add_argument("--describe", default="", help="AI only: what is happening in the clip, so the continuation matches")
    ap.add_argument("--yes-spend", action="store_true", help="Alfonso approved the cost (AI only)")
    a = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    name = a.provider or cfg["generator"].get("extend_provider", "free-local")
    if name == "local-reframe":
        name = "free-local"
    if name not in cfg["providers"]:
        die(f"unknown generator {name!r}; config.yaml has: {', '.join(cfg['providers'])}")
    pcfg = cfg["providers"][name]
    check_generator(name, pcfg, cfg, "extend")
    local = pcfg.get("api") == "local"
    if not local and not any(k in pcfg.get("model", "") for k in ("seedance", "ltx")):
        die(f"footage extension supports free-local, ltx-cheap and seedance-2.5 (got {name})")
    src = resolve(a.video)
    if not src.exists() or (ROOT / "input").resolve() not in src.resolve().parents:
        die("the clip to extend must be Alfonso's own video in input/")
    if "#" in a.describe:
        die("--describe must be plain English with no hashtags")

    have = probe(src)["duration"]
    need = a.to - have
    if need <= 0:
        die(f"the clip is already {have:.1f}s; nothing to extend")

    edir, tmp = OUT / "extended", WORK / "extend_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    edir.mkdir(parents=True, exist_ok=True)
    parts = [tmp / "part_00.mp4"]
    conform(src, parts[0])
    timeline = [{"from": 0.0, "to": round(have, 3), "kind": "real", "what": "original clip"}]
    total, cost = have, 0.0

    if local:
        i = 0
        while total < a.to - 0.3:
            speed, zoom, fx, fy, label = REPLAYS[i % len(REPLAYS)]
            length = have / speed
            if total + length > a.to + 0.5:   # last replay: only as much as needed
                length = a.to - total
            part = tmp / f"part_{i + 1:02d}.mp4"
            conform(src, part, 0.0, length * speed, speed, zoom, fx, fy)
            got = probe(part)["duration"]
            parts.append(part)
            timeline.append({"from": round(total, 3), "to": round(total + got, 3), "kind": "replay", "what": label})
            total += got
            i += 1
        print(f"free-local: {have:.1f}s real + {total - have:.1f}s of replays of the same real reps, $0")
    else:
        if not a.describe:
            die("--describe is required for an AI extension (what the person is doing, the room, the light)")
        key = env_key(pcfg["key_env"])
        if not key:
            die(f"no API key: {pcfg['key_env']} is not set in .env. Nothing was generated.", code=3)
        rate = float(pcfg.get("cost_per_second_usd", 0.473))
        if "ltx" in pcfg["model"]:
            calls = [need]
            cost = (min(have, 30) + need) * rate
        else:
            calls, left = [], need
            while left > 0.5:
                n = int(min(30, max(4, round(left))))
                calls.append(n)
                left -= n
            cost = sum(calls) * rate
        print(f"plan: {have:.1f}s real + {sum(calls):.0f}s AI by {name} in {len(calls)} call(s), about ${cost:.2f}")
        if not a.yes_spend:
            die("Alfonso has to approve this cost first. Re-run with --yes-spend once he has.", code=3)
        for i, n in enumerate(calls, 1):
            joined = tmp / f"so_far_{i}.mp4"
            (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
            run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", joined])
            ref, raw = tmp / f"ref_{i}.mp4", tmp / f"raw_{i}.mp4"
            ref_len = min(total, 30.0)
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{total - ref_len:.3f}", "-i", joined, "-an",
                 "-c:v", "libx264", "-preset", "fast", "-crf", "18", ref])
            prompt = PROMPT.format(describe=a.describe.strip())
            print(f"call {i}/{len(calls)}: continuing from the last {ref_len:.1f}s, asking for {n:.0f}s ...", flush=True)
            if "ltx" in pcfg["model"]:
                ltx_generate(pcfg, key, ref, prompt, ref_len, n, raw)
                got = probe(raw)["duration"]
                new_start = ref_len if got > ref_len + 1.0 else 0.0
            else:
                fal_generate({**pcfg, "task": "extension", "min_clip_seconds": n, "max_clip_seconds": n},
                             key, ref, prompt.replace("Continue the video", "Continue @Video1"), n, raw)
                got = probe(raw)["duration"]
                new_start = ref_len if got >= ref_len + n * 0.8 else 0.0
            new_len = got - new_start
            if new_len < 3.0:
                die(f"call {i}: the generator returned only {new_len:.1f}s of new footage. Stopped; nothing was kept.")
            part = tmp / f"part_{i:02d}.mp4"
            conform(raw, part, new_start, new_len)
            parts.append(part)
            timeline.append({"from": round(total, 3), "to": round(total + new_len, 3), "kind": "ai",
                             "what": f"AI continuation by {name}"})
            total += new_len

    (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    picture = tmp / "picture.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", picture])
    total = probe(picture)["duration"]
    out = edir / f"{src.stem}_extended.mp4"
    # audio: Alfonso's own sound for the real part, then silence. No AI audio.
    run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", src, "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total:.3f}[a]",
         "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out])
    shutil.rmtree(tmp, ignore_errors=True)
    ai_s = sum(t["to"] - t["from"] for t in timeline if t["kind"] == "ai")
    save_json(edir / "extend.json", {
        "extended": rel(out), "base": rel(src), "base_sha256": sha256(src), "generator": name, "describe": a.describe,
        "timeline": timeline, "real_seconds": round(have, 3), "replay_seconds": round(total - have - ai_s, 3),
        "ai_seconds": round(ai_s, 3), "estimated_cost_usd": round(cost, 2)})
    o = probe(out)
    print(f"wrote  {rel(out)}  {o['video']['width']}x{o['video']['height']} {o['video']['fps']}fps  {o['duration']:.2f}s")
    for t in timeline:
        print(f"       {t['from']:6.2f}-{t['to']:6.2f}s  {t['kind']:<7} {t['what']}")


if __name__ == "__main__":
    main()
