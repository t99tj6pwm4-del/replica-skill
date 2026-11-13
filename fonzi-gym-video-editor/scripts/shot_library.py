"""The 100-shot multicam library (docs/multicam_shot_library.md) and the rules for picking from it.

Used by multicam_prompt.py. Rules:
  * 4 shots per video, from 4 DIFFERENT categories
  * fitted to the moment: hard rep -> low hero / detail close-up, talking -> face / chest up,
    setup -> wide / full body
  * no shot number from the previous video unless Alfonso asks (--allow-repeat)
  * shot 100 ("back to the original camera") only as the closing angle
  * shots Flow cannot do safely or cleanly (config multicam.skip_shots) are never picked
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from common import OUT, ROOT, die

LIBRARY = ROOT / "docs" / "multicam_shot_library.md"
LOG = OUT / "multicam_shots_log.md"
CLOSING = 100

# what fits which moment, best first (the agent can always choose its own with --shots)
FIT = {
    "hard_rep": [22, 91, 80, 99, 23, 10, 37, 38, 81, 84, 95, 44, 29, 28, 54, 60, 63, 77, 90, 93],
    "talking": [6, 7, 5, 25, 27, 26, 16, 17, 44, 48, 93, 49, 50, 15, 56],
    "setup": [2, 3, 1, 94, 43, 14, 24, 56, 58, 59, 53, 75, 65, 39, 40, 11],
}


def load() -> dict[int, dict]:
    if not LIBRARY.exists():
        die("docs/multicam_shot_library.md is missing")
    shots, cat = {}, None
    for line in LIBRARY.read_text().splitlines():
        if line.startswith("## "):
            cat = line[3:].strip()
            continue
        m = re.match(r"^(\d+)\. (.+)$", line.strip())
        if m and cat:
            shots[int(m.group(1))] = {"num": int(m.group(1)), "category": cat, "text": m.group(2).strip()}
    if len(shots) != 100:
        die(f"docs/multicam_shot_library.md has {len(shots)} numbered shots, expected 100")
    return shots


def description(shot: dict) -> str:
    """'Low angle looking up' -> 'low angle looking up' for the 'Hard cut to ...' prompt."""
    t = shot["text"]
    return t[0].lower() + t[1:] if not t[:2].isupper() else t


def last_video_shots(video: str = "") -> set[int]:
    """Shot numbers of the most recent OTHER video in the log."""
    if not LOG.exists():
        return set()
    rows = [r for r in LOG.read_text().splitlines() if r.startswith("| 20")]
    rows = [r for r in rows if not video or r.split("|")[2].strip() != video]
    return {int(n) for n in re.findall(r"#(\d+)", rows[-1])} if rows else set()


def pick(moments: list[str], skip: set[int], chosen: list[int] | None, allow_repeat: bool,
         video: str = "") -> list[dict]:
    """moments: one of hard_rep / talking / setup per shot, in time order."""
    lib = load()
    banned = set(skip) | (set() if allow_repeat else last_video_shots(video))
    if chosen:
        if len(chosen) != len(moments):
            die(f"--shots needs exactly {len(moments)} shot numbers, got {len(chosen)}")
        out = []
        for i, n in enumerate(chosen):
            if n not in lib:
                die(f"shot {n} is not in the library (1-100)")
            if n in skip:
                die(f"shot {n} ({lib[n]['text']}) is on the skip list: Flow cannot do it safely or cleanly")
            if n == CLOSING and i != len(chosen) - 1:
                die("shot 100 (back to the original camera) can only be the closing shot")
            if n in banned and not allow_repeat:
                die(f"shot {n} was used in the previous video. Pick another, or pass --allow-repeat if Alfonso asked")
            out.append(lib[n])
        cats = [s["category"] for s in out]
        if len(set(cats)) != len(cats):
            die(f"the {len(out)} shots must come from {len(out)} different categories (got {cats})")
        return out
    out, used_cats = [], set()
    for m in moments:
        pref = FIT.get(m, FIT["hard_rep"]) + list(range(1, 100))
        pickn = next((n for n in pref if n in lib and n not in banned and n != CLOSING
                      and lib[n]["category"] not in used_cats and n not in [s["num"] for s in out]), None)
        if pickn is None:
            die("could not find enough unused shots from different categories")
        out.append(lib[pickn])
        used_cats.add(lib[pickn]["category"])
    return out


def log_shots(video: str, spans: list[dict]) -> None:
    if not LOG.exists():
        LOG.write_text("# Multicam shots log\n\nEvery shot used, so the next video does not repeat them.\n\n"
                       "| Date | Video | Shots (timestamp: shot) |\n|---|---|---|\n")
    row = ", ".join(f"{s['from']:.2f}s: #{s['shot']} {s['shot_text']}" for s in spans)
    line = f"| {time.strftime('%Y-%m-%d %H:%M')} | {video} | {row} |"
    lines = LOG.read_text().rstrip("\n").split("\n")
    if lines[-1].startswith("| 20") and lines[-1].split("|")[2].strip() == video:
        lines[-1] = line          # a re-plan of the same video replaces its row
    else:
        lines.append(line)
    LOG.write_text("\n".join(lines) + "\n")
