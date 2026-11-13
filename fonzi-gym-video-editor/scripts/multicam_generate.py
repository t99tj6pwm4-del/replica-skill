#!/usr/bin/env python3
"""MULTICAM / B-ROLL AGENT tool, job (b): GENERATOR.

    python3 scripts/multicam_generate.py                      # generator from config.yaml (default Seedance 2.5)
    python3 scripts/multicam_generate.py --provider kling-multicam
    python3 scripts/multicam_generate.py --stand-in           # TEST ONLY: no AI, re-frames your own pixels

Sends output/multicam_prompt.txt + your own clip to the generator, gets the new camera angles back,
and cuts them in OVER the A-roll at the planned timestamps. The original audio is the truth: it is
copied through bit for bit and generated clips are forced to the exact slot length.

Writes:
  output/multicam/<id>_<angle>.mp4   each generated angle / B-roll clip
  output/multicam_version.mp4        the cut with the angles cut in (same length, same audio)
  output/work/multicam_map.json      what was inserted where, and by which generator

    python3 scripts/multicam_generate.py --provider google-flow      # (default) Google Flow, free:
        1st run: makes the hand-off pack output/flow_pack/ and FREEZES multicam_prompt.txt
        2nd run, after Alfonso's Flow clips are in output/flow_pack/returned/: cuts them in

Never Sora. Omni only inside Google Flow, only for multicam reframes. API keys come from .env only.
"""
from __future__ import annotations

import argparse
import hashlib
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, ROOT, W, WORK, check_generator, die, load_json, probe, rel, run, save_json  # noqa: E402
from multicam_prompt import ANGLES, HEAD  # noqa: E402

# stand-in "angles": perspective re-framing of the same pixels (source corner points as fractions of w,h)
STAND_IN = {
    "three-quarter": (0.16, 0.06, 0.94, 0.16, 0.16, 0.94, 0.94, 0.84),
    "profile": (0.22, 0.04, 0.92, 0.20, 0.22, 0.96, 0.92, 0.80),
    "low": (0.17, 0.03, 0.83, 0.03, 0.02, 0.90, 0.98, 0.90),
    "high": (0.04, 0.06, 0.96, 0.06, 0.20, 0.86, 0.80, 0.86),
}


def env_key(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if line.strip().startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def audio_md5(path: Path) -> str:
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "2", "-ar", "48000", "-f", "s16le", "-"],
                       capture_output=True)
    return hashlib.md5(p.stdout).hexdigest()


def fal_generate(pcfg: dict, key: str, clip: Path, prompt: str, seconds: float, out: Path):
    try:
        import fal_client
    except ImportError:
        die("fal-client is not installed. Run: pip install fal-client")
    import requests
    os.environ["FAL_KEY"] = key
    url = fal_client.upload_file(str(clip))
    args = {"prompt": prompt, "video_urls": [url], "generate_audio": False,
            "aspect_ratio": pcfg.get("aspect_ratio", "9:16")}
    for k in ("task", "resolution"):
        if pcfg.get(k):
            args[k] = pcfg[k]
    if pcfg.get("task") != "editing":            # editing keeps the reference's own duration
        args["duration"] = str(int(round(min(max(seconds, pcfg.get("min_clip_seconds", 4)), pcfg.get("max_clip_seconds", 30)))))
    result = fal_client.subscribe(pcfg["model"], arguments=args)
    video = (result.get("video") or {}).get("url")
    if not video:
        die(f"the generator returned no video: {str(result)[:300]}")
    with requests.get(video, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)


def stand_in_generate(clip: Path, angle: str, out: Path):
    c = STAND_IN.get(angle, STAND_IN["three-quarter"])
    pts = ":".join(f"{'W' if i % 2 == 0 else 'H'}*{v}" for i, v in enumerate(c))
    run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-an", "-vf",
         f"perspective={pts}:sense=source:interpolation=cubic,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6",
         "-c:v", "libx264", "-preset", "fast", "-crf", "14", out])


FLOW_STEPS = """# Google Flow hand-off: {n} clips to make (free tier)

Open https://flow.google.com on your phone or computer, signed in with your Google account. Free tier:
50 credits a day, they do not roll over. Never pick Veo 3.1 Quality (100 credits). If Flow says it is busy
(peak hours), wait and try again later. Do not buy a plan without telling the Director first.

Make ONE clip per shot below, in this order. For each shot:
1. Upload the reference clip named for that shot (it is {maxs:g}s or less, 9:16, your real footage).
2. Model: {reframe} (reframe of the uploaded video). Vertical 9:16, 720p, 8 seconds.
3. Paste the prompt for that shot EXACTLY as written below. Do not change a word. Every shot is a HARD CUT
   from the library: same person, face, clothes, tattoos, gym, equipment and lighting. If the reframe
   cannot show that shot (e.g. it needs a camera position Omni cannot invent), use Veo 3.1 Lite from the
   start frame instead, never Veo 3.1 Quality.
4. Continuity: if Flow offers it, use the shot's start frame (`<id>_start.jpg`) as the first frame / scene
   anchor, so the new angle cuts in cleanly on the real moment.
5. Download the result and name it `<id>.mp4` (e.g. `angle_1.mp4`), then send all {n} files back to Claude
   (upload them in the chat, or drop them in output/flow_pack/returned/).

{shots}
B-roll shots (if any) use {broll} from the still `<id>_start.jpg` instead: picture only, 6 or 8 seconds.
Their sound is thrown away; your original audio always stays.
"""


def flow_handoff(cut: Path, plan: dict, pcfg: dict, shots: list) -> dict:
    """Google Flow has no API: build the pack Alfonso runs in Flow, or pick up the clips he sent back."""
    pack, ret = OUT / "flow_pack", OUT / "flow_pack" / "returned"
    ret.mkdir(parents=True, exist_ok=True)
    found, missing = {}, []
    for s in shots:
        hits = sorted(p for p in ret.glob(f"{s['id']}*") if p.suffix.lower() in (".mp4", ".mov", ".webm"))
        if hits:
            found[s["id"]] = hits[0]
        else:
            missing.append(s)
    if not missing:
        print(f"found all {len(found)} Flow clips in output/flow_pack/returned/")
        return found
    maxs = float(pcfg.get("max_clip_seconds", 8))
    blocks = []
    for s in shots:
        length = min(maxs, plan["duration"] - s["from"])
        ref = pack / f"{s['id']}_reference.mp4"
        if not ref.exists():
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['from']:.3f}", "-t", f"{length:.3f}", "-i", cut,
                 "-vf", "scale=720:1280,setsar=1", "-c:v", "libx264", "-crf", "17", "-c:a", "aac", "-b:a", "128k", ref])
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['from']:.3f}", "-i", cut, "-frames:v", "1", "-q:v", "2",
                 pack / f"{s['id']}_start.jpg"])
        prompt = s.get("flow_prompt") or "(see output/broll_prompt.txt)"
        blocks.append(f"## {s['id']}  (shot {s.get('shot', '-')}: {s.get('shot_text', s['angle'])}{', B-roll, ' + str(s.get('model')) if s['kind'] == 'broll' else ''})\n"
                      f"- Reference clip: `{ref.name}`   Start frame: `{s['id']}_start.jpg`\n"
                      f"- Cuts in at {s['from']:.2f}s, back to your original camera at {s['to']:.2f}s\n"
                      f"- Prompt:\n\n    {prompt}\n"
                      + ("- STILL NEEDED\n" if s in missing else "- received\n"))
    (pack / "FLOW_STEPS.md").write_text(FLOW_STEPS.format(n=len(shots), maxs=maxs, reframe=pcfg.get("reframe_model"),
                                                          broll=pcfg.get("broll_model"), shots="\n".join(blocks)))
    print(f"Google Flow hand-off pack ready: output/flow_pack/ ({len(missing)} of {len(shots)} clips still needed)")
    for s in missing:
        print(f"   {s['id']:<8} {s['angle']:<11} reference {s['id']}_reference.mp4   cut in at {s['from']:.2f}s")
    print("multicam_prompt.txt is now FROZEN. Steps for Alfonso: output/flow_pack/FLOW_STEPS.md")
    print("When the clips are in output/flow_pack/returned/<id>.mp4, run this script again to cut them in.")
    sys.exit(4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider")
    ap.add_argument("--stand-in", action="store_true", help="TEST ONLY: no AI generator, re-frame the original pixels")
    ap.add_argument("--yes-spend", action="store_true", help="allow more generated seconds than the config guard")
    a = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    gen = cfg["generator"]
    name = "free-local" if a.stand_in else (a.provider or gen["provider"])
    if name not in cfg["providers"]:
        die(f"unknown generator {name!r}; config.yaml has: {', '.join(cfg['providers'])}")
    pcfg = cfg["providers"][name]
    check_generator(name, pcfg, cfg, "multicam")
    if "/extend" in str(pcfg.get("model", "")):
        die(f"{name} can only extend a clip; it cannot re-film a camera angle. Use free-local or seedance-2.5 for multicam.")

    cut = OUT / "cut_version.mp4"
    plan = load_json(WORK / "multicam_plan.json")
    prompt_file = OUT / "multicam_prompt.txt"
    if not cut.exists() or not prompt_file.exists():
        die("need output/cut_version.mp4 and output/multicam_prompt.txt first (run scripts/multicam_prompt.py)")
    frozen = prompt_file.read_text()
    info = probe(cut)
    dur = info["duration"]
    if abs(dur - plan["duration"]) > 0.1:
        die("multicam_prompt.txt was written for a different cut. Re-run scripts/multicam_prompt.py")
    shots = plan["spans"] + plan.get("broll", [])
    if not shots:
        die("the plan has no shots to generate")
    if plan.get("provider") != name and not (name == "free-local" and plan.get("provider") == "local-reframe"):
        die(f"multicam_prompt.txt was planned for {plan.get('provider')}, not {name}. Re-run multicam_prompt.py "
            f"--provider={name} (only before generation starts).")
    if hashlib.sha256(frozen.encode()).hexdigest() != plan.get("frozen_sha256"):
        die("output/multicam_prompt.txt was changed after it was frozen. Restore it or re-plan with --unfreeze.")
    if not plan.get("generation_started"):
        import shot_library
        shot_library.log_shots(load_json(OUT / "job.json", default={}).get("video", plan.get("source", "")),
                               [s for s in plan["spans"] if s.get("shot")])
    plan["generation_started"] = True
    save_json(WORK / "multicam_plan.json", plan)
    returned = {}
    if pcfg["api"] == "manual-web":
        returned = flow_handoff(cut, plan, pcfg, shots)
    simulated = pcfg["api"] == "local"
    key = None
    if not simulated and not returned:
        if not pcfg.get("model"):
            die(f"config.yaml providers.{name}.model is empty. Set the model id for {name} first.")
        key = env_key(pcfg["key_env"])
        if not key:
            die(f"no API key: {pcfg['key_env']} is not set in .env, so {name} cannot generate anything.\n"
                f"Nothing was generated. Add {pcfg['key_env']}=... to .env (your own key) and run this again.", code=3)
        lo, hi = float(pcfg.get("min_clip_seconds", 3)), float(pcfg.get("max_clip_seconds", 10))
        for s in shots:
            if not lo - 0.05 <= s["to"] - s["from"] <= hi + 0.05:
                die(f"{s['id']} is {s['to'] - s['from']:.1f}s but {name} takes {lo:g}-{hi:g}s clips. "
                    "Change multicam.min/max_shot_seconds in config.yaml and re-run scripts/multicam_prompt.py")
        total = sum(s["to"] - s["from"] for s in shots)
        if total > float(gen.get("max_generated_seconds", 24)) and not a.yes_spend:
            die(f"this would generate {total:.1f}s of video, over the {gen['max_generated_seconds']}s guard in config.yaml. "
                "Ask Alfonso, then re-run with --yes-spend.", code=3)

    mdir, tmp = OUT / "multicam", WORK / "multicam_tmp"
    shutil.rmtree(mdir, ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)
    mdir.mkdir(parents=True)
    tmp.mkdir(parents=True)

    # whole-take mode: a short video goes to the generator once, with the frozen prompt verbatim
    whole = (not simulated and not returned and not plan.get("broll") and dur <= float(pcfg.get("max_clip_seconds", 10))
             and dur <= float(gen.get("max_generated_seconds", 24)))
    whole_raw = tmp / "whole_raw.mp4"
    if whole:
        ref = tmp / "whole_ref.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-an", "-c:v", "libx264", "-crf", "16", ref])
        print(f"sending the whole {dur:.1f}s take + multicam_prompt.txt to {name} ...")
        fal_generate(pcfg, key, ref, frozen, dur, whole_raw)

    inserts = []
    for s in shots:
        length = round(s["to"] - s["from"], 3)
        ref, raw = tmp / f"{s['id']}_ref.mp4", tmp / f"{s['id']}_raw.mp4"
        clip = mdir / f"{s['id']}_{s['angle']}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['from']:.3f}", "-t", f"{length:.3f}", "-i", cut, "-an",
             "-c:v", "libx264", "-preset", "fast", "-crf", "16", ref])       # 3-10s reference clip, picture only
        if returned:
            raw, offset = returned[s["id"]], 0.0
        elif simulated:
            stand_in_generate(ref, s["angle"], raw)
            offset = 0.0
        elif whole:
            raw, offset = whole_raw, s["from"]
        else:
            if s["kind"] == "broll":
                text = next(t for t in (OUT / "broll_prompt.txt").read_text().split("--- B-roll ") if t.startswith(s["id"].split("_")[1]))
                prompt = text.split("---\n", 1)[1]
            else:   # the frozen rules + this shot's own line of the timeline
                prompt = (HEAD.split("Follow this timeline:")[0]
                          + f"This clip is the section [{s['from']:.2f}s] to [{s['to']:.2f}s] of the take. "
                          f"Re-film all of it from a {ANGLES[s['angle']]}. Same moment, same motion, same lip sync.\n\n"
                          f"Output: vertical 9:16, 30 fps, exactly {length:.2f}s.\n")
            print(f"sending {s['id']} ({length:.1f}s reference clip, {s['angle']}) to {name} ...")
            fal_generate(pcfg, key, ref, prompt, length, raw)
            offset = 0.0
        got = probe(raw)["duration"] - offset
        if got < length - 0.2:
            die(f"{s['id']}: the generator returned {got:.2f}s for a {length:.2f}s slot. Timing would drift "
                "from the audio, so it was not cut in. Regenerate this shot.")
        # conform: exact slot length, 1080x1920, 30fps, no audio (the original audio stays the truth)
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{offset:.3f}", "-i", raw, "-an", "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p",
             "-t", f"{length:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "16", clip])
        rv = probe(raw)["video"] or {}
        inserts.append({**s, "clip": rel(clip), "provider": name, "simulated": simulated,
                        "returned_seconds": round(got, 3), "returned_width": rv.get("width"),
                        "returned_height": rv.get("height"),
                        "model": (s.get("model") or pcfg.get("reframe_model")) if returned else pcfg.get("model")})

    # cut the angles in OVER the A-roll; audio is copied, never re-encoded
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", cut]
    fc, last = [], "0:v"
    for i, ins in enumerate(inserts, 1):
        cmd += ["-i", ROOT / ins["clip"]]
        fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{ins['from']:.3f}/TB[c{i}]")
        fc.append(f"[{last}][c{i}]overlay=enable='between(t,{ins['from']:.3f},{ins['to'] - 0.001:.3f})':eof_action=pass[v{i}]")
        last = f"v{i}"
    out = OUT / "multicam_version.mp4"
    cmd += ["-filter_complex", ";".join(fc) + f";[{last}]fps={FPS},format=yuv420p[v]", "-map", "[v]", "-map", "0:a",
            "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high",
            "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart", out]
    run(cmd)
    shutil.rmtree(tmp, ignore_errors=True)

    o = probe(out)
    same_audio = audio_md5(out) == audio_md5(cut)
    save_json(WORK / "multicam_map.json", {
        "base": "output/cut_version.mp4", "output": rel(out), "provider": name, "simulated": simulated,
        "mode": "whole take" if whole else "per shot", "cuts": plan["cuts"], "inserts": inserts,
        "audio_identical_to_cut": same_audio, "duration": round(o["duration"], 3)})
    print(f"wrote  output/multicam_version.mp4  {o['video']['width']}x{o['video']['height']} {o['video']['fps']}fps  "
          f"{o['duration']:.2f}s  ({len(inserts)} shots cut in, generator: {name})")
    for ins in inserts:
        print(f"       {ins['from']:6.2f}-{ins['to']:6.2f}s  {ins['kind']:<8} {ins['angle']:<14} {ins['clip']}")
    print(f"       original audio untouched: {'yes' if same_audio else 'NO'}")
    if simulated:
        print("NOTE   free-local: these angles are virtual cameras cropped from your real pixels ($0), not AI re-filmed angles.")
    if not same_audio or abs(o["duration"] - dur) > 0.05:
        die("the multicam version does not match the cut's audio/length. Do not pass it on.")


if __name__ == "__main__":
    main()
