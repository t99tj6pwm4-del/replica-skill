#!/usr/bin/env python3
"""FINAL APPROVAL AGENT tool, step 1 of 2. Measures the final video. Edits nothing, posts nothing.

    python3 scripts/qa_check.py

Checks output/final_edit.mp4 with ffprobe (streams, size, fps, codecs, length), audio level,
on-screen text rules, duplicate-of-a-posted-video, and where the footage came from.
Saves 3 frames to output/qa/frame_1.jpg .. frame_3.jpg for the agent to look at,
and the measurements to output/qa/tech.json. Then run scripts/qa_verdict.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (FPS, H, INPUT, OUT, W, WORK, find_duplicate, load_json, probe, rel, resolve, run,  # noqa: E402
                    save_json, sha256)


def main():
    final = OUT / "final_edit.mp4"
    checks = []

    def add(name: str, ok: bool, detail: str, owner: str, soft: bool = False):
        # soft = does not fail the video, but Alfonso is told about it at approval
        checks.append({"check": name, "pass": bool(ok), "detail": detail, "owner": owner, "soft": soft})

    if not final.exists():
        add("final video exists", False, "output/final_edit.mp4 is missing", "text_visuals")
        save_json(OUT / "qa" / "tech.json", {"checks": checks, "frames": []})
        print("FAIL: output/final_edit.mp4 is missing")
        sys.exit(0)

    sb = load_json(OUT / "storyboard.json", default={})
    job = load_json(OUT / "job.json", default={})
    props = load_json(WORK / "overlay_props.json", default={})
    cut = OUT / "cut_version.mp4"
    info = probe(final)
    v, a = info["video"], info["audio"]
    cut_info = probe(cut) if cut.exists() else None

    def owner(cut_ok: bool) -> str:  # a fault already present in the cut belongs to the Cuts Agent
        return "text_visuals" if cut_ok else "cuts"

    add("video stream present", v is not None, f"{v['codec']}" if v else "none", "text_visuals")
    add("audio stream present", a is not None, f"{a['codec']} {a['sample_rate']}Hz" if a else "none",
        owner(bool(cut_info and cut_info["audio"])))
    if v:
        cv = cut_info["video"] if cut_info else None
        add("1080x1920 vertical", (v["width"], v["height"]) == (W, H), f"{v['width']}x{v['height']}",
            owner(bool(cv and (cv["width"], cv["height"]) == (W, H))))
        add("30 fps", abs(v["fps"] - FPS) < 0.01, f"{v['fps']} fps", owner(bool(cv and abs(cv["fps"] - FPS) < 0.01)))
        add("H.264 video", v["codec"] == "h264", v["codec"], "text_visuals")
    if a:
        add("AAC audio", a["codec"] == "aac", a["codec"], "cuts")
        vol = run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                  check=False).stderr
        m = re.search(r"mean_volume: ([-\d.]+) dB", vol)
        mean = float(m.group(1)) if m else -91.0
        # compare with the raw video: a quiet source is Alfonso's sound, not a broken edit
        src_level = None
        if sb.get("source") and resolve(sb["source"]).exists():
            sv = run(["ffmpeg", "-hide_banner", "-nostats", "-i", resolve(sb["source"]), "-vn", "-af", "volumedetect",
                      "-f", "null", "-"], check=False).stderr
            sm = re.search(r"mean_volume: ([-\d.]+) dB", sv)
            src_level = float(sm.group(1)) if sm else None
        rule = load_json(WORK / "audio_rule.json", default={})
        if rule.get("muted"):
            add("audio muted by Alfonso's rule (always mute baked-in music)", True,
                f"mean {mean:.1f} dB; {rule.get('reason', '')}", "cuts")
            add("sound muted: add a sound in the Instagram/Facebook app or one of your songs", False,
                "the video has no sound", "cuts", soft=True)
        elif mean > -50:
            add("audio is not silent", True, f"mean {mean:.1f} dB", "cuts")
        elif src_level is not None and src_level <= -45:
            add("audio is not silent", False, f"mean {mean:.1f} dB; the raw video is quiet too ({src_level:.1f} dB). "
                "Add one of your songs to songs/ for music", "cuts", soft=True)
        else:
            add("audio is not silent", False, f"mean {mean:.1f} dB but the raw video is {src_level} dB", "cuts")
    lo, hi = sb.get("min_duration", 60), sb.get("max_duration", 90)
    add(f"length {lo}-{hi}s", lo <= info["duration"] <= hi, f"{info['duration']:.2f}s", "cuts")
    if cut_info:
        add("same length as the cut", abs(cut_info["duration"] - info["duration"]) < 0.2,
            f"cut {cut_info['duration']:.2f}s, final {info['duration']:.2f}s", "text_visuals")

    # on-screen text rules
    texts = []

    def walk(n):
        if isinstance(n, dict):
            for k, x in n.items():
                if k not in ("brand", "kind"):
                    walk(x)
        elif isinstance(n, list):
            for x in n:
                walk(x)
        elif isinstance(n, str):
            texts.append(n)

    walk({k: x for k, x in props.items() if k != "popups"})
    bad = [t for t in texts if "#" in t or re.search(r"[^\x20-\x7E]", t)]
    # approved exception (Alfonso, 2026-11-17): the pop-up cards' Spanish lines may use Spanish letters and •
    from add_popups import build_popups, is_song_video, no_text_windows, popup_text_ok
    pop_texts = []
    if props.get("popups"):
        texts_before = len(texts)
        walk(props["popups"])
        pop_texts = texts[texts_before:]
        bad += [t for t in pop_texts if not popup_text_ok(t)]
    add("English only, no hashtags on screen (Spanish allowed in pop-ups)", not bad and bool(props),
        f"{len(texts)} text items checked ({len(pop_texts)} in pop-ups)" if not bad else f"bad: {bad[:5]}",
        "text_visuals")

    # pop-up cards (Alfonso, 2026-11-17): every gym reel, never a song video
    pops = props.get("popups") or {}
    lifts = sorted(sb.get("lifts") or [], key=lambda l: float(l.get("cut_start", 0)))
    if is_song_video(sb):
        add("song video: no pop-up cards", not pops.get("bars") and not pops.get("formTip") and not pops.get("checklists"),
            "none" if not pops else "pop-ups present on a song video", "text_visuals")
    elif lifts:
        bars, lists, tip = pops.get("bars") or [], pops.get("checklists") or [], pops.get("formTip")
        names = [l["name"].strip() for l in lifts]
        bar_names = [b["title"] for b in bars]
        add("pop-up: one Exercise Bar per lift", bar_names == [n.upper() for n in names],
            f"{len(bars)} bars for {len(lifts)} lifts" + ("" if bar_names == [n.upper() for n in names]
                                                          else f": bars {bar_names} vs lifts {names}"), "text_visuals")
        want, _ = build_popups(sb, float(props.get("duration", info["duration"])), props)
        want_detail = [b["detail"] for b in (want or {}).get("bars", [])]
        add("pop-up: bars show the routine's sets x reps + Spanish name (no invented lift)",
            [b["detail"] for b in bars] == want_detail, " | ".join(b["detail"] for b in bars) or "none", "text_visuals")
        okl = (len(lists) == len(lifts) - 1 and all(c.get("items") == names and c.get("current") == i
                                                    for i, c in enumerate(lists, 1)))
        add("pop-up: a Routine Checklist on every lift after the first", okl,
            f"{len(lists)} checklists for {len(lifts) - 1} lifts after the first"
            + ("" if okl else " (items must be the lifts in order, current = the lift on screen)"), "text_visuals")
        okt = bool(tip and tip.get("cue") and tip.get("lift", "").lower() in [n.lower() for n in names])
        add("pop-up: exactly one Form Tip, tied to a lift in the video", okt,
            f"{tip['lift']}: {tip['cue']} / {tip.get('cueEs', '')} at {tip['from']:.2f}-{tip['to']:.2f}s" if tip
            else "missing", "text_visuals")
        wins = no_text_windows(sb, props)
        spans = [("bar " + b["title"], b) for b in bars] + [(f"checklist {c['current']}", c) for c in lists]
        spans += [("form tip", tip)] if tip else []
        hits = [f"{n} {x['from']:.2f}-{x['to']:.2f}s vs {a:.2f}-{b:.2f}s" for n, x in spans for a, b in wins
                if x["from"] < b + 0.1 - 1e-3 and a - 0.1 + 1e-3 < x["to"]]
        add("pop-ups stay out of the no-text windows (0.1s margin)", not hits,
            f"{len(spans)} pop-ups, {len(wins)} windows" if not hits else "; ".join(hits[:4]), "text_visuals")
    elif any(s.get("type") == "exercise" for s in sb.get("segments", [])):
        add("pop-up cards planned (storyboard \"lifts\" + \"form_tip\")", False,
            "gym reel without \"lifts\" in the storyboard: no pop-ups", "storyboard", soft=True)
    lt = load_json(WORK / "layered_title.json", default={})
    plus = props.get("title_style") == "layered-gold-plus"
    if props.get("title_style") in ("layered-gold", "layered-gold-plus") and lt:
        if not plus:
            # Layered Title (Documentary Gold): ONLY that title, nothing else on screen
            extra = [k for k in ("title", "captions", "lowerThirds", "callouts", "endCard", "progress") if props.get(k)]
            add("layered title only: no subtitles, captions, lower-thirds, title card or end card", not extra,
                "none present" if not extra else f"still present: {', '.join(extra)}", "text_visuals")
        cov = lt.get("first_name_covered_by_person")
        add(f"{lt['first']} sits BEHIND him (part of the letters hidden by his body)", bool(cov and cov > 0.02),
            f"{(cov or 0) * 100:.0f}% of the first name is covered by him", "text_visuals")
        add(f"layered title {lt['first']} / {lt['intro_line']} / {lt['last']}", True,
            f"{lt['at']:.2f}-{lt['at'] + lt['dur']:.2f}s, gold {lt['gold']}, 90% width; frame {lt['frame']}", "text_visuals")
        logf = OUT / "effects_log.md"
        add("title style logged in output/effects_log.md", logf.exists() and "Layered Title" in logf.read_text(),
            "logged" if logf.exists() else "missing", "text_visuals")
    if props.get("title_style") != "layered-gold" or not lt:
        ex_titles = load_json(WORK / "exercise_titles.json", default=[]) if props.get("exercise_titles") else []
        if ex_titles:
            # front_only titles (Director's call when no back word can be read behind him) need no cover
            behind = [t for t in ex_titles if t.get("front_only")
                      or 0.02 < (t.get("first_name_covered_by_person") or 0) <= 0.45]
            add("exercise names as gold layered titles (back word partly behind him, still readable)",
                len(behind) == len(ex_titles),
                f"{len(behind)}/{len(ex_titles)} have the back word 2-45% covered by him; "
                + "; ".join(f"{t['first']} {t['last']} {(t.get('first_name_covered_by_person') or 0) * 100:.0f}%"
                            if not t.get("front_only") else f"{t['first']} {t['last']} front-only"
                            for t in ex_titles) + "; frames: "
                + ", ".join(t["frame"] for t in ex_titles), "text_visuals")
        need = {"title card": props.get("title"), "lower-thirds": props.get("lowerThirds") or ex_titles,
                "progress bar": props.get("progress"), "end card": props.get("endCard")}
        missing = [k for k, x in need.items() if not x]
        add("title card, lower-thirds, progress bar, end card present", not missing,
            "all present" if not missing else f"missing: {', '.join(missing)}", "text_visuals")
        n_words = sum(len(p["words"]) for p in props.get("captions", []))
        spoken = len(load_json(WORK / "transcript.json", default={"words": []})["words"])
        if spoken >= 3:
            add("word-by-word captions present", n_words > 0, f"{n_words} caption words for {spoken} spoken", "text_visuals")
        else:
            add("word-by-word captions present", n_words > 0, "no speech in the video, so there is nothing to caption",
                "text_visuals", soft=True)

    # duplicate + footage origin
    src = resolve(sb["source"]) if sb.get("source") else None
    src_sha = sha256(src) if src and src.exists() else None
    dup = find_duplicate(final, src_sha)
    add("not a duplicate of a posted video", dup is None,
        "no match in posted/ledger.json" if dup is None else f"{dup['match']}: posted {dup.get('posted_at')}", "director")
    in_input = bool(src and src.exists() and INPUT.resolve() in src.resolve().parents)
    ext = load_json(OUT / "extended" / "extend.json", default={})
    if not in_input and ext and src and rel(src) == ext.get("extended"):
        base = resolve(ext["base"])
        ok = base.exists() and INPUT.resolve() in base.resolve().parents and sha256(base) == ext.get("base_sha256")
        add("footage comes from input/ only", ok, f"{ext['base']} extended with {ext['generator']}", "director")
        ai_s, rep_s = ext.get("ai_seconds", 0), ext.get("replay_seconds", 0)
        if ai_s > 0:
            add("no AI-made footage", False, f"{ext['real_seconds']:.1f}s real + {ai_s:.1f}s generated by "
                f"{ext['generator']} at Alfonso's request; label it as AI-assisted when posting", "director", soft=True)
        else:
            add("no AI-made footage", True, f"{ext['real_seconds']:.1f}s clip + {rep_s:.1f}s replays of the same "
                "real reps (free-local, $0)", "director")
    else:
        add("footage comes from input/ only", in_input, sb.get("source", "unknown"), "director")
    confirmed = job.get("own_footage_confirmed", "unknown")
    add("Alfonso confirmed it is his own footage", confirmed == "yes",
        {"yes": "confirmed in the brief", "no": "brief says this is NOT his footage",
         "unknown": "not confirmed yet: ask Alfonso at approval"}.get(confirmed, confirmed), "director",
        soft=confirmed == "unknown")

    # multicam / B-roll: audio is the truth, cuts on the beat of the speech, never mid-word
    mmap = load_json(WORK / "multicam_map.json", default={})
    inserts = mmap.get("inserts", [])
    mc_video = OUT / "multicam_version.mp4"
    step = job.get("steps", {}).get("multicam", {}).get("status")
    if step == "done" or inserts:
        add("multicam prompt written", (OUT / "multicam_prompt.txt").exists(), "output/multicam_prompt.txt", "multicam")
        add("multicam version exists", mc_video.exists() and bool(inserts), f"{len(inserts)} shots cut in", "multicam")
    if inserts and mc_video.exists():
        add("original audio untouched (audio is the truth)", mmap.get("audio_identical_to_cut") is True,
            "audio identical to the cut" if mmap.get("audio_identical_to_cut") else "audio differs from the cut", "multicam")
        words = load_json(WORK / "transcript.json", default={"words": []})["words"]
        times = sorted({t for i in inserts for t in (i["from"], i["to"])})
        mid = [t for t in times if any(w["start"] + 0.02 < t < w["end"] - 0.02 for w in words)]
        add("angle cuts never mid-word", not mid, f"{len(times)} cuts checked against {len(words)} words"
            if not mid else f"mid-word at {mid}", "multicam")
        # where does the picture really change? measure it and compare with the plan
        import subprocess
        import numpy as np
        worst, detail = 0.0, []
        base_cut = OUT / "cut_version.mp4"
        # an AI image-to-video clip starts FROM the original frame, so the picture change shows up late on the
        # detector; its cut-in is placed exactly (see the slot-length check), so only its cut-out is measured
        ai_in = {i["from"] for i in inserts if i.get("ai") and not i.get("simulated")}
        ai_skipped = sorted(t for t in times if t in ai_in)
        times = [t for t in times if t not in ai_in]

        def frame_diffs(video, a0):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a0:.3f}", "-t", "1.0", "-i", str(video), "-vf",
                                  f"fps={FPS},scale=48:86,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
            fr = np.frombuffer(raw, dtype=np.uint8)
            n = len(fr) // (48 * 86)
            if n < 3:
                return None
            return np.abs(np.diff(fr[: n * 48 * 86].reshape(n, 86, 48).astype(np.float32), axis=0)).mean(axis=(1, 2))

        for t in times:
            a0 = max(0.0, t - 0.5)
            d = frame_diffs(mc_video, a0)
            if d is None:
                continue
            # ignore picture changes that are already in the cut (its own jump cuts), so only the angle cut counts
            b = frame_diffs(base_cut, a0) if base_cut.exists() else None
            if b is not None:
                k = min(len(d), len(b))
                d = np.clip(d[:k] - b[:k], 0, None)
            actual = a0 + (int(np.argmax(d)) + 1) / FPS
            worst = max(worst, abs(actual - t))
            detail.append(f"{t:.2f}s->{actual:.2f}s")
        add("cut timing within 0.2s of the plan", worst <= 0.2, f"worst drift {worst:.2f}s ({', '.join(detail)})"
            + (f"; AI cut-ins not measured (clip starts from the original frame): {ai_skipped}" if ai_skipped else ""),
            "multicam")
        slot = [i for i in inserts if abs(probe(resolve(i["clip"]))["duration"] - (i["to"] - i["from"])) > 0.05]
        add("each generated clip fills its slot exactly (lip sync cannot drift)", not slot,
            "all clips match their slot length" if not slot else f"wrong length: {[i['id'] for i in slot]}", "multicam")
        plan = load_json(WORK / "multicam_plan.json", default={})
        pf = OUT / "multicam_prompt.txt"
        if pf.exists():
            import hashlib
            same = hashlib.sha256(pf.read_text().encode()).hexdigest() == plan.get("frozen_sha256")
            add("multicam prompt frozen (unchanged since generation started)", same,
                "matches the frozen copy" if same else "multicam_prompt.txt was edited after generation", "multicam")
        if mmap.get("provider") == "google-flow":
            angles = [i for i in inserts if i["kind"] == "multicam"]
            add("4 Google Flow shots cut in", len(angles) == 4,
                ", ".join(f"#{i.get('shot', i['angle'])}@{i['from']:.2f}s" for i in angles), "multicam")
            low = [i["id"] for i in inserts if (i.get("returned_height") or 0) < 720 and (i.get("returned_width") or 0) < 720]
            add("Flow clips are 720p or better", not low, "all 720p+" if not low else f"below 720p: {low}", "multicam")
        shots = [i for i in inserts if i.get("shot")]
        if shots:
            cats = [i["category"] for i in shots]
            add("library shots from different categories", len(set(cats)) == len(cats),
                ", ".join(f"#{i['shot']} ({i['category']})" for i in shots), "multicam")
            logf = OUT / "multicam_shots_log.md"
            logged = logf.exists() and all(f"#{i['shot']} " in logf.read_text().splitlines()[-1] for i in shots)
            add("shots logged in output/multicam_shots_log.md", logged,
                "logged" if logged else "the last log row does not list these shots", "multicam")
        add("no dropped or rewritten words (original audio kept bit for bit)",
            mmap.get("audio_identical_to_cut") is True, "audio identical to the cut", "multicam")
        n_ai = sum(1 for i in inserts if not i.get("simulated"))
        add("angles made by the AI generator", n_ai == len(inserts),
            f"{n_ai} of {len(inserts)} shots are AI-generated ({mmap.get('provider')}); the rest are free-local crops "
            "of the real footage" if n_ai < len(inserts) else f"all {n_ai} shots AI-generated ({mmap.get('provider')})",
            "multicam", soft=True)

    # CapCut-library effects: list every one with its duration, re-check the rules
    fx = load_json(WORK / "effects_applied.json", default={})
    if fx:
        import effects as fxmod
        plan = load_json(WORK / "effects_plan.json", default={})
        errs, _, _ = fxmod.validate(plan, load_json(WORK / "cut_map.json"), job.get("video", ""), strict=False)
        add("effects follow the library rules (1 filter, durations, max per clip, no cartoon / reshape / Pro)",
            not errs, "all rules met" if not errs else "; ".join(errs), "text_visuals")
        add("filter (one, whole video)", bool(fx.get("filter")), str(fx.get("filter")), "text_visuals")
        for i in fx["items"]:
            add(f"{i['group'][:-1].replace('_', ' ')}: {i['name']}", True,
                f"{i['dur']}s at {i['from']:.2f}-{i['to']:.2f}s (ffmpeg equivalent)" + (f", {i['why']}" if i.get("why") else ""),
                "text_visuals")
        if fx.get("title_animation"):
            add(f"title animation in: {fx['title_animation']}", True, "hook title, first 2s", "text_visuals")
        hero = [e for e in load_json(WORK / "cut_map.json").get("events", []) if e["kind"] == "hero"]
        for e in hero:
            add("speed curve: Hero", True, f"{e['out_start']:.2f}-{e['out_end']:.2f}s, slow-to-fast", "cuts")
        logf = OUT / "effects_log.md"
        add("effects logged in output/effects_log.md", logf.exists() and job.get("video", "?") in logf.read_text(),
            "logged" if logf.exists() else "missing", "text_visuals")

    # 3 frames: animated captions, a multicam angle change, a punch-in (or lower-third)
    dur = info["duration"]
    body_end = (props.get("endCard") or {}).get("from", dur)
    picks = []
    allcaps = props.get("captions", [])

    def cap_time(c):   # a moment when the page's last word has just popped in
        return min(c["words"][-1]["start"] + 0.15, c["end"] - 0.05)

    def inside(t, spans):
        return any(s["from"] <= t <= s["to"] for s in spans)

    shot_ins = [i for i in inserts if i.get("shot")]
    if len(shot_ins) >= 3:
        # 3 frames from 3 different library shots, each with animated captions on screen where possible
        for ins in shot_ins[:3]:
            hit = [cap_time(c) for c in allcaps if ins["from"] + 0.3 <= cap_time(c) <= ins["to"] - 0.1]
            picks.append((f"shot #{ins['shot']} {ins['shot_text']} ({ins['category']})"
                          + (" + animated captions" if hit else ""),
                          hit[0] if hit else ins["from"] + (ins["to"] - ins["from"]) * 0.4))
    caps = [c for c in allcaps if not inside(cap_time(c), inserts)]
    if caps and len(picks) < 3:
        picks.append(("animated word-by-word captions", cap_time(caps[len(caps) // 2])))
    if inserts and len(picks) < 3:
        ins = inserts[0]
        hit = [cap_time(c) for c in allcaps if ins["from"] + 0.3 <= cap_time(c) <= ins["to"] - 0.1]
        picks.append((f"multicam angle change ({ins['angle']})", hit[0] if hit else ins["from"] + (ins["to"] - ins["from"]) * 0.4))
    punches = [e for e in props.get("events", []) if e["kind"] == "punch_in"]
    lts = props.get("lowerThirds") or []
    if len(picks) >= 3:
        pass
    elif punches:
        p = punches[len(punches) // 2]
        picks.append(("punch-in (zoomed)", (p["from"] + p["to"]) / 2))
    elif lts:
        picks.append(("lower-third on screen", lts[0]["from"] + 1.6))
    for frac in (0.3, 0.55, 0.8):
        if len(picks) < 3:
            picks.append(("mid-video", body_end * frac))
    qdir = OUT / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, (what, t) in enumerate(picks[:3], 1):
        out = qdir / f"frame_{i}.jpg"
        t = max(0.0, min(t, dur - 0.1))
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", final, "-frames:v", "1", "-q:v", "2", out])
        frames.append({"file": rel(out), "time": round(t, 2), "shows": what})

    # side by side: original camera | what is in the final, at the same instant (lip sync, B-roll match)
    compares = []
    for old in qdir.glob("compare_*.jpg"):
        old.unlink()
    for ins in inserts:
        words_in = [w for w in load_json(WORK / "transcript.json", default={"words": []})["words"]
                    if ins["from"] + 0.2 < (w["start"] + w["end"]) / 2 < ins["to"] - 0.2]
        t = (words_in[len(words_in) // 2]["start"] + words_in[len(words_in) // 2]["end"]) / 2 if words_in else (ins["from"] + ins["to"]) / 2
        out = qdir / f"compare_{ins['id']}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", cut, "-ss", f"{t:.3f}", "-i", final, "-filter_complex",
             "[0:v]scale=540:960[a];[1:v]scale=540:960[b];[a][b]hstack", "-frames:v", "1", "-q:v", "3", out])
        compares.append({"file": rel(out), "time": round(t, 2), "id": ins["id"], "kind": ins["kind"], "angle": ins["angle"],
                         "note": ins.get("note", ""), "speaking": bool(words_in)})

    save_json(qdir / "tech.json", {"compares": compares, "final": rel(final), "sha256": sha256(final), "source_sha256": src_sha,
                                   "probe": info, "checks": checks, "frames": frames})
    for c in checks:
        print(f"{'PASS' if c['pass'] else ('NOTE' if c['soft'] else 'FAIL')}  {c['check']:<58} {c['detail']}")
    print("\nNow LOOK at these 3 frames, then run scripts/qa_verdict.py:")
    for f in frames:
        print(f"  {f['file']}  ({f['time']}s, {f['shows']})")
    if compares:
        print("\nAnd these side-by-sides (LEFT = original camera, RIGHT = final, same instant):")
        for c in compares:
            print(f"  {c['file']}  ({c['time']}s, {c['kind']} {c['angle']}" + (f", asked for: {c['note']}" if c["note"] else "")
                  + (", he is speaking here: compare the mouths" if c["speaking"] else "") + ")")


if __name__ == "__main__":
    main()
