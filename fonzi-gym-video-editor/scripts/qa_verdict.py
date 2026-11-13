#!/usr/bin/env python3
"""FINAL APPROVAL AGENT tool, step 2 of 2. Records what the agent saw in the 3 frames, combines it
with the measurements from qa_check.py, and writes the pass/fail report.

    python3 scripts/qa_verdict.py --captions pass --zoom pass --face-clear pass --own-footage pass \
        --notes "what you saw in each frame"

    # any visual fail needs who fixes it and the exact fix:
    python3 scripts/qa_verdict.py --captions fail --zoom pass --face-clear pass --own-footage pass \
        --send-to text_visuals --fix "Captions sit on the lifter's face at 31s: set layout.captionY to 1500"

PASS -> copies the video to output/staged/ ready for Alfonso's yes. FAIL -> nothing is staged.
This script never edits the video and never posts.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, die, load_json, rel, save_json, sha256  # noqa: E402

AGENT = {"multicam": "Multicam/B-Roll Agent", "cuts": "Cuts Agent", "text_visuals": "Text/Visuals Agent", "storyboard": "Storyboard Agent",
         "director": "Director (needs Alfonso)"}


def main():
    ap = argparse.ArgumentParser()
    for flag in ("captions", "zoom", "face-clear", "own-footage"):
        ap.add_argument(f"--{flag}", choices=["pass", "fail"], required=True)
    for flag in ("lip-sync", "broll-match"):   # required when the video has multicam / B-roll shots
        ap.add_argument(f"--{flag}", choices=["pass", "fail", "na"], default="na")
    ap.add_argument("--notes", default="")
    ap.add_argument("--send-to", choices=["cuts", "multicam", "text_visuals", "storyboard", "director"])
    ap.add_argument("--fix", default="")
    a = ap.parse_args()

    tech = load_json(OUT / "qa" / "tech.json")
    final = OUT / "final_edit.mp4"
    if not final.exists() or sha256(final) != tech.get("sha256"):
        die("final_edit.mp4 changed since qa_check.py ran. Run scripts/qa_check.py again first.")
    visual = [
        ("captions readable", a.captions), ("zoom / framing looks right", a.zoom),
        ("no text covering the face mid-lift", a.face_clear),
        ("looks like Alfonso's own footage (no other creator's watermark, logo or stock branding)", a.own_footage),
    ]
    if tech.get("compares"):
        if "na" in (a.lip_sync, a.broll_match):
            die("this video has multicam / B-roll shots: --lip-sync and --broll-match must be pass or fail")
        visual += [("lip sync matches in the new angles", a.lip_sync),
                   ("multicam / B-roll shows the same moment as the original", a.broll_match)]
    vis_fail = [n for n, r in visual if r == "fail"]
    if vis_fail and not (a.send_to and a.fix):
        die("a visual check failed: --send-to and --fix (the exact fix needed) are required")

    # 'own footage not confirmed yet' is a question for Alfonso at approval, not a defect in the edit
    soft = "Alfonso confirmed it is his own footage"
    tech_fail = [c for c in tech["checks"] if not c["pass"] and not c.get("soft")]
    notes_for_alfonso = [c for c in tech["checks"] if not c["pass"] and c.get("soft")]
    ask_owner = any(c["check"] == soft for c in notes_for_alfonso)

    send_back = []
    for c in tech_fail:
        send_back.append({"to": c["owner"], "fix": f"{c['check']}: got {c['detail']}"})
    if vis_fail:
        send_back.append({"to": a.send_to, "fix": a.fix})
    elif a.send_to and a.fix and send_back:
        send_back.append({"to": a.send_to, "fix": a.fix})   # the agent's own note on a measured fail
    passed = not send_back
    report = {"verdict": "PASS" if passed else "FAIL", "checked": time.strftime("%Y-%m-%d %H:%M:%S"),
              "final": tech["final"], "sha256": tech["sha256"], "technical": tech["checks"],
              "visual": [{"check": n, "pass": r == "pass"} for n, r in visual], "frames": tech["frames"],
              "compares": tech.get("compares", []), "notes": a.notes, "send_back": send_back,
              "needs_own_footage_confirmation": ask_owner,
              "tell_alfonso": [f"{c['check']}: {c['detail']}" for c in notes_for_alfonso]}

    staged = OUT / "staged"
    shutil.rmtree(staged, ignore_errors=True)
    if passed:
        staged.mkdir(parents=True)
        shutil.copy2(final, staged / "final_edit.mp4")
        sb = load_json(OUT / "storyboard.json", default={})
        carousel = load_json(OUT / "carousel" / "carousel.json", default={})
        save_json(staged / "post.json", {
            "video": rel(staged / "final_edit.mp4"), "sha256": tech["sha256"], "source_sha256": tech.get("source_sha256"),
            "title": sb.get("title", ""),
            # Alfonso's own caption is posted word for word; the storyboard's is only a fallback
            "caption": load_json(OUT / "job.json", default={}).get("caption") or sb.get("caption") or sb.get("title", ""),
            "carousel": carousel or None, "facebook_page": "Fonzi.stays.fit", "instagram": "@fonzi.stays.fit"})
        report["staged"] = rel(staged / "final_edit.mp4")
    save_json(OUT / "qa_report.json", report)

    p = tech["probe"]
    L = [f"# Final Approval report: {report['verdict']}", "",
         f"- **Video:** `{tech['final']}`  ({p['video']['width']}x{p['video']['height']}, {p['video']['fps']}fps, "
         f"{p['duration']:.1f}s)" if p.get("video") else f"- **Video:** `{tech['final']}`",
         f"- **Checked:** {report['checked']}", "",
         "## Measured (ffprobe)", "", "| Check | Result | Detail |", "|---|---|---|"]
    for c in tech["checks"]:
        res = "PASS" if c["pass"] else ("TELL ALFONSO" if c.get("soft") else "FAIL")
        L.append(f"| {c['check']} | {res} | {c['detail']} |")
    L += ["", "## Looked at (3 sampled frames)", "", "| Check | Result |", "|---|---|"]
    L += [f"| {n} | {'PASS' if r == 'pass' else 'FAIL'} |" for n, r in visual]
    L += [""] + [f"- `{f['file']}` at {f['time']}s: {f['shows']}" for f in tech["frames"]]
    L += [f"- `{c['file']}` at {c['time']}s: original camera vs final, {c['kind']} {c['angle']}" for c in tech.get("compares", [])]
    if a.notes:
        L += ["", f"**What the agent saw:** {a.notes}"]
    L += ["", "## Decision", ""]
    if passed:
        L += [f"**PASS.** Staged at `{report['staged']}`. Waiting for Alfonso's final yes. Nothing has been posted."]
        if notes_for_alfonso:
            L += ["", "Alfonso, before you say yes:"] + [f"- {c['check']}: {c['detail']}" for c in notes_for_alfonso]
    else:
        L += ["**FAIL.** Not staged. Send back to:", ""]
        L += [f"- **{AGENT[s['to']]}:** {s['fix']}" for s in send_back]
    (OUT / "qa_report.md").write_text("\n".join(L) + "\n")

    print(f"VERDICT: {report['verdict']}")
    if passed:
        print(f"staged {report['staged']} - waiting for Alfonso's yes" + (" (and his own-footage confirmation)" if ask_owner else ""))
    for s in send_back:
        print(f"SEND BACK to {AGENT[s['to']]}: {s['fix']}")
    print(f"report: {rel(OUT / 'qa_report.md')}")


if __name__ == "__main__":
    main()
