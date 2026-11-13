#!/usr/bin/env python3
"""MULTICAM / B-ROLL AGENT tool, job (a): PROMPT-MAKER ONLY. It never generates video.

    python3 scripts/multicam_prompt.py

Transcribes the cut word by word with Whisper, finds the speech beats (phrase starts / breaths),
picks 4 cut timestamps that never land mid-word, and writes ONE frozen multicam prompt:
same face, same room, same voice, same lip sync, same timing. ONLY the camera angle changes.

Writes:
  output/multicam_prompt.txt        the one frozen prompt
  output/broll_prompt.txt           one prompt per B-roll request (only if Alfonso asked for B-roll)
  output/work/multicam_plan.json    the timestamps the generator and QA work from
  output/work/transcript.json       word-level transcript (re-used by the Text/Visuals Agent)
"""
from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, OUT, ROOT, WORK, die, load_json, probe, save_json  # noqa: E402

ANGLES = {
    "profile": "side profile angle, camera at 90 degrees to the person, eye level",
    "three-quarter": "three-quarter angle, camera about 45 degrees to the person's side, eye level",
    "low": "low angle, camera near the floor looking up at the person",
    "high": "high angle, camera above head height looking down at the person",
}

HEAD = """Use the uploaded video as the only source. Video timing must be exactly the same as the original video.

Preserve the person's face, identity, expression, clothing, body proportions, movement and lip sync exactly as in the original footage. Preserve the room, lighting, equipment, background and overall environment. Preserve the original voice and audio exactly. Do not add music, sound effects or new speech. Do not replace, redesign or hallucinate any part of the scene. Do not add text, captions, logos or graphics.

The ONLY change is the camera angle. Hard cuts only: no transitions, no morphs, no speed changes, no camera movement inside a shot.

Follow this timeline:
"""
TAIL = "\nOutput: vertical 9:16, 30 fps, exactly the same duration as the source ({dur}s). Every frame not listed above stays on the original camera angle.\n"

BROLL = """Use the uploaded video as the only source. Video timing must be exactly the same as the original video.

Preserve the person's face, identity, clothing, body proportions and movement exactly as in the original footage. Preserve the room, lighting, equipment and background. Do not add music, sound, text, captions, logos or graphics. Do not replace, redesign or hallucinate any part of the scene.

The ONLY change is the camera angle: re-film this exact moment ({note}) from a {angle}. One locked-off shot, no cuts, no camera movement.

Output: vertical 9:16, 30 fps, {dur}s, same timing as the source.
"""


def snap(t: float) -> float:
    return round(round(t * FPS) / FPS, 3)


def parse_time(text: str) -> float:
    m = re.match(r"^\s*(?:at\s+)?(\d+):(\d{1,2}(?:\.\d+)?)", text)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.match(r"^\s*(?:at\s+)?(\d+(?:\.\d+)?)\s*s?\b", text)
    if not m:
        die(f"cannot read a time from B-roll request {text!r} (use e.g. '0:23 bench press lockout')")
    return float(m.group(1))


def boundaries(words: list, lo: float, hi: float) -> list[dict]:
    """Cut points on phrase starts / breaths: inside the silence before a word, never inside a word."""
    out = []
    for prev, w in zip(words, words[1:]):
        gap = w["start"] - prev["end"]
        if gap < 0.15:
            continue
        t = snap(max(prev["end"] + 0.03, w["start"] - 0.10))
        if lo <= t <= hi and prev["end"] <= t <= w["start"]:
            out.append({"t": t, "gap": round(gap, 2), "after": prev["text"], "before": w["text"]})
    return out


def scene_cuts(path: Path) -> list[float]:
    """Hard picture changes in the cut (jump cuts, shot changes). An angle shot must sit inside ONE shot."""
    import subprocess
    import numpy as np
    w, h = 48, 86
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8)
    n = len(a) // (w * h)
    if n < 3:
        return []
    d = np.abs(np.diff(a[: n * w * h].reshape(n, h, w).astype(np.float32), axis=0)).mean(axis=(1, 2))
    thr = max(18.0, float(np.median(d)) * 6)
    return [round(float(i + 1) / FPS, 3) for i in np.where(d > thr)[0]]


def rep_points(path: Path, lo: float, hi: float) -> list[dict]:
    """Moments where the motion is at a local minimum (the top or bottom of a rep): clean places to cut."""
    import subprocess
    import numpy as np
    w, h = 48, 86
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8)
    n = len(a) // (w * h)
    if n < 5:
        return []
    d = np.abs(np.diff(a[: n * w * h].reshape(n, h, w).astype(np.float32), axis=0)).mean(axis=(1, 2))
    d = np.convolve(d, np.ones(5) / 5, mode="same")
    out = []
    for i in range(3, len(d) - 3):
        t = snap((i + 1) / FPS)
        if lo <= t <= hi and d[i] == d[i - 3:i + 4].min():
            if not out or t - out[-1]["t"] >= 0.5:
                out.append({"t": t, "gap": 0.3, "after": "rep", "before": "rep"})
    return out


def mid_word(t: float, words: list) -> bool:
    return any(w["start"] + 0.02 < t < w["end"] - 0.02 for w in words)


def overlap(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    mc = cfg["multicam"]
    provider = cfg["generator"]["provider"]
    pcfg = cfg["providers"][provider]
    pmin = float(pcfg.get("min_clip_seconds", 4))
    smin, smax = max(float(mc["min_shot_seconds"]), pmin), max(float(mc["max_shot_seconds"]), pmin + 1)
    min_between = 3.0
    cut = OUT / "cut_version.mp4"
    if not cut.exists():
        die("output/cut_version.mp4 is missing: the Cuts Agent has to run first")
    cm = load_json(WORK / "cut_map.json")
    job = load_json(OUT / "job.json", default={})
    dur = probe(cut)["duration"]

    from transcribe import transcribe
    tr = transcribe(WORK / "cut_voice.wav")
    save_json(WORK / "transcript.json", tr)
    words = tr["words"]

    # a short take goes to the generator WHOLE (see multicam_generate.py), so angle shots can be short
    if pcfg.get("api") != "local" and dur <= float(pcfg.get("max_clip_seconds", 10)) \
            and dur <= float(cfg["generator"].get("max_generated_seconds", 24)) and not job.get("broll"):
        smin, smax, min_between = 1.2, 3.5, 1.0
    hook = next((s for s in cm["segments"] if s["type"] == "hook"), None)
    lo = (hook["out_end"] if hook else min(2.0, dur * 0.2)) + 0.3
    hi = cm["end_card"]["out_start"] - 0.5
    no_speech = len(words) < 3
    if no_speech:
        # nobody talks: cut on the movement instead, at the still points of the reps (top / bottom of a curl)
        cands = rep_points(cut, lo, hi)
    else:
        cands = boundaries(words, lo, hi)
    busy = [(e["out_start"], e["out_end"]) for e in cm["events"]]          # punch-ins, slow-mo, ramps
    shots = scene_cuts(cut)
    seg_starts = [s["out_start"] for s in cm["segments"]]

    # every span = (cut in, cut out) on two speech beats, the right length for the generator
    spans = []
    for a, b in itertools.combinations(cands, 2):
        length = b["t"] - a["t"]
        if not smin <= length <= smax:
            continue
        clash = sum(overlap(a["t"], b["t"], x, y) for x, y in busy)
        speech = sum(overlap(a["t"], b["t"], w["start"], w["end"]) for w in words) if not no_speech else length
        crosses = sum(1 for s in seg_starts if a["t"] < s < b["t"])       # do not straddle two exercises
        if any(a["t"] + 0.1 < c < b["t"] - 0.1 for c in shots):
            continue                                                       # never straddle two different shots
        score = speech - 4 * clash - 6 * crosses + min(a["gap"], 0.6) + min(b["gap"], 0.6)
        spans.append((score, a, b))
    n_spans = int(mc["cuts"]) // 2
    best, best_score = None, -1e9
    for combo in itertools.combinations(sorted(spans, key=lambda s: -s[0])[:60], n_spans):
        combo = sorted(combo, key=lambda s: s[1]["t"])
        if any(y[1]["t"] - x[2]["t"] < min_between for x, y in zip(combo, combo[1:])):
            continue                                                       # at least 3s of original camera between angles
        spread = min([y[1]["t"] - x[2]["t"] for x, y in zip(combo, combo[1:])] or [dur])
        score = sum(c[0] for c in combo) + 0.15 * min(spread, 20)
        if score > best_score:
            best, best_score = combo, score
    if not best:
        die(f"could not find {mc['cuts']} cut points on speech beats inside single continuous shots "
            f"({len(cands)} phrase starts, {len(shots)} shot changes between {lo:.1f}s and {hi:.1f}s). "
            "A multicam pass needs stretches of one continuous take of at least "
            f"{smin:.0f}s with speech: tell the Director.")

    angles = list(mc["angles"])
    plan_spans, lines, cuts = [], ["* At [0.0s]: original camera angle, unchanged."], []
    for i, (_, a, b) in enumerate(best):
        angle = angles[i % len(angles)]
        if angle not in ANGLES:
            die(f"config.yaml multicam.angles: unknown angle {angle!r} (use {', '.join(ANGLES)})")
        cuts += [a["t"], b["t"]]
        where = ("still point of a rep", "still point of a rep") if no_speech else (
            f"breath before \"{a['before']}\"", f"breath before \"{b['before']}\"")
        plan_spans.append({"id": f"angle_{i + 1}", "kind": "multicam", "from": a["t"], "to": b["t"], "angle": angle,
                           "cut_in": where[0], "cut_out": where[1]})
        lines.append(f"* At [{a['t']:.2f}s]: hard cut to a {ANGLES[angle]}. Same moment, same motion"
                     + (", same lip sync." if not no_speech else "."))
        last = i == len(best) - 1
        lines.append(f"* At [{b['t']:.2f}s]: hard cut back to the original camera angle"
                     + (f" and hold until the end at [{dur:.2f}s]." if last else "."))
    bad = [t for t in cuts if mid_word(t, words)]
    if bad:
        die(f"internal check failed: cut(s) {bad} land mid-word")
    prompt = HEAD + "\n" + "\n".join(lines) + "\n" + TAIL.format(dur=f"{dur:.2f}")
    (OUT / "multicam_prompt.txt").write_text(prompt)

    # B-roll Alfonso asked for: "at 0:23, bench press lockout"
    broll, texts = [], []
    for n, req in enumerate(job.get("broll", []), 1):
        at = parse_time(req)
        note = re.sub(r"^\s*(?:at\s+)?[\d:.]+s?\s*[,:-]?\s*", "", req).strip() or "this moment"
        angle = next((k for k in ANGLES if k.replace("-", " ") in req.lower() or k in req.lower()), "low")
        length = max(float(mc["broll_seconds"]), pmin)
        near = [c["t"] for c in cands if abs(c["t"] - at) <= 0.4]
        start = snap(min(near, key=lambda t: abs(t - at)) if near else at)
        if mid_word(start, words):   # never cut mid-word: slide to the start of that word's silence
            w = next(w for w in words if w["start"] < start < w["end"])
            start = snap(max(0.0, w["start"] - 0.06))
        before = [c for c in shots if c <= at + 0.05]
        after = [c for c in shots if c > at + 0.05]
        shot_in, shot_out = (before[-1] if before else 0.0), (after[0] if after else hi + 1.0)
        start = max(start, snap(shot_in))
        while mid_word(start, words):
            start = snap(start + 1 / FPS)
        end = snap(min(start + length, shot_out, hi + 1.0))
        if end - start < pmin - 0.01 or start < 0:
            die(f"B-roll request {req!r}: the shot that holds {at:.1f}s runs {shot_in:.2f}-{shot_out:.2f}s, "
                f"too short for a {pmin:.0f}s generated clip. Pick a moment inside a longer continuous shot.")
        if any(overlap(start, end, s["from"], s["to"]) > 0 for s in plan_spans + broll):
            die(f"B-roll request {req!r} overlaps another generated shot; pick a different time")
        broll.append({"id": f"broll_{n}", "kind": "broll", "from": start, "to": end, "angle": angle, "note": note,
                      "requested_at": at, "request": req})
        texts.append(f"--- B-roll {n}: {req} | cut-version time {start:.2f}s-{end:.2f}s ---\n"
                     + BROLL.format(note=note, angle=ANGLES[angle], dur=f"{end - start:.2f}"))
    bp = OUT / "broll_prompt.txt"
    if texts:
        bp.write_text("\n".join(texts))
    else:
        bp.unlink(missing_ok=True)

    save_json(WORK / "multicam_plan.json", {
        "source": "output/cut_version.mp4", "duration": round(dur, 3), "provider": provider, "cuts": cuts,
        "spans": plan_spans, "broll": broll, "prompt_file": "output/multicam_prompt.txt",
        "phrase_starts_found": len(cands), "cut_basis": "rep still points (no speech)" if no_speech else "speech beats"})

    print(f"speech     {len(words)} words, {len(cands)} "
          + ("rep still points (no speech: cutting on the movement)" if no_speech else "phrase starts / breaths")
          + " usable as cut points")
    print(f"4 cuts     {', '.join(f'{t:.2f}s' for t in cuts)}  (none mid-word)")
    for s in plan_spans:
        print(f"  {s['from']:6.2f}-{s['to']:6.2f}s  {s['angle']:<14} in on {s['cut_in']}, out on {s['cut_out']}")
    for b in broll:
        print(f"  {b['from']:6.2f}-{b['to']:6.2f}s  B-roll {b['angle']:<8} \"{b['note']}\" (asked for {b['requested_at']:.1f}s)")
    print("wrote      output/multicam_prompt.txt" + (" + output/broll_prompt.txt" if texts else ""))
    print("No video was generated by this job.")


if __name__ == "__main__":
    main()
