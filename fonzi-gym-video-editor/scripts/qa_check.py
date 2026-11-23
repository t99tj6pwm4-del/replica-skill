#!/usr/bin/env python3
"""FINAL APPROVAL AGENT tool, step 1 of 2. Measures the final video. Edits nothing, posts nothing.

    python3 scripts/qa_check.py
    python3 scripts/qa_check.py --final output/intro_test/final_edit_test.mp4   # check a test render instead;
        # its frames + tech.json go to <that folder>/qa/ so output/qa/ (the staged video's QA) is untouched

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
from common import (load_config, FPS, H, INPUT, OUT, W, WORK, find_duplicate, load_json, probe, rel, resolve, run,  # noqa: E402
                    save_json, sha256)


ROOT_BRAND = Path(__file__).resolve().parent.parent / "config" / "brand.json"
INTRO_STYLES = ("strobe", "pulse", "glitch", "smash")   # finish_fx.ALL_INTRO_STYLES (Round 7, 2026-11-22)
LOGO_STYLES = ("flat", "3d")
TITLE_MAX_RGB = (0xEC, 0xD4, 0x97)                      # GOLD look (shipped default): title never brighter than #ECD497
# Alfonso 2026-11-23 (answer 24): with the white look ON (config text_look.enabled / --text-look white) the gold
# ceiling does not apply: text must be white / neutral (no tint) and there must be no box behind it.
SPLIT_ALPHA_MAX = 0.6                                   # glitch split copies
SMASH_MIN_GAP = 24                                      # smash scatter: never a glyph gap < 24 px
LOGO_ON_FACE_SOFT = 2500                                # soft: a window sum (3 s windows go over it)


def intro_checks(ir: dict, fin: dict | None = None) -> list[dict]:
    """The Round 7 intro checks from the finish_fx.json entry (fin) and its intro report (ir). Hard unless soft.
    Entries from before round 7 lack the new keys: missing logo_style = flat, glitch / smash missing = not used,
    logo_box_max / title_max_rgb missing = not measured (pass)."""
    fin = fin or {}
    out = []

    def c(name, ok, detail, soft=False):
        out.append({"check": name, "pass": bool(ok), "detail": detail, "soft": soft})

    style, logo = ir.get("style"), ir.get("logo_style") or "flat"
    if style == "video_text":                     # Director answer 25: the video-inside-text intro
        return video_text_checks(ir, fin)
    c("intro title style is one of the 4", style in INTRO_STYLES, f"{style} ({' | '.join(INTRO_STYLES)})")
    c("intro logo style is flat or 3d", logo in LOGO_STYLES, f"{logo} ({' | '.join(LOGO_STYLES)})")
    box = ir.get("logo_box_max")
    inside = box is None or (len(box) == 4 and box[0] >= 0 and box[1] >= 0 and box[2] <= W and box[3] <= H)
    c("intro logo fully inside the frame", ir.get("logo_edge_px", 0) == 0 and inside,
      f"edge px {ir.get('logo_edge_px', 0)}, logo box over the window {box if box else 'not logged (pre round 7)'}"
      f" in {W}x{H}, scale {ir.get('logo_scale', 1.0)}")
    gl = ir.get("glitch")
    if style == "glitch" or gl:
        ok = bool(gl) and gl.get("split_px_inside_letters", 1) == 0 and \
            float(gl.get("split_alpha_max", 1)) <= SPLIT_ALPHA_MAX
        c("glitch split on the letter edges only", ok,
          f"split px inside the letters {gl.get('split_px_inside_letters')}, split alpha max "
          f"{gl.get('split_alpha_max')} (<= {SPLIT_ALPHA_MAX}), offset max {gl.get('split_offset_max_px')} px, "
          f"frames {gl.get('frames')}" if gl else "style glitch but no glitch stats logged")
    sm = ir.get("smash")
    if style == "smash" or sm:
        ok = bool(sm) and sm.get("min_glyph_gap_px") is not None and float(sm["min_glyph_gap_px"]) >= SMASH_MIN_GAP
        c(f"smash letters never closer than {SMASH_MIN_GAP} px", ok,
          f"min glyph gap {sm.get('min_glyph_gap_px')} px, keep-out {sm.get('keep_out')} "
          f"({sm.get('keep_out_source')}), scatter shrink {sm.get('scatter_shrink')}, lands on frame "
          f"{sm.get('land_frame')}" if sm else "style smash but no smash stats logged")
    import text_look as TL
    lim = int(TL.look()["neutral_max_spread"])
    rgb = ir.get("title_max_rgb")
    if (ir.get("title_rgb") or "").upper() != TL.look()["color"].upper():      # the GOLD look (shipped default)
        if rgb is not None:
            ok = all(int(v) <= m for v, m in zip(rgb, TITLE_MAX_RGB))
            c("title never brighter than #ECD497", ok,
              f"brightest title pixel {list(rgb)} ({'ok' if ok else 'over #ECD497'}"
              f"{'' if style == 'glitch' else ', window max incl. pulse frames: note only'})", soft=style != "glitch")
    elif "title_tint_spread_max" in ir:
        sp = int(ir["title_tint_spread_max"])
        c("intro title is white (no tint, text_look)", sp <= lim and (ir.get("title_rgb") or "#FFFFFF") == TL.look()["color"],
          f"title {ir.get('title_rgb')}, max R-G-B spread over the window {sp} (<= {lim}), brightest "
          f"{ir.get('title_max_rgb')}, glow / shadow px on his face {ir.get('glow_on_face_px_max', 0)}")
    else:
        c("intro title is white (no tint, text_look)", False,
          f"intro rendered before the white look (title max rgb {ir.get('title_max_rgb')}): re-render", soft=True)
    face = ir.get("logo_on_face_px_max")
    if face is not None:
        c(f"logo on his face edge <= {LOGO_ON_FACE_SOFT} px (window sum)", face <= LOGO_ON_FACE_SOFT,
          f"{face} px over the window (report only)", soft=True)
    fb = fin.get("fallback_reason")
    if fb or (fin.get("intro_planned") and fin.get("intro_planned") != style):
        c("intro style as planned by the rotation", False,
          f"planned {fin.get('intro_planned')}, rendered {style}: {fb or 'fallback'}", soft=True)
    return out


def video_text_checks(ir: dict, fin: dict | None = None) -> list[dict]:
    """Director answer 25: the video-inside-text intro (style_fx intro --style video_text). All from its report,
    which style_fx measured on the frames it wrote."""
    out = []

    def c(name, ok, detail, soft=False):
        out.append({"check": name, "pass": bool(ok), "detail": detail, "soft": soft})
    words = ir.get("title") or []
    c("video-text intro: title 1-2 words, ALL CAPS", 1 <= len(words) <= 2 and all(w == w.upper() for w in words),
      " / ".join(words))
    d = float(ir.get("dur") or 0)
    c("video-text intro is 2.6 s (never over 3 s)", abs(d - 2.6) < 0.04 or (ir.get("scaled_reason") and d <= 3.0),
      f"{d:.2f}s{' (scaled: ' + ir['scaled_reason'] + ')' if ir.get('scaled_reason') else ''}",
      soft=bool(ir.get("scaled_reason")))
    c("video-text intro never over 3 s", d <= 3.0 + 1e-6, f"{d:.2f}s")
    ob = ir.get("outside_letters_max_value_0_1_8")
    c("outside the letters is black during 0-1.8 s", ob is not None and ob <= 2, f"max pixel value outside {ob}")
    lu = ir.get("through_letters_luma_min")
    c("his footage shows through the letters", lu is not None and lu >= 0.08,
      f"luma through the letters min {lu} (raw {ir.get('through_letters_luma_raw')}, letters-only gain "
      f"{ir.get('brighten_gain_letters_only')})")
    sp, gone, n = ir.get("split_from_s"), ir.get("matte_gone_frame"), ir.get("frames")
    c("split on time and the matte fully gone by the end", sp is not None and gone is not None and gone <= n - 1
      and float(ir.get("cover_at_split_start", 0)) >= 0.5,
      f"split from {sp}s, black cover at the split {ir.get('cover_at_split_start')}, matte gone at frame {gone} of {n}")
    j = ir.get("last_frame_vs_footage_mean_abs")
    c("no jump after the intro (last frame = the footage)", j is not None and j <= 0.5, f"mean abs diff {j}")
    return out


OPENER_DUR = (0.9, 2.5)                                 # seconds: ~1.5 s on the beat grid (config intro.opener)


def _frame_gray(video: Path, t: float):
    import numpy as np
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-vf",
                          f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8)
    return a[: W * H].reshape(H, W).astype(np.float32) / 255 if a.size >= W * H else None


def opener_checks(fin: dict, ir: dict, final: Path) -> list[dict]:
    """Logo opener (Alfonso 2026-11-23, answer 23): ~1.5 s of the end-card look before the intro. Checks: it exists
    (or finish_fx logged why not: soft), it lasts ~1.5 s and ends on the beat, the logo is fully in frame, the
    intro starts after it (window and beat 1), and a real frame of the final looks like it (dark blurred footage,
    white logo)."""
    out = []

    def c(name, ok, detail, soft=False):
        out.append({"check": name, "pass": bool(ok), "detail": detail, "soft": soft})

    on = (load_config().get("intro") or {}).get("opener") or {}
    op = fin.get("opener")
    if not op:
        why = fin.get("opener_fallback_reason")
        if not on.get("enabled", True):
            return out
        if why:
            c("logo opener before the intro (end-card look, ~1.5 s)", False, f"not baked in: {why}", soft=True)
        elif not fin.get("opener_checked"):
            c("logo opener before the intro (end-card look, ~1.5 s)", False,
              "finished before the opener rule (2026-11-23): re-render with scripts/render_final.py", soft=True)
        else:
            c("logo opener before the intro (end-card look, ~1.5 s)", False, "finish_fx.py logged no opener and no "
              "reason", soft=False)
        return out
    dur = float(op.get("dur") or 0)
    c("logo opener before the intro (end-card look, ~1.5 s)",
      OPENER_DUR[0] <= dur <= OPENER_DUR[1] and op.get("from", 0) == 0,
      f"0-{dur:.2f}s = {op.get('beats')} beats (planned {op.get('planned_beats')}), ends on the beat at "
      f"{op.get('end_beat_s')}s, {op.get('drips')} drips, logo solid on frame {op.get('solid_frame')}"
      f"{' on the beat' if op.get('solid_on_beat') else ''}")
    box = op.get("logo_box") or []
    inside = len(box) == 4 and box[0] >= 0 and box[1] >= 110 and box[2] <= W and box[3] <= H - 420
    c("opener logo fully inside the frame", inside and op.get("logo_edge_px", 1) == 0,
      f"logo box {box} in {W}x{H} (safe band 110-{H - 420}), edge px {op.get('logo_edge_px')}")
    of = int(op.get("frames") or 0)
    st = int(ir.get("start_frame") if ir.get("start_frame") is not None else -1)
    b1 = (ir.get("beats_abs_s") or [None])[0]
    vt = ir.get("style") == "video_text"          # fixed timeline, no beats: it starts right at the opener's end
    c("intro starts after the opener", st >= of and (vt or (b1 is not None and b1 * FPS > of)),
      f"opener frames 0-{of - 1}, intro window from frame {st} ({ir.get('start')}s), intro beat 1 at {b1}s")
    t = (of - 4) / FPS if of > 8 else 0.5 * dur
    g = _frame_gray(final, t)
    if g is not None and len(box) == 4:
        import numpy as np
        x0, y0, x1, y1 = box
        m = np.ones_like(g, bool)
        m[y0:y1, x0:x1] = False
        bg_mean, white = float(g[m].mean()), float((g[y0:y1, x0:x1] > 0.8).mean())
        c("opener frame: dark blurred footage + white logo", bg_mean < 0.3 and white > 0.02,
          f"frame {t:.2f}s: background mean {bg_mean:.2f} (< 0.30), white logo px {white * 100:.1f}% of its box")
    return out


def main():
    final, qdir = OUT / "final_edit.mp4", OUT / "qa"
    if "--final" in sys.argv:
        final = Path(sys.argv[sys.argv.index("--final") + 1]).resolve()
        qdir = final.parent / "qa"
    checks = []

    def add(name: str, ok: bool, detail: str, owner: str, soft: bool = False):
        # soft = does not fail the video, but Alfonso is told about it at approval
        checks.append({"check": name, "pass": bool(ok), "detail": detail, "owner": owner, "soft": soft})

    if not final.exists():
        add("final video exists", False, "output/final_edit.mp4 is missing", "text_visuals")
        save_json(qdir / "tech.json", {"checks": checks, "frames": []})
        print(f"FAIL: {rel(final)} is missing")
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
    vl = (load_config().get("video_length") or {})
    if vl.get("target_seconds"):
        # Alfonso's hard rule (2026-11-17): every video is 90 seconds
        tgt, tol = float(vl["target_seconds"]), float(vl.get("tolerance_seconds", 1.0))
        add(f"length {tgt:.0f}s (Alfonso's hard rule, +/-{tol:g}s)", abs(info["duration"] - tgt) <= tol,
            f"{info['duration']:.2f}s", "cuts")
    else:
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
                if k not in ("brand", "kind", "textLook"):
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
        wins = no_text_windows(sb, props)
        # a lift lying entirely inside a no-text window (his own baked-in title) correctly gets no cards
        hidden = [i for i, l in enumerate(lifts) if any(a - 0.1 <= float(l["cut_start"]) and float(l["cut_end"]) <= b + 0.1
                                                         for a, b in wins)]
        shown = [i for i in range(len(lifts)) if i not in hidden]
        want_names = [names[i].upper() for i in shown]
        bar_names = [b["title"] for b in bars]
        note = f"; {len(hidden)} lift(s) inside a no-text window get none: {[names[i] for i in hidden]}" if hidden else ""
        add("pop-up: one Exercise Bar per lift", bar_names == want_names,
            f"{len(bars)} bars for {len(shown)} lifts" + note + ("" if bar_names == want_names
                                                              else f": bars {bar_names} vs lifts {want_names}"), "text_visuals")
        want, _ = build_popups(sb, float(props.get("duration", info["duration"])), props)
        want_detail = [b["detail"] for b in (want or {}).get("bars", [])]
        add("pop-up: bars show the routine's sets x reps + Spanish name (no invented lift)",
            [b["detail"] for b in bars] == want_detail, " | ".join(b["detail"] for b in bars) or "none", "text_visuals")
        want_cur = [i for i in shown if i > 0]
        okl = (len(lists) == len(want_cur) and all(c.get("items") == names and c.get("current") == i
                                                   for i, c in zip(want_cur, lists)))
        add("pop-up: a Routine Checklist on every lift after the first", okl,
            f"{len(lists)} checklists for {len(want_cur)} shown lifts after the first" + note
            + ("" if okl else " (items must be the lifts in order, current = the lift on screen)"), "text_visuals")
        okt = bool(tip and tip.get("cue") and tip.get("lift", "").lower() in [n.lower() for n in names])
        add("pop-up: exactly one Form Tip, tied to a lift in the video", okt,
            f"{tip['lift']}: {tip['cue']} / {tip.get('cueEs', '')} at {tip['from']:.2f}-{tip['to']:.2f}s" if tip
            else "missing", "text_visuals")
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
            f"{lt['at']:.2f}-{lt['at'] + lt['dur']:.2f}s, {lt.get('text_rgb') or 'gold ' + str(lt.get('gold'))} "
            f"text_look, 90% width; frame {lt['frame']}", "text_visuals")
        logf = OUT / "effects_log.md"
        add("title style logged in output/effects_log.md", logf.exists() and "Layered Title" in logf.read_text(),
            "logged" if logf.exists() else "missing", "text_visuals")
    if props.get("title_style") != "layered-gold" or not lt:
        ex_titles = load_json(WORK / "exercise_titles.json", default=[]) if props.get("exercise_titles") else []
        if ex_titles:
            # front_only titles (Director's call when no back word can be read behind him) need no cover.
            # Alfonso 2026-11-18: the back word may be mostly hidden, readability is not required
            # (config titles.max_back_cover; it must still be really behind him and not fully gone).
            max_cov = float((load_config().get("titles") or {}).get("max_back_cover", 0.45))
            behind = [t for t in ex_titles if t.get("front_only")
                      or 0.02 < (t.get("first_name_covered_by_person") or 0) <= max_cov]
            add("exercise names as layered titles (back word partly behind him)",
                len(behind) == len(ex_titles),
                f"{len(behind)}/{len(ex_titles)} have the back word 2-{max_cov * 100:.0f}% covered by him; "
                + "; ".join(f"{t['first']} {t['last']} {(t.get('first_name_covered_by_person') or 0) * 100:.0f}%"
                            if not t.get("front_only") else f"{t['first']} {t['last']} front-only"
                            for t in ex_titles) + "; frames: "
                + ", ".join(t["frame"] for t in ex_titles), "text_visuals")
        # Alfonso 2026-11-23 (answer 24): every text white in the glow look, no box. Only when this render used the
        # white look (props.textLook present); the gold look (shipped default) keeps the checks above.
        import text_look as TL
        lk = TL.look()
        white = bool(props.get("textLook"))
        b = load_json(ROOT_BRAND, default={})
        if white:
            okc = props.get("textLook") == TL.for_remotion()
            add("text look: white everywhere (Remotion textLook = config text_look)", okc,
                f"props.textLook {'= config' if okc else 'differs from config text_look: re-render'}", "text_visuals")
        if white and ex_titles:
            nonw = [f"{t['first']} {t['last']}" for t in ex_titles if (t.get("text_rgb") or "") != lk["color"]]
            add("layered exercise titles are white with the glow look", not nonw,
                "all white (back word's glow + shadow behind his cut-out)" if not nonw else f"not white: {nonw}",
                "text_visuals")
        tl_chk = load_json(WORK / "text_look_check.json", default={})
        if not white:
            pass
        elif tl_chk and tl_chk.get("final") == rel(final):
            bad = [r for r in tl_chk.get("samples", []) if not r.get("ok")]
            add("Remotion text white / neutral with no box (measured on the graphics layer)", not bad,
                f"{len(tl_chk['samples'])} frames: max tint spread "
                f"{max((r.get('tint_spread', 0) for r in tl_chk['samples']), default=0)} (<= {lk['neutral_max_spread']}), "
                f"box px {sum(r.get('box_px', 0) for r in tl_chk['samples'])}"
                + (f"; FAIL {bad[:3]}" if bad else ""), "text_visuals")
        else:
            add("Remotion text white / neutral with no box (measured on the graphics layer)", False,
                "no output/work/text_look_check.json for this file (render with scripts/render_final.py)",
                "text_visuals", soft=True)
        need = {"title card": props.get("title") or props.get("opener"),   # Alfonso's own opener image counts as the hook card
                "lower-thirds": props.get("lowerThirds") or ex_titles,
                "progress bar": props.get("progress"), "end card": props.get("endCard")}
        if is_song_video(sb):   # song videos (Director): no lower-thirds or progress bar needed
            need.pop("lower-thirds"); need.pop("progress bar")
        missing = [k for k, x in need.items() if not x]
        # Fonzi style (STYLE.md rule 0 / rule 3): the intro card and the logo end card are baked in by finish_fx.py
        # after the render; they count only if finish_fx.py logged THIS file (same sha256) with a clean intro
        fin = next((e for e in load_json(WORK / "finish_fx.json", default={"finished": []})["finished"]
                    if e.get("sha256") == sha256(final)), None)
        if (props.get("title") or {}).get("style") == "fonzi_intro":
            ir = (fin or {}).get("intro") or {}
            ok = bool(ir.get("ok"))
            vt = ir.get("style") == "video_text"
            add("intro card (video-inside-text)" if vt else "intro card (Rubik Dirt title, logo behind him, title on the beat)", ok,
                (f"video-inside-text: {' / '.join(ir['title'])} {ir.get('start', 0):.2f}-"
                 f"{ir.get('start', 0) + ir['dur']:.2f}s, Montserrat Black {ir.get('size')}px, split at y={ir.get('split_y')}"
                 if ok and vt else
                 f"{ir['style']} title, {ir.get('logo_style') or 'flat'} logo: {' / '.join(ir['title'])} "
                 f"{ir.get('start', 0):.2f}-{ir.get('start', 0) + ir['dur']:.2f}s, beats "
                 f"{ir.get('beats_abs_s') or ir['beats_s']}, text y "
                 f"{ir['text_y_range'][0]}-{ir['text_y_range'][1]} below his face (down to y={ir['face_max_y']}), "
                 f"logo {ir['logo_size'][0]}x{ir['logo_size'][1]} fully in frame, {len(ir['shot_cuts'])} shot cut(s)"
                 if ok else "title.style is fonzi_intro but finish_fx.py did not bake an intro into this file "
                 "(render with scripts/render_final.py, it runs finish_fx.py itself)"), "text_visuals")
            if ok:
                for ic in intro_checks(ir, fin) + opener_checks(fin, ir, final):
                    add(ic["check"], ic["pass"], ic["detail"], "text_visuals", soft=ic["soft"])
            if not ok:
                missing.append("intro card")
        elif props.get("title") and not props.get("opener"):
            add("intro card is the Fonzi intro (STYLE.md rule 0)", False, "the old Remotion hook card is used "
                "(title.style is not fonzi_intro): fine only if Alfonso asked for it", "text_visuals", soft=True)
        if (props.get("endCard") or {}).get("style") == "logo_drip":
            ec = (fin or {}).get("end_card") or {}
            add("logo end card with drips", bool(ec), f"{ec['drips']} drips from {ec['from']:.2f}s" if ec else
                "endCard.style is logo_drip but finish_fx.py did not bake the logo card into this file", "text_visuals")
            if not ec:
                missing.append("logo end card")
        add("title card, lower-thirds, progress bar, end card present" if not is_song_video(sb) else "title card, end card present", not missing,
            "all present" if not missing else f"missing: {', '.join(missing)}", "text_visuals")
        n_words = sum(len(p["words"]) for p in props.get("captions", []))
        spoken = len(load_json(WORK / "transcript.json", default={"words": []})["words"])
        if sb.get("captions") is False:   # storyboard turned captions off (e.g. explicit song lyrics, no dialogue)
            add("word-by-word captions present", n_words == 0, "captions off in the storyboard (captions: false); "
                f"{n_words} caption words rendered", "text_visuals", soft=True)
        elif spoken >= 3:
            add("word-by-word captions present", n_words > 0, f"{n_words} caption words for {spoken} spoken", "text_visuals")
        else:
            add("word-by-word captions present", n_words > 0, "no speech in the video, so there is nothing to caption",
                "text_visuals", soft=True)

    # duplicate + footage origin
    src = resolve(sb["source"]) if sb.get("source") else None
    src_sha = sha256(src) if src and src.exists() else None
    dup = find_duplicate(final, src_sha)
    # a new version Alfonso asked for (job.py replaces <export>) may reuse that export's footage, never its file
    allowed = bool(dup and job.get("replaces") and dup.get("handed_to_alfonso") == job["replaces"]
                   and dup["match"] != "identical file")
    add("not a duplicate of a posted video", dup is None or allowed,
        "no match in posted/ledger.json" if dup is None else
        (f"{dup['match']} as {job['replaces']}: the new version Alfonso asked for" if allowed
         else f"{dup['match']}: posted {dup.get('posted_at')}"), "director")
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
        # frame-exact timing (2026-11-17): every frame inside a slot must be the angle, and the frame just
        # before and just after the slot must still be the cut. Comparing with the cut frame by frame is exact,
        # where guessing cut points from motion confused an AI angle that looks like the original with a cut.
        import subprocess
        import numpy as np
        base_cut = OUT / "cut_version.mp4"

        _all = {}

        def gray_frames(video, f_from, f_to):
            # decode the whole video once (small, grey) and index by frame number: seeking can land a frame off
            if video not in _all:
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "scale=72:128,format=gray",
                                      "-f", "rawvideo", "-"], capture_output=True).stdout
                k = len(raw) // (72 * 128)
                _all[video] = np.frombuffer(raw[: k * 72 * 128], dtype=np.uint8).reshape(k, 128, 72).astype(np.float32)
            return _all[video][max(0, f_from): f_to + 1]

        bad_t, detail = [], []
        if base_cut.exists():
            for i in inserts:
                f0, f1 = round(i["from"] * FPS), round(i["to"] * FPS) - 1
                m = gray_frames(mc_video, f0 - 1, f1 + 1)
                c = gray_frames(base_cut, f0 - 1, f1 + 1)
                k = min(len(m), len(c))
                if k < 3:
                    continue
                d = np.abs(m[:k] - c[:k]).mean(axis=(1, 2))
                outside_ok = d[0] < 2.0 and (k < f1 - f0 + 3 or d[-1] < 2.0)
                inside = d[1:k - 1] if k == f1 - f0 + 3 else d[1:]
                inside_ok = bool(len(inside)) and float(np.median(inside)) >= 2.0
                detail.append(f"{i['id']} {i['from']:.3f}-{i['to']:.3f}s: before/after {d[0]:.1f}/{d[-1]:.1f}, "
                              f"inside median {float(np.median(inside)) if len(inside) else 0:.1f}")
                if not (outside_ok and inside_ok):
                    bad_t.append(i["id"])
        add("cut timing exact (each angle fills its slot frame by frame, the cut on both sides)", not bad_t,
            "; ".join(detail) if not bad_t else f"off: {bad_t}; " + "; ".join(detail), "multicam")
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
