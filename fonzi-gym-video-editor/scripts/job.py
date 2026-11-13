#!/usr/bin/env python3
"""DIRECTOR tool. Job tracking only: it never touches video.

    python3 scripts/job.py init input/<video> --brief "Friday gym video, Form Fix Friday, 60 seconds" [--own-footage yes|no|unknown]
        [--caption "Alfonso's own post caption, posted word for word"] [--broll "0:23 bench press lockout"]...
    python3 scripts/job.py broll "0:23 bench press lockout"     # add a B-roll request later (time = cut-version time)
    python3 scripts/job.py set <storyboard|cuts|multicam|text_visuals|qa|approval|posted> <working|done|failed|waiting> [--note "..."]
    python3 scripts/job.py show

`init` moves the previous job's files into output/archive/<time>/ so jobs never mix.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, die, load_json, rel, resolve, save_json  # noqa: E402

STEPS = ["storyboard", "cuts", "multicam", "text_visuals", "qa", "approval", "posted"]
NAMES = {"storyboard": "Storyboard", "cuts": "Cuts", "multicam": "Multicam/B-Roll", "text_visuals": "Text/Visuals", "qa": "Final Approval (QA)",
         "approval": "Alfonso's approval", "posted": "Posted to Meta"}
JOB = OUT / "job.json"


def show(job: dict):
    print(f"job    {job['video']}  |  {job['brief']}")
    for s in STEPS:
        st = job["steps"][s]
        extra = f"  (attempt {st['attempts']})" if st["attempts"] > 1 else ""
        note = f"  - {st['note']}" if st.get("note") else ""
        print(f"  {NAMES[s]:<22} {st['status']}{extra}{note}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("video")
    i.add_argument("--brief", required=True)
    i.add_argument("--own-footage", choices=["yes", "no", "unknown"], default="unknown")
    i.add_argument("--caption", default="")
    i.add_argument("--broll", action="append", default=[])
    b = sub.add_parser("broll")
    b.add_argument("request")
    s = sub.add_parser("set")
    s.add_argument("step", choices=STEPS)
    s.add_argument("status", choices=["working", "done", "failed", "waiting"])
    s.add_argument("--note", default="")
    sub.add_parser("show")
    a = ap.parse_args()

    if a.cmd == "init":
        video = resolve(a.video)
        if not video.exists():
            die(f"video not found: {a.video}")
        OUT.mkdir(exist_ok=True)
        old = [p for p in OUT.iterdir() if p.name not in ("archive", ".gitkeep")]
        if old:
            dest = OUT / "archive" / time.strftime("%Y%m%d-%H%M%S")
            dest.mkdir(parents=True)
            for p in old:
                if p.name == "work":
                    shutil.rmtree(p)   # scratch files are not worth keeping
                else:
                    shutil.move(str(p), dest / p.name)
            print(f"previous job archived to {rel(dest)}")
        job = {"video": rel(video), "brief": a.brief, "own_footage_confirmed": a.own_footage,
               "caption": a.caption, "broll": a.broll,
               "created": time.strftime("%Y-%m-%d %H:%M:%S"),
               "steps": {s: {"status": "pending", "attempts": 0, "note": ""} for s in STEPS}}
        save_json(JOB, job)
        show(job)
        return

    job = load_json(JOB)
    if a.cmd == "broll":
        job.setdefault("broll", []).append(a.request)
        save_json(JOB, job)
        print(f"B-roll requests: {job['broll']}")
    if a.cmd == "set":
        st = job["steps"][a.step]
        if a.status == "working":
            st["attempts"] += 1
        st["status"], st["note"] = a.status, a.note
        st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_json(JOB, job)
    show(job)


if __name__ == "__main__":
    main()
