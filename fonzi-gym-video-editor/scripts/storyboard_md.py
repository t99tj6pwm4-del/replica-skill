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
EFFECTS = {"punch_in", "slow_mo", "speed_ramp", "hero", "callout"}
HERO = [0.35, 0.5, 0.75, 1.0]   # Hero speed curve: slow-to-fast, four equal steps
CUT_LOCKS = {"in", "out", "both"}   # cut on motion (2026-11-23): keep this segment's cut(s) exactly as planned


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
        # cut on motion (optional, 2026-11-23): camera angle label + cut locks
        if "angle" in s and not (isinstance(s["angle"], str) and s["angle"].strip()):
            errors.append(f"{name}: 'angle' must be a short label like \"side\" or \"front\"")
        if "cut_lock" in s and s["cut_lock"] not in CUT_LOCKS:
            errors.append(f"{name}: 'cut_lock' must be one of {sorted(CUT_LOCKS)}")
        if s.get("cut_lock") and not s.get("cut_lock_note"):
            warnings.append(f"{name}: cut_lock without 'cut_lock_note': say why this cut may sit on stillness")
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
            if e["type"] == "hero":
                part = (t1 - t0) / len(HERO)
                seg_len += sum(part / s for s in HERO) - (t1 - t0) / float(s.get("speed", 1.0))
                continue
            if e["type"] in ("slow_mo", "speed_ramp"):
                sp = e.get("speed")
                if not sp or not 0.25 <= sp <= 4:
                    errors.append(f"{name}: {e['type']} speed must be 0.25-4")
                else:
                    seg_len += (t1 - t0) / sp - (t1 - t0) / float(s.get("speed", 1.0))
            if e["type"] == "callout":
                english_only(e.get("text", ""), f"{name} callout", errors)
        total += seg_len
    mc = sb.get("motion_cuts")
    if mc is not None and not isinstance(mc, bool):
        if not isinstance(mc, dict):
            errors.append("'motion_cuts' must be true/false or {\"enabled\", \"roll\", \"roll_wide\", \"slip_match\"}")
        else:
            for k in ("roll", "roll_wide", "slip_match"):
                if k in mc and not (isinstance(mc[k], (int, float)) and 0 <= mc[k] <= 2):
                    errors.append(f"motion_cuts.{k} must be 0-2 seconds")
    if not 1.0 <= sb["segments"][0]["src_out"] - sb["segments"][0]["src_in"] <= 3.5 if sb["segments"] else False:
        warnings.append("hook segment should be about 2 seconds")
    total += float(sb["end_card"].get("duration", 2.5))
    lo, hi = sb.get("min_duration", 60), sb.get("max_duration", 90)
    try:  # Alfonso's hard rule (2026-11-17): every video is 90 seconds
        from common import load_config
        vl = load_config().get("video_length") or {}
    except Exception:
        vl = {}
    if vl.get("target_seconds"):
        tgt, tol = float(vl["target_seconds"]), float(vl.get("tolerance_seconds", 1.0))
        lo, hi = tgt - tol, tgt + tol
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
            elif e["type"] == "hero":
                fx.append(f"Hero speed curve (slow-to-fast) on {fmt(e['from'])}-{fmt(e['to'])}")
                part = (e["to"] - e["from"]) / len(HERO)
                length += sum(part / x for x in HERO) - (e["to"] - e["from"]) / float(s.get("speed", 1.0))
            elif e["type"] == "speed_ramp":
                fx.append(f"speed ramp {e['speed']}x on {fmt(e['from'])}-{fmt(e['to'])}")
                length += (e["to"] - e["from"]) * (1 / e["speed"] - 1 / float(s.get("speed", 1.0)))
            elif e["type"] == "callout":
                fx.append(f"callout \"{e['text']}\" at {fmt(e['at'])}")
        if s.get("remove_pauses"):
            fx.append("cut pauses over 0.5s")
        if s.get("angle"):
            fx.append(f"angle: {s['angle']}")
        if s.get("cut_lock"):
            fx.append(f"cut locked ({s['cut_lock']}): {s.get('cut_lock_note', 'no reason given')}")
        if s.get("cut_on"):
            fx.append(f"cut in on: {s['cut_on']}")
        if s.get("visual"):
            fx.insert(0, s["visual"])
        if s["type"] == "hook":
            text = f"Title card: \"{sb['hook']['text']}\"" + (f" / \"{sb['hook']['subtitle']}\"" if sb["hook"].get("subtitle") else "")
        elif s["type"] == "exercise":
            kind = "Gold layered title" if sb.get("exercise_titles") else "Lower third"
            text = f"{kind}: \"{s['exercise'].upper()}" + (f" - {s['sets_reps']}\"" if s.get("sets_reps") else "\"")
            if sb.get("exercise_titles") and not any(t - 0.05 <= float(e["at"]) < t + length - 0.05 for e in sb["exercise_titles"]):
                text = f"(title already shown; same lift, new angle)"
        else:
            text = s.get("text", "captions only")
        L.append(f"| {i} | {fmt(t)}-{fmt(t + length)} | {fmt(a)}-{fmt(b)} | {s.get('label', s['type'])} | "
                 f"{s.get('exercise', '-')}{' ' + s['sets_reps'] if s.get('sets_reps') else ''} | {text} | {'; '.join(fx) or '-'} |")
        t += length
    ec = sb["end_card"]
    L.append(f"| {len(sb['segments']) + 1} | {fmt(t)}-{fmt(t + ec.get('duration', 2.5))} | freeze of last frame | End card | - | "
             f"\"{ec['text']}\"" + (f" / \"{ec['subtitle']}\"" if ec.get("subtitle") else "") + f" | {ec.get('style', 'animated bookmark end card')} |")
    L += ["", "## Throughout", "",
          ("- No running captions (captions: false); key words for the pop-ups / carousel: " if sb.get("captions") is False
           else "- Word-by-word captions, each word pops in as it is said; key words in the brand colour: ")
          + (", ".join(sb.get("key_words", [])) or "(none listed)"),
          "- Segmented progress bar across the top",
          ("- Cuts land on motion (Alfonso 2026-11-23): the Cuts Agent snaps each cut to the nearest moving frame, "
           "beat only within 3 frames; see output/cut_list.md" if sb.get("motion_cuts", True) not in (False,)
           and not (isinstance(sb.get("motion_cuts"), dict) and sb["motion_cuts"].get("enabled") is False)
           else "- Cut on motion is OFF for this video (motion_cuts: false): cuts exactly as planned"),
          "- English only, no hashtags on screen", ""]
    L += render_plan_extras(sb)
    if sb.get("carousel"):
        L += ["## Carousel post (2+ exercises)", "", "| Exercise | Sets x reps | Cue |", "|---|---|---|"]
        L += [f"| {c['exercise']} | {c.get('sets_reps', '')} | {c.get('cue', '')} |" for c in sb["carousel"]]
        L.append("")
    if sb.get("caption"):
        L += ["## Post caption", "", sb["caption"], ""]
    if sb.get("notes"):
        L += ["## Notes for the editors", ""] + [f"- {n}" for n in sb["notes"]] + [""]
    return "\n".join(L)


def render_plan_extras(sb: dict) -> list[str]:
    """Optional plan keys (song section, gold titles, pop-ups, style fx, multicam, relight), straight from the JSON."""
    L = []
    ss = sb.get("song_section")
    if ss:
        L += ["## Song section", "", f"- Song {ss.get('start')}s-{ss.get('end')}s, {ss.get('beats', '')}",
              f"- Why: {ss.get('why', '')}"]
        L += [f"- Cut {k}: {v}" for k, v in (ss.get("energy_map_cut") or {}).items()] + [""]
    if sb.get("exercise_titles"):
        L += ["## Gold layered exercise titles (cut time)", "",
              "| At | Dur | Behind him | In front | Intro line | y back / intro / front | Note |", "|---|---|---|---|---|---|---|"]
        L += [f"| {fmt(t['at'])} | {fmt(t['dur'])} | {t['first']} | {t['last']} | {t.get('intro_line', '')} | "
              f"{t.get('first_y')} / {t.get('intro_y')} / {t.get('last_y')} | {t.get('note', '')} |" for t in sb["exercise_titles"]]
        L.append("")
    if sb.get("lifts"):
        L += ["## Pop-up cards", "", "| Lift | Sets x reps | Spanish | Cut span | Gold title ends | Placement |", "|---|---|---|---|---|---|"]
        for x in sb["lifts"]:
            pl = ", ".join(f"{k} {x[k]}" for k in ("bar_y", "checklist_y") if k in x) or "default"
            L.append(f"| {x['name']} | {x.get('sets_reps', '')} | {x.get('spanish', '')} | {fmt(x['cut_start'])}-{fmt(x['cut_end'])} | "
                     f"{fmt(x['gold_title_end']) if 'gold_title_end' in x else '-'} | {pl} |")
        ft = sb.get("form_tip")
        if ft:
            L.append(f"\n- **Form tip** ({ft['lift']}, at {fmt(ft['at'])}, holds 5s): \"{ft['cue']}\" / \"{ft.get('cue_es', '')}\""
                     + (f". {ft['note']}" if ft.get("note") else ""))
        for w in sb.get("no_text_windows") or []:
            L.append(f"- **No text** {fmt(w.get('cut_start', w.get('from', 0)))}-{fmt(w.get('cut_end', w.get('to', 0)))}: {w.get('why', '')}")
        L.append("")
    if sb.get("style_fx"):
        L += ["## Fonzi style effects (style-lab/STYLE.md, scripts/style_fx.py)", "",
              "| Cut time | Tool | Where | Built by | Command | Note |", "|---|---|---|---|---|---|"]
        L += [f"| {fmt(f['cut'])} | {f['tool']} | {f.get('where', '')} | {f.get('who', '')} | `{f.get('cmd', '')}` | {f.get('note', '')} |"
              for f in sb["style_fx"]]
        if sb.get("plain_cuts"):
            L += ["", f"- {sb['plain_cuts']}"]
        L.append("")
    if sb.get("multicam_room"):
        L += ["## Multicam slots (clean, real-time stretches)", "", "| Slot | Cut time | Raw | Segment | Shot | Note |", "|---|---|---|---|---|---|"]
        L += [f"| {m['slot']} | {fmt(m['cut_start'])}-{fmt(m['cut_end'])} | {m.get('raw', '')} | {m.get('segment', '')} | "
              f"{m.get('shot', '')} | {m.get('note', '')} |" for m in sb["multicam_room"]]
        L.append("")
    r = sb.get("relight_suggestion")
    if r:
        L += ["## Suggested relight (for Alfonso to approve; nothing generated)", "",
              f"- **Clip:** cut {fmt(r['cut_start'])}-{fmt(r['cut_end'])} (raw {r.get('raw', '')}): {r.get('clip', '')}",
              f"- **Look:** {r.get('look', '')}" + (f"; alternative {r['alt_look']}" if r.get("alt_look") else ""),
              f"- **Model / cost:** {r.get('model', '')}", f"- **Status:** {r.get('status', '')}", ""]
    return L


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
