#!/usr/bin/env python3
"""MULTICAM / B-ROLL AGENT tool, generator job: EXTEND a too-short clip with AI ("missing shots").
Only when Alfonso asked for it. It runs BEFORE the Storyboard Agent, because the plan needs the footage.

    python3 scripts/extend_footage.py input/<video> --to 60 --describe "<what he is doing, the room, the light>" --yes-spend

Sends Alfonso's own clip to the generator in config.yaml (Seedance 2.5, task "extension") and asks it to
continue the same take: same person, same room, same light, same locked-off camera. Repeats until the
footage reaches --to seconds (each call can continue from at most the last 30s).

Never touches input/. Writes:
  output/extended/<name>_extended.mp4   real clip + AI continuation, 1080x1920, 30fps, original audio
                                        then silence (no AI audio, ever)
  output/extended/extend.json           which seconds are real and which are AI-made, and the cost estimate
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, ROOT, W, WORK, die, probe, rel, resolve, run, save_json, sha256  # noqa: E402
from multicam_generate import env_key, fal_generate  # noqa: E402

PROMPT = """Continue @Video1 seamlessly from its last frame as one continuous take. This is the same moment carrying on: the same person, the same face, identity, clothing, body proportions and build, the same room, equipment, lighting, colour and shadows, and the same locked-off camera position, framing, lens and angle. Do not cut, do not move the camera, do not change the scene.

{describe}

Keep the movement real and natural at normal speed: controlled reps with a short pause between them. Do not add new people, text, captions, logos, graphics or music. Do not replace, redesign or hallucinate any part of the scene.
"""
PRICE_720P = 0.473   # USD per generated second, fal.ai list price for Seedance 2.5 at 720p (Nov 2026)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--to", type=float, default=60.0, help="total length wanted, seconds")
    ap.add_argument("--describe", required=True, help="what is happening in the clip, so the continuation matches")
    ap.add_argument("--yes-spend", action="store_true", help="Alfonso approved the cost")
    a = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    name = cfg["generator"]["provider"]
    if any(b in name.lower() for b in cfg["generator"].get("blocked", [])) or "omni" in name or "sora" in name:
        die(f"generator {name!r} is blocked")
    pcfg = cfg["providers"][name]
    if pcfg.get("api") != "fal" or "seedance" not in pcfg.get("model", ""):
        die(f"footage extension needs Seedance 2.5 as the generator in config.yaml (got {name})")
    src = resolve(a.video)
    if not src.exists() or (ROOT / "input").resolve() not in src.resolve().parents:
        die("the clip to extend must be Alfonso's own video in input/")
    if "#" in a.describe:
        die("--describe must be plain English with no hashtags")
    key = env_key(pcfg["key_env"])
    if not key:
        die(f"no API key: {pcfg['key_env']} is not set in .env. Nothing was generated.", code=3)

    info = probe(src)
    have = info["duration"]
    need = a.to - have
    if need <= 0:
        die(f"the clip is already {have:.1f}s; nothing to extend")
    calls, left = [], need
    while left > 0.5:
        n = int(min(30, max(4, round(left))))
        calls.append(n)
        left -= n
    cost = sum(calls) * PRICE_720P
    print(f"plan: {have:.1f}s real + {sum(calls)}s AI continuation in {len(calls)} call(s) {calls}, "
          f"about ${cost:.0f} at 720p (plus a little for the reference video)")
    if not a.yes_spend:
        die("Alfonso has to approve this cost first. Re-run with --yes-spend once he has.", code=3)

    edir, tmp = OUT / "extended", WORK / "extend_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    edir.mkdir(parents=True, exist_ok=True)

    def conform(inp: Path, out: Path, start: float = 0.0, dur: float | None = None):
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", inp]
        if dur:
            cmd += ["-t", f"{dur:.3f}"]
        run(cmd + ["-an", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
                   f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "16", out])

    parts = [tmp / "part_00.mp4"]
    conform(src, parts[0])                                   # the real footage, picture only for now
    timeline = [{"from": 0.0, "to": round(have, 3), "kind": "real", "source": rel(src)}]
    total = have
    for i, n in enumerate(calls, 1):
        # reference = the last (up to) 30s of what we have so far, so the continuation picks up from the end
        joined = tmp / f"so_far_{i}.mp4"
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", joined])
        ref = tmp / f"ref_{i}.mp4"
        ref_len = min(total, 30.0)
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{total - ref_len:.3f}", "-i", joined, "-an",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", ref])
        raw = tmp / f"raw_{i}.mp4"
        print(f"call {i}/{len(calls)}: continuing from the last {ref_len:.1f}s, asking for {n}s ...", flush=True)
        ext_cfg = {**pcfg, "task": "extension", "min_clip_seconds": n, "max_clip_seconds": n}
        fal_generate(ext_cfg, key, ref, PROMPT.format(describe=a.describe.strip()), n, raw)
        got = probe(raw)["duration"]
        # some providers return reference + continuation, some only the continuation: keep only the new part
        new_start = ref_len if got >= ref_len + n * 0.8 else 0.0
        new_len = got - new_start
        if new_len < 3.0:
            die(f"call {i}: the generator returned only {new_len:.1f}s of new footage. Stopped; nothing was kept.")
        part = tmp / f"part_{i:02d}.mp4"
        conform(raw, part, new_start, new_len)
        parts.append(part)
        timeline.append({"from": round(total, 3), "to": round(total + new_len, 3), "kind": "ai",
                         "generator": name, "returned_seconds": round(got, 3)})
        total += new_len
        print(f"   got {new_len:.1f}s of new footage (total {total:.1f}s)", flush=True)

    (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    picture = tmp / "picture.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", picture])
    out = edir / f"{src.stem}_extended.mp4"
    # audio: Alfonso's own sound for the real part, then silence. No AI audio.
    run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", src, "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total:.3f}[a]",
         "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out])
    shutil.rmtree(tmp, ignore_errors=True)
    real_s = timeline[0]["to"]
    save_json(edir / "extend.json", {
        "extended": rel(out), "base": rel(src), "base_sha256": sha256(src), "generator": name,
        "describe": a.describe, "timeline": timeline, "real_seconds": round(real_s, 3),
        "ai_seconds": round(total - real_s, 3), "estimated_cost_usd": round(cost, 2)})
    o = probe(out)
    print(f"wrote  {rel(out)}  {o['video']['width']}x{o['video']['height']} {o['video']['fps']}fps  {o['duration']:.2f}s "
          f"({real_s:.1f}s real + {total - real_s:.1f}s AI-made by {name})")


if __name__ == "__main__":
    main()
