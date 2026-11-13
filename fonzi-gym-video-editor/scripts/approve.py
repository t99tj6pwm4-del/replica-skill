#!/usr/bin/env python3
"""DIRECTOR tool. Records Alfonso's final yes. Run it ONLY after Alfonso has said yes in his own words
to the staged video in this conversation. post_to_meta.py refuses to post without this record.

    python3 scripts/approve.py --alfonso-said-yes [--own-footage-confirmed]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, die, load_json, save_json, sha256  # noqa: E402

if __name__ == "__main__":
    if "--alfonso-said-yes" not in sys.argv:
        die("refusing: pass --alfonso-said-yes, and only after Alfonso actually approved the staged video")
    report = load_json(OUT / "qa_report.json")
    staged = OUT / "staged" / "final_edit.mp4"
    if report.get("verdict") != "PASS" or not staged.exists():
        die("the Final Approval Agent has not passed and staged this video")
    if sha256(staged) != report["sha256"]:
        die("the staged video is not the one QA checked. Run QA again.")
    if report.get("needs_own_footage_confirmation") and "--own-footage-confirmed" not in sys.argv:
        die("Alfonso still has to confirm this is his own footage (then add --own-footage-confirmed)")
    save_json(OUT / "staged" / "approval.json", {"approved_by": "Alfonso", "sha256": report["sha256"],
                                                 "approved_at": time.strftime("%Y-%m-%d %H:%M:%S")})
    print("approval recorded: output/staged/approval.json")
