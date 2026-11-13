#!/usr/bin/env python3
"""DIRECTOR tool. Hands the approved video to Alfonso, who posts it himself.

    python3 scripts/export_final.py

Copies output/staged/final_edit.mp4 (only after QA passed AND Alfonso approved that exact file) to
exports/<date>_<title>.mp4 with the caption in a .txt beside it (and the carousel slides if any), and
records it in posted/ledger.json as "handed to Alfonso", so a re-edit of the same footage is flagged
as a duplicate by the Final Approval Agent later. Never posts anything.
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import LEDGER, OUT, ROOT, die, fingerprint, load_json, rel, save_json, sha256  # noqa: E402

if __name__ == "__main__":
    staged = OUT / "staged" / "final_edit.mp4"
    report = load_json(OUT / "qa_report.json", default={})
    approval = load_json(OUT / "staged" / "approval.json", default={})
    post = load_json(OUT / "staged" / "post.json", default={})
    if not staged.exists() or report.get("verdict") != "PASS":
        die("nothing to export: the Final Approval Agent has not passed and staged a video")
    vsha = sha256(staged)
    if vsha != report.get("sha256") or approval.get("sha256") != vsha:
        die("Alfonso has not approved this exact file yet (run scripts/approve.py after his yes)")
    title = re.sub(r"[^a-z0-9]+", "-", (post.get("title") or "gym-video").lower()).strip("-") or "gym-video"
    edir = ROOT / "exports"
    edir.mkdir(exist_ok=True)
    base = edir / f"{time.strftime('%Y-%m-%d')}_{title}"
    shutil.copy2(staged, base.with_suffix(".mp4"))
    lines = [post.get("caption", "")]
    car = post.get("carousel") or {}
    if car.get("slides"):
        sdir = Path(str(base) + "_carousel")
        sdir.mkdir(exist_ok=True)
        for s in car["slides"]:
            shutil.copy2(ROOT / s, sdir / Path(s).name)
        lines += ["", "Carousel caption:", car.get("caption", "")]
    base.with_suffix(".txt").write_text("\n".join(lines).strip() + "\n")
    ledger = load_json(LEDGER, default={"posted": []})
    if not any(e.get("sha256") == vsha for e in ledger["posted"]):
        ledger["posted"].append({"sha256": vsha, "source_sha256": post.get("source_sha256"),
                                 "fingerprint": fingerprint(staged), "title": post.get("title"),
                                 "posted_at": time.strftime("%Y-%m-%d %H:%M:%S"), "reel": {},
                                 "handed_to_alfonso": rel(base.with_suffix(".mp4"))})
        save_json(LEDGER, ledger)
    print(f"exported {rel(base.with_suffix('.mp4'))} + {rel(base.with_suffix('.txt'))}"
          + (f" + {rel(Path(str(base) + '_carousel'))}/" if car.get("slides") else ""))
    print("Nothing was posted. Alfonso posts it himself.")
