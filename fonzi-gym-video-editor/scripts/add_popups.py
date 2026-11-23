#!/usr/bin/env python3
"""TEXT / VISUALS AGENT tool. Pop-up cards on every gym reel (Alfonso, 2026-11-17), never on song videos.

    python3 scripts/add_popups.py            # merge ONLY the pop-ups into the existing output/work/overlay_props.json
    python3 scripts/add_popups.py --dry-run  # print what it would add, write nothing

build_overlay_props.py calls build_popups() too, so a fresh build already has them. Use this script when
overlay_props.json was hand-edited (caption fixes, callout positions ...): it replaces only the "popups" key
and brand.popupColor, everything else in the file stays exactly as it is.

From output/storyboard.json:
  "lifts": [{"name": "Landmine Press", "sets_reps": "4 x 12", "spanish": "Press de mina",
             "cut_start": 3.2, "cut_end": 14.8, "gold_title_end": 4.7,       # gold_title_end optional
             "bar_y": 1160, "checklist_y": 570}, ...]                          # *_y optional (keep off his face)
  "form_tip": {"lift": "Landmine Press", "at": 8.0, "cue": "Breathe out on the hardest part",
               "cue_es": "Exhala en la parte más difícil", "y": 196}           # y optional
  "video_type": "song_video"    # only on song videos: then NO pop-ups (a gym reel with a song is still a gym reel)

Timing: the Exercise Bar (every lift) and the Routine Checklist (every lift after the first) pop in when the
lift's gold title ends (lifts[].gold_title_end, else the end of an exercise_titles entry inside the lift,
else the lift start) and hold 4s or until the lift ends. The Form Tip
pops in once at form_tip.at and holds 5s (never past its lift's end). Nothing is on screen inside a storyboard
no_text_window (0.1s margin): a pop-up that would start inside one starts 0.1s after it, one that would run
into one ends 0.1s before it, unless the piece after the window is longer (then it waits until 0.1s after it).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, WORK, brand, die, load_json, rel, save_json  # noqa: E402

BAR_HOLD, TIP_HOLD, LIST_HOLD = 4.0, 5.0, 4.0
MARGIN = 0.1          # keep this far from a no_text_window
MIN_SHOW = 1.0        # a pop-up shorter than this after clipping is dropped (and reported)
BAR_Y, TIP_Y, LIST_Y = 1160, 196, 570   # tip below the progress bar label, list below the tip, bar above captions
DOT = "•"
# the only non-English text allowed on screen: the Spanish lines of these pop-ups (approved exception)
POPUP_CHARS = re.compile(r"^[\x20-\x7EÀ-ÿ¡¿•]*$")


def popup_text_ok(text: str) -> bool:
    """English + Spanish letters (á é í ó ú ü ñ ¿ ¡) + the • separator; never a hashtag."""
    return "#" not in text and bool(POPUP_CHARS.match(text))


def is_song_video(sb: dict) -> bool:
    return str(sb.get("video_type", "")).lower().replace("-", "_") in ("song_video", "song")


def no_text_windows(sb: dict, props: dict | None = None) -> list[tuple[float, float]]:
    out = []
    for w in sb.get("no_text_windows") or []:
        a, b = w.get("cut_start", w.get("from")), w.get("cut_end", w.get("to"))
        if a is not None and b is not None:
            out.append((float(a), float(b)))
    for w in (props or {}).get("noTextWindows") or []:
        out.append((float(w["from"]), float(w["to"])))
    return sorted(set(out))


def clip(a: float, b: float, windows: list) -> tuple[float, float]:
    """Shift the start out of a window, cut the end short of the next one (0.1s margin)."""
    for wa, wb in windows:
        if wa - MARGIN <= a < wb + MARGIN:
            a = wb + MARGIN
    for wa, wb in windows:
        if a < wa - MARGIN < b or (a < wa < b):
            b = min(b, wa - MARGIN)
    return round(a, 3), round(b, 3)


def place(start: float, hold: float, end: float, windows: list) -> tuple[float, float]:
    """Best spot for a pop-up that wants `hold` seconds from `start`, never past `end`: the first piece
    that fits, or (if a no-text window cuts it short) the longest piece right after a window."""
    best = clip(start, min(start + hold, end), windows)
    for wa, wb in windows:
        if wb + MARGIN <= start or wb + MARGIN >= end or best[1] - best[0] >= hold - 0.05:
            continue
        a2 = wb + MARGIN
        cand = clip(a2, min(a2 + hold, end), windows)
        if cand[1] - cand[0] > best[1] - best[0] + 0.05:
            best = cand
    return best


def build_popups(sb: dict, duration: float, props: dict | None = None) -> tuple[dict | None, list[str]]:
    """Returns (popups, notes). popups is None when this video gets none (song video / no lifts)."""
    notes = []
    if is_song_video(sb):
        return None, ["song video: no pop-ups (Alfonso's rule: gym reels only)"]
    lifts = sb.get("lifts") or []
    if not lifts:
        return None, ["storyboard has no \"lifts\": no pop-ups (the Storyboard Agent must add them on a gym reel)"]
    for i, l in enumerate(lifts):
        for k in ("name", "cut_start", "cut_end"):
            if l.get(k) in (None, ""):
                die(f"storyboard lifts[{i}] is missing {k!r}")
    lifts = sorted(lifts, key=lambda l: float(l["cut_start"]))
    wins = no_text_windows(sb, props)
    names = [l["name"].strip() for l in lifts]
    bars, lists = [], []
    for i, l in enumerate(lifts):
        cs, ce = float(l["cut_start"]), min(float(l["cut_end"]), duration)
        gt = l.get("gold_title_end")
        if gt is None:   # fall back to a per-exercise gold layered title inside this lift
            et = next((e for e in sb.get("exercise_titles") or [] if cs <= float(e["at"]) < ce), None)
            gt = float(et["at"]) + float(et.get("dur", 1.8)) if et else None
        start = float(gt) if gt is not None and cs <= float(gt) < ce else cs
        a, b = place(start, BAR_HOLD, ce, wins)
        if b - a < MIN_SHOW:
            notes.append(f"{l['name']}: no room for the bar/checklist ({a:.2f}-{b:.2f}s after the no-text windows)")
            continue
        detail = " ".join(x for x in [(l.get("sets_reps") or "").strip(),
                                      DOT if l.get("sets_reps") and l.get("spanish") else "",
                                      (l.get("spanish") or "").strip()] if x)
        bars.append({"from": a, "to": b, "title": l["name"].strip().upper(), "detail": detail,
                     "y": int(l.get("bar_y") or BAR_Y)})
        if i > 0:
            lists.append({"from": a, "to": b, "items": names, "current": i, "y": int(l.get("checklist_y") or LIST_Y)})

    tip = None
    ft = sb.get("form_tip") or {}
    if ft.get("cue"):
        lift = next((l for l in lifts if l["name"].strip().lower() == str(ft.get("lift", "")).strip().lower()), None)
        if not lift:
            die(f"form_tip.lift {ft.get('lift')!r} is not one of the lifts: {names}")
        cs, ce = float(lift["cut_start"]), min(float(lift["cut_end"]), duration)
        at = float(ft.get("at", cs + (ce - cs) / 3))
        if not cs <= at < ce:
            notes.append(f"form_tip.at {at} is outside {lift['name']} ({cs}-{ce}); moved to the lift start")
            at = cs
        a, b = place(at, TIP_HOLD, ce, wins)
        if b - a < MIN_SHOW:
            notes.append(f"form tip: no room at {at:.2f}s (no-text window / lift end); pick another 'at'")
        else:
            if b - a < TIP_HOLD - 0.05:
                notes.append(f"form tip holds {b - a:.2f}s, not 5s (lift end or a no-text window)")
            tip = {"from": a, "to": b, "lift": lift["name"].strip(), "cue": ft["cue"].strip(),
                   "cueEs": (ft.get("cue_es") or "").strip(), "y": int(ft.get("y") or TIP_Y)}
    else:
        notes.append("storyboard has no form_tip cue: no Form Tip card")
    pops = {"bars": bars, "formTip": tip, "checklists": lists}
    for path, text in walk_text(pops):
        if not popup_text_ok(text):
            die(f"pop-up text not allowed (English / Spanish letters only, no hashtags): {path} = {text!r}")
    return pops, notes


def walk_text(node, path="popups"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_text(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_text(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def summary(pops: dict | None) -> str:
    if not pops:
        return "no pop-ups"
    return (f"{len(pops['bars'])} exercise bars, {len(pops['checklists'])} checklists, "
            f"{'1 form tip' if pops['formTip'] else 'NO form tip'}")


def main():
    path = WORK / "overlay_props.json"
    props = load_json(path)
    sb = load_json(OUT / "storyboard.json")
    pops, notes = build_popups(sb, float(props["duration"]), props)
    for n in notes:
        print(f"note       {n}")
    if pops:
        for b in pops["bars"]:
            print(f"bar        {b['from']:6.2f}-{b['to']:6.2f}s  {b['title']} / {b['detail']}  y={b['y']}")
        for c in pops["checklists"]:
            print(f"checklist  {c['from']:6.2f}-{c['to']:6.2f}s  {c['current']} OF {len(c['items'])} DONE  y={c['y']}")
        if pops["formTip"]:
            t = pops["formTip"]
            print(f"form tip   {t['from']:6.2f}-{t['to']:6.2f}s  {t['cue']} / {t['cueEs']}  y={t['y']}")
    if "--dry-run" in sys.argv:
        return
    if pops:
        props["popups"] = pops
        props.setdefault("brand", {})["popupColor"] = brand().get("popup_color", "#FFFFFF")
    else:
        props.pop("popups", None)
    save_json(path, props)
    print(f"merged     {summary(pops)} into {rel(path)} (nothing else changed)")


if __name__ == "__main__":
    main()
