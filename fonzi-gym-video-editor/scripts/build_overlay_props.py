#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Turns storyboard + cut map + Whisper words into the data the
Remotion motion-graphics layer animates.

    python3 scripts/build_overlay_props.py            # uses the Multicam Agent's Whisper transcript if there is one
    python3 scripts/build_overlay_props.py --retranscribe      # run Whisper again on output/work/cut_voice.wav

Writes output/work/overlay_props.json (safe to hand-edit: fix a mis-heard word, move a callout,
change which words are highlighted), then run scripts/render_final.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, W, WORK, brand, die, load_json, rel, save_json  # noqa: E402

MAX_WORDS = 3      # words on screen at once
MAX_CHARS = 18
GAP = 0.55         # a pause this long starts a new caption page
STOP = set("a an the and or but so of to in on at for with is are was be it its this that you your i we my "
           "me do does not no yes up down out off just very really then than as if when from by".split())


def clean(word: str) -> str:
    word = word.replace("#", "").replace("’", "'").upper()
    word = re.sub(r"[^\x20-\x7E]", "", word)          # English characters only
    return re.sub(r"^[^A-Z0-9']+|[^A-Z0-9'%!?]+$", "", word)


def caption_pages(words: list, key_words: set, t_min: float, t_max: float) -> list:
    pages, cur = [], []

    def flush():
        if cur:
            pages.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": list(cur)})
            cur.clear()

    for i, w in enumerate(words):
        text = clean(w["text"])
        if not text or w["end"] <= t_min or w["start"] >= t_max:
            continue
        start, end = max(w["start"], t_min), min(max(w["end"], w["start"] + 0.12), t_max)
        bare = re.sub(r"[^A-Z0-9]", "", text)
        hi = bare.lower() in key_words or (bare.isdigit() and bare.lower() not in STOP)
        chars = sum(len(x["text"]) + 1 for x in cur) + len(text)
        ends_sentence = bool(re.search(r"[.!?,]$", w["text"].strip())) or i == len(words) - 1
        full = len(cur) >= MAX_WORDS or chars > MAX_CHARS
        if full and ends_sentence and len(cur) == MAX_WORDS and chars <= MAX_CHARS + 4:
            full = False   # keep a sentence's last word with its friends instead of alone on screen
        if cur and (full or start - cur[-1]["end"] > GAP):
            flush()
        cur.append({"text": text, "start": round(start, 3), "end": round(end, 3), "highlight": hi})
        if re.search(r"[.!?]$", w["text"].strip()):
            flush()
    flush()
    # hold each page until the next one starts (max 0.6s) so words do not flicker off
    for i, p in enumerate(pages):
        nxt = pages[i + 1]["start"] if i + 1 < len(pages) else t_max
        p["end"] = round(min(p["end"] + 0.6, nxt, t_max), 3)
    return pages


def main():
    sb = load_json(OUT / "storyboard.json")
    cm = load_json(WORK / "cut_map.json")
    b = brand()
    tpath = WORK / "transcript.json"
    if "--retranscribe" in sys.argv or not tpath.exists():
        from transcribe import transcribe
        save_json(tpath, transcribe(WORK / "cut_voice.wav"))
    words = load_json(tpath)["words"]

    segs = cm["segments"]
    hook = next((s for s in segs if s["type"] == "hook"), None)
    title_end = hook["out_end"] if hook else min(2.0, cm["body_end"])
    end = cm["end_card"]

    key_words = {k.lower() for k in sb.get("key_words", [])}
    for k in list(key_words):
        key_words |= set(k.split())

    lower, seen = [], []
    ex_segs = [s for s in segs if s["type"] == "exercise" and s.get("exercise")]
    names = list(dict.fromkeys(s["exercise"] for s in ex_segs))
    for s in ex_segs:
        if s["exercise"] in seen:
            continue
        seen.append(s["exercise"])
        lower.append({
            "from": round(s["out_start"] + 0.15, 3),
            "to": round(min(s["out_start"] + 4.8, s["out_end"] - 0.1), 3),
            "title": s["exercise"].upper(), "detail": s.get("sets_reps") or "",
            "index": len(seen), "total": len(names),
        })

    # progress bar: one part for the hook, one per exercise (its extra shots belong to it), one for the outro
    progress = []
    for i, s in enumerate(segs):
        outro = i == len(segs) - 1 and s["type"] == "talk" and len(segs) > 2
        if s["type"] == "hook" or outro or not progress:
            label = s.get("label") or s["type"]
        elif s.get("exercise"):
            label = s["exercise"]
        else:
            label = progress[-1]["label"] if progress[-1]["label"] in names else (s.get("label") or s["type"])
        if progress and progress[-1]["label"] == label:
            progress[-1]["to"] = s["out_end"]
        else:
            progress.append({"from": s["out_start"], "to": s["out_end"], "label": label})

    events = []
    mmap = load_json(WORK / "multicam_map.json", default={})
    for n, ins in enumerate(mmap.get("inserts", []), 2):
        label = "B-ROLL" if ins["kind"] == "broll" else f"CAM {n}"
        events.append({"from": ins["from"], "to": ins["to"], "kind": "cam",
                       "label": label})
    for e in cm["events"]:
        ev = {"from": e["out_start"], "to": e["out_end"], "kind": e["kind"]}
        if e["kind"] == "slow_mo":
            ev["label"] = f"SLOW-MO {e['speed']:g}x"
        elif e["kind"] == "hero":
            ev["kind"], ev["label"] = "slow_mo", "HERO SLOW-MO"
        elif e["kind"] == "speed_ramp":
            ev["label"] = f"{e['speed']:g}x SPEED"
        events.append(ev)

    props = {
        "fps": FPS, "width": W, "height": H, "duration": cm["duration"],
        "brand": {k: b[k] for k in ("name", "handle", "color", "textColor", "darkColor")},
        "layout": {"captionY": 1400, "lowerThirdY": 1090},
        "title": {"from": 0, "to": title_end, "text": sb["hook"]["text"].upper(),
                  "subtitle": sb["hook"].get("subtitle", "")},
        "lowerThirds": lower,
        "progress": progress,
        "captions": caption_pages(words, key_words, title_end, end["out_start"]),
        "callouts": [{"from": c["out_start"], "to": c["out_end"], "text": c["text"].upper(),
                      "x": c.get("x") or 0.5, "y": c.get("y") or 0.42} for c in cm["callouts"]],
        "events": events,
        "endCard": {"from": end["out_start"], "to": end["out_end"], "text": sb["end_card"]["text"].upper(),
                    "subtitle": sb["end_card"].get("subtitle", "")},
    }
    save_json(WORK / "overlay_props.json", props)
    n = sum(len(p["words"]) for p in props["captions"])
    print(f"captions   {n} words on {len(props['captions'])} pages, "
          f"{sum(w['highlight'] for p in props['captions'] for w in p['words'])} highlighted")
    print(f"visuals    title card, {len(lower)} lower-thirds, {len(progress)}-part progress bar, "
          f"{len(props['callouts'])} callouts, {len(events)} edit accents, end card")
    if not words:
        print("note       Whisper heard no speech in the cut, so there are no captions to animate.")
    print(f"wrote      {rel(WORK / 'overlay_props.json')}")


if __name__ == "__main__":
    if not (WORK / "cut_map.json").exists():
        die("output/work/cut_map.json is missing: the Cuts Agent has to run first")
    main()
