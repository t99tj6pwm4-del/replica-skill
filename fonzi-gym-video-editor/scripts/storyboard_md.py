#!/usr/bin/env python3
"""STORYBOARD AGENT tool. Checks output/storyboard.json and writes output/storyboard.md from it,
so the plan Alfonso reads and the plan the Cuts Agent follows can never disagree.

    python3 scripts/storyboard_md.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, WORK, die, load_json, resolve  # noqa: E402

TYPES = {"hook", "exercise", "talk", "broll"}
EFFECTS = {"punch_in", "slow_mo", "speed_ramp", "callout"}


def english_only(text: str, where: str, errors: list):
    if not text:
        return
    if "#" in text:
        errors.append(f"{where}: no hashtags on screen ({text!r})")
    if re.search(r"[^\x20-\x7E]", text):
        errors.append(f"{where}: on-screen text must be plain English characters ({text!r})")


def validate(sb: dict, src_duration: float | None = None) -> tuple[list, list, float]:
    errors, warnings = [], []
    for key in ("title", "source", "segments", "hook", "end_card"):
        if key not in sb:
            errors.append(f"missing '{key}'")
    if errors:
        return errors, warnings, 0.0
    if not resolve(sb["source"]).exists():
        errors.append(f"source video not found: {sb['source']}")
    if sb.get("song") and not resolve(sb["song"]).exists():
        errors.append(f"song not found: {sb['song']}")
    english_only(sb["hook"].get("text", ""), "hook.text", errors)
    english_only(sb["hook"].get("subtitle", ""), "hook.subtitle", errors)
    english_only(sb["end_card"].get("text", ""), "end_card.text", errors)
    english_only(sb["end_card"].get("subtitle", ""), "end_card.subtitle", errors)
    total = 0.0
    if not sb["segments"]:
        errors.append("no segments")
    elif sb["segments"][0].get("type") != "hook":
        errors.append("the first segment must be the hook (type 'hook')")
    for i, s in enumerate(sb["segments"]):
        name = f"segment {i + 1} ({s.get('id', '?')})"
        if s.get("type") not in TYPES:
            errors.append(f"{name}: type must be one of {sorted(TYPES)}")
        a, b = s.get("src_in"), s.get("src_out")
        if a is None or b is None or b <= a:
            errors.append(f"{name}: needs src_in < src_out")
            continue
        if src_duration and b > src_duration + 0.05:
            errors.append(f"{name}: src_out {b} is past the end of the video ({src_duration:.2f}s)")
        if s.get("type") == "exercise" and not s.get("exercise"):
            errors.append(f"{name}: exercise segments need 'exercise'")
        english_only(s.get("exercise", ""), f"{name} exercise", errors)
        english_only(s.get("sets_reps", ""), f"{name} sets_reps", errors)
        seg_len = (b - a) / float(s.get("speed", 1.0))
        for e in s.get("effects", []):
            if e.get("type") not in EFFECTS:
                errors.append(f"{name}: unknown effect {e.get('type')!r}")
                continue
            if e["type"] in ("punch_in", "callout"):
                t0, t1 = e.get("at"), (e.get("at") or 0) + e.get("dur", 0)
            else:
                t0, t1 = e.get("from"), e.get("to")
            if t0 is None or t1 is None or t1 <= t0 or t0 < a - 0.01 or t1 > b + 0.01:
                errors.append(f"{name}: effect {e['type']} must sit inside {a}-{b}s of the source")
                continue
            if e["type"] == "punch_in" and not 1.10 <= e.get("zoom", 1.2) <= 1.30:
                errors.append(f"{name}: punch-in zoom must be 1.10-1.30")
            if e["type"] in ("slow_mo", "speed_ramp"):
                sp = e.get("speed")
                if not sp or not 0.25 <= sp <= 4:
                    errors.append(f"{name}: {e['type']} speed must be 0.25-4")
                else:
                    seg_len += (t1 - t0) / sp - (t1 - t0) / float(s.get("speed", 1.0))
            if e["type"] == "callout":
                english_only(e.get("text", ""), f"{name} callout", errors)
        total += seg_len
    if not 1.0 <= sb["segments"][0]["src_out"] - sb["segments"][0]["src_in"] <= 3.5 if sb["segments"] else False:
        warnings.append("hook segment should be about 2 seconds")
    total += float(sb["end_card"].get("duration", 2.5))
    lo, hi = sb.get("min_duration", 60), sb.get("max_duration", 90)
    if not lo <= total <= hi:
        errors.append(f"planned length is {total:.1f}s; it must land between {lo} and {hi}s "
                      "(pauses removed by the Cuts Agent will shorten it a little more)")
    exercises = [s for s in sb["segments"] if s.get("type") == "exercise"]
    names = list(dict.fromkeys(s["exercise"] for s in exercises if s.get("exercise")))
    if len(names) >= 2 and len(sb.get("carousel", [])) < len(names):
        errors.append("2+ exercises: 'carousel' must list every exercise with sets_reps")
    return errors, warnings, total


def fmt(t: float) -> str:
    return f"{t:.1f}s"


def render(sb: dict, total: float) -> str:
    L = [f"# Storyboard: {sb['title']}", ""]
    L += [f"- **Brief:** {sb.get('brief', '')}",
          f"- **Raw video:** `{sb['source']}`",
          f"- **Planned length:** about {total:.0f}s, vertical 9:16, 1080x1920, 30fps",
          f"- **Song:** `{sb['song']}`" + (f" ({sb.get('song_bpm')} BPM, punch-ins land on the beat)" if sb.get("song_bpm") else "")
          if sb.get("song") else "- **Song:** none (original audio only)",
          ""]
    if sb.get("summary"):
        L += [sb["summary"], ""]
    L += ["## Timeline", "",
          "| # | Final time | From raw | Segment | Exercise | On-screen text | Visuals / edit |",
          "|---|---|---|---|---|---|---|"]
    t = 0.0
    for i, s in enumerate(sb["segments"], 1):
        a, b = s["src_in"], s["src_out"]
        length = (b - a) / float(s.get("speed", 1.0))
        fx = []
        for e in s.get("effects", []):
            if e["type"] == "punch_in":
                fx.append(f"punch-in {round(e.get('zoom', 1.2) * 100)}% at {fmt(e['at'])} for {fmt(e['dur'])}")
            elif e["type"] == "slow_mo":
                fx.append(f"slow-mo {e['speed']}x on {fmt(e['from'])}-{fmt(e['to'])}")
                length += (e["to"] - e["from"]) * (1 / e["speed"] - 1 / float(s.get("speed", 1.0)))
            elif e["type"] == "speed_ramp":
                fx.append(f"speed ramp {e['speed']}x on {fmt(e['from'])}-{fmt(e['to'])}")
                length += (e["to"] - e["from"]) * (1 / e["speed"] - 1 / float(s.get("speed", 1.0)))
            elif e["type"] == "callout":
                fx.append(f"callout \"{e['text']}\" at {fmt(e['at'])}")
        if s.get("remove_pauses"):
            fx.append("cut pauses over 0.5s")
        if s.get("visual"):
            fx.insert(0, s["visual"])
        if s["type"] == "hook":
            text = f"Title card: \"{sb['hook']['text']}\"" + (f" / \"{sb['hook']['subtitle']}\"" if sb["hook"].get("subtitle") else "")
        elif s["type"] == "exercise":
            text = f"Lower third: \"{s['exercise'].upper()}" + (f" - {s['sets_reps']}\"" if s.get("sets_reps") else "\"")
        else:
            text = s.get("text", "captions only")
        L.append(f"| {i} | {fmt(t)}-{fmt(t + length)} | {fmt(a)}-{fmt(b)} | {s.get('label', s['type'])} | "
                 f"{s.get('exercise', '-')}{' ' + s['sets_reps'] if s.get('sets_reps') else ''} | {text} | {'; '.join(fx) or '-'} |")
        t += length
    ec = sb["end_card"]
    L.append(f"| {len(sb['segments']) + 1} | {fmt(t)}-{fmt(t + ec.get('duration', 2.5))} | freeze of last frame | End card | - | "
             f"\"{ec['text']}\"" + (f" / \"{ec['subtitle']}\"" if ec.get("subtitle") else "") + " | animated bookmark end card |")
    L += ["", "## Throughout", "",
          "- Word-by-word captions, each word pops in as it is said; key words in the brand colour: "
          + (", ".join(sb.get("key_words", [])) or "(none listed)"),
          "- Segmented progress bar across the top",
          "- English only, no hashtags on screen", ""]
    if sb.get("carousel"):
        L += ["## Carousel post (2+ exercises)", "", "| Exercise | Sets x reps | Cue |", "|---|---|---|"]
        L += [f"| {c['exercise']} | {c.get('sets_reps', '')} | {c.get('cue', '')} |" for c in sb["carousel"]]
        L.append("")
    if sb.get("caption"):
        L += ["## Post caption", "", sb["caption"], ""]
    if sb.get("notes"):
        L += ["## Notes for the editors", ""] + [f"- {n}" for n in sb["notes"]] + [""]
    return "\n".join(L)


def main():
    sb = load_json(OUT / "storyboard.json")
    analysis = load_json(WORK / "analysis.json", default={})
    dur = analysis.get("probe", {}).get("duration")
    errors, warnings, total = validate(sb, dur)
    for w in warnings:
        print(f"warning: {w}")
    if errors:
        die("storyboard.json is not valid:\n  - " + "\n  - ".join(errors))
    (OUT / "storyboard.md").write_text(render(sb, total))
    print(f"storyboard OK, planned length {total:.1f}s -> output/storyboard.md")


if __name__ == "__main__":
    main()
