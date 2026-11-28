#!/usr/bin/env python3
"""CUTS AGENT tool. Cuts the raw video exactly as output/storyboard.json says. No text, ever.

    python3 scripts/cut_video.py
    python3 scripts/cut_video.py --plan-only [DIR]   # cut list only, no render, nothing shipped touched
    python3 scripts/cut_video.py --no-motion         # old behaviour: cuts exactly as planned, punch-ins on the beat

Cut on motion (Alfonso 2026-11-23, Director answer 26, scripts/motion_cuts.py): before cutting, every planned
cut is moved to the nearest motion-safe frame (roll <= 0.4 s, up to 1.0 s only when nothing moves closer;
the cut after the hook only slips the incoming clip so the opener / intro timing stays; two angles of the
same exercise slip the incoming angle up to 1.0 s to line up the same rep point). Beat is second: snapped
only if the beat is within 3 frames. Storyboard `cut_lock` keeps a cut exactly where planned (still scored).

Does: trim to the planned ranges (black tail / dead ends never make it in), cut pauses over 0.5s,
jump cuts, punch-ins (110-130%, snapped to the beat when a song is set), slow-mo, speed ramps,
9:16 reframing, song mix, freeze-frame tail for the end card.

Writes:
  output/cut_version.mp4       1080x1920, 30fps, H.264 + AAC
  output/work/cut_voice.wav    voice only (for Whisper)
  output/work/cut_map.json     where every segment / effect landed on the final timeline, plus "cut_list"
  output/cut_list.md           every cut with its motion, matched, direction, beat and stillness_flag
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, SONGS, W, WORK, die, load_json, probe, rel, resolve, run, save_json  # noqa: E402
from storyboard_md import validate  # noqa: E402
import motion_cuts as mc  # noqa: E402

PAD = 0.12       # breath kept on each side of a removed pause
MIN_PAUSE = 0.5  # only pauses longer than this are cut
FRAME = 1.0 / FPS


def q(t: float) -> float:
    """Quantise a duration to whole frames so audio and video never drift apart."""
    return round(t * FPS) / FPS


def keep_ranges(a: float, b: float, dead: list) -> list[tuple[float, float]]:
    cuts = []
    for d0, d1 in dead:
        lo, hi = max(a, d0) + PAD, min(b, d1) - PAD
        # a pause touching the segment edge is a dead end: drop it entirely
        if d0 <= a + 0.05:
            lo = a
        if d1 >= b - 0.05:
            hi = b
        if min(b, d1) - max(a, d0) > MIN_PAUSE and hi - lo > 0.1:
            cuts.append((lo, hi))
    keep, cur = [], a
    for lo, hi in sorted(cuts):
        if lo - cur > FRAME:
            keep.append((cur, lo))
        cur = max(cur, hi)
    if b - cur > FRAME:
        keep.append((cur, b))
    return keep


def build_pieces(seg: dict, dead: list) -> list[dict]:
    """Split one storyboard segment into pieces of constant speed + zoom."""
    a, b = float(seg["src_in"]), float(seg["src_out"])
    base_speed = float(seg.get("speed", 1.0))
    keep = keep_ranges(a, b, dead) if seg.get("remove_pauses") else [(a, b)]
    speeds, zooms = [], []
    for e in seg.get("effects", []):
        if e["type"] == "punch_in":
            zooms.append((e["at"], e["at"] + e["dur"], float(e.get("zoom", 1.2)), e))
        elif e["type"] == "slow_mo":
            speeds.append((e["from"], e["to"], float(e["speed"]), "slow_mo"))
        elif e["type"] == "hero":
            # CapCut "Hero" speed curve, free here: slow on the peak of the rep, ramping back to normal
            f, t = e["from"], e["to"]
            part = (t - f) / 4
            for k, sp in enumerate((0.35, 0.5, 0.75, 1.0)):
                speeds.append((f + k * part, f + (k + 1) * part, sp, "hero"))
        elif e["type"] == "speed_ramp":
            # ramp = ease in, hold, ease out. The storyboard plans a ramp as (to - from) / speed seconds
            # (storyboard_md.validate), so the hold is solved to keep exactly that length: the eased
            # edges never push later cuts off the beat grid.
            f, t, sp = e["from"], e["to"], float(e["speed"])
            edge = (t - f) * 0.1
            mid = sp ** 0.5 if base_speed == 1.0 else (sp * base_speed) ** 0.5
            hold = (t - f - 2 * edge) / ((t - f) / sp - 2 * edge / mid)
            speeds += [(f, f + edge, mid, "speed_ramp"), (f + edge, t - edge, hold, "speed_ramp"),
                       (t - edge, t, mid, "speed_ramp")]
    marks = sorted({x for k in keep for x in k} | {x for s in speeds for x in s[:2]} | {x for z in zooms for x in z[:2]})
    pieces = []
    for lo, hi in zip(marks, marks[1:]):
        mid = (lo + hi) / 2
        if not any(k0 <= mid <= k1 for k0, k1 in keep):
            continue
        if hi - lo < FRAME:
            if pieces and abs(pieces[-1]["src_b"] - lo) < 1e-9:
                pieces[-1]["src_b"] = hi   # fold a sub-frame sliver into the piece before it (no lost time)
            continue
        sp, kind = next(((s[2], s[3]) for s in speeds if s[0] <= mid < s[1]), (base_speed, None))
        z = max([zz[2] for zz in zooms if zz[0] <= mid < zz[1]] or [float(seg.get("zoom", 1.0))])
        pieces.append({"src_a": lo, "src_b": hi, "speed": sp, "zoom": z, "kind": kind,
                       "punch": any(zz[0] <= mid < zz[1] for zz in zooms)})
    return pieces


def video_filter(seg: dict, piece: dict, sw: int, sh: int, src_fps: float) -> str:
    target = W / H
    fx, fy = float(seg.get("focus_x", 0.5)), float(seg.get("focus_y", 0.45))
    chain = [f"setpts=(PTS-STARTPTS)/{piece['speed']}"]
    if piece["speed"] < 1 and src_fps * piece["speed"] < 24:
        chain.append(f"minterpolate=fps={FPS}:mi_mode=blend")  # frame-blend slow-mo from 30fps footage
    if seg.get("fit") == "blur" and sw / sh > target:
        z = piece["zoom"]
        return (",".join(chain) + f",split[b][f];[b]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},boxblur=28:4,eq=brightness=-0.12[bg];"
                f"[f]crop=iw/{z}:ih/{z}:(iw-iw/{z})*{fx}:(ih-ih/{z})*{fy},scale={W}:-2[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={FPS},format=yuv420p")
    if sw / sh > target:   # wider than 9:16 -> crop the sides around crop_x
        cx = float(seg.get("crop_x", 0.5))
        chain.append(f"crop=ih*{target:.6f}:ih:(iw-ih*{target:.6f})*{cx}:0")
    else:                  # taller -> crop top/bottom
        chain.append(f"crop=iw:iw/{target:.6f}:0:(ih-iw/{target:.6f})*{float(seg.get('crop_y', 0.5))}")
    z = piece["zoom"]
    if z > 1.001:
        chain.append(f"crop=iw/{z}:ih/{z}:(iw-iw/{z})*{fx}:(ih-ih/{z})*{fy}")
    chain += [f"scale={W}:{H}:flags=lanczos", "setsar=1", f"fps={FPS}", "format=yuv420p"]
    return ",".join(chain)


def atempo(speed: float) -> str:
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.5f}")
    return ",".join(parts)


def seg_len(seg: dict, dead: list) -> float:
    return sum((p["src_b"] - p["src_a"]) / p["speed"] for p in build_pieces(seg, dead))


def _edge_speed(seg: dict, dead: list, end: bool) -> float:
    ps = build_pieces(seg, dead)
    return (ps[-1] if end else ps[0])["speed"] if ps else 1.0


def _effect_span(seg: dict) -> tuple[float, float] | None:
    spans = [(e["at"], e["at"] + e.get("dur", 0)) if "at" in e else (e["from"], e["to"]) for e in seg.get("effects", [])]
    return (min(a for a, _ in spans), max(b for _, b in spans)) if spans else None


def plan_motion_cuts(sb: dict, dead: list, period, phase, src, info, usable) -> tuple[list, list] | None:
    """Move every planned cut onto motion (rules 1-9). Returns (new segments, cut rows) or None when off.
    Only src_in / src_out (roll, slip) and punch-in `at` change; nothing is added, dropped or reordered."""
    cfg = sb.get("motion_cuts", {})
    if cfg is False or (isinstance(cfg, dict) and cfg.get("enabled") is False):
        return None
    cfg = cfg if isinstance(cfg, dict) else {}
    tracks = mc.Tracks(src, info)
    beat = (period, phase)
    lo_ok, hi_ok = float(usable[0]), float(usable[1])
    segs = [{**s, "effects": [dict(e) for e in s.get("effects", [])]} for s in sb["segments"]]
    rows = []
    for i, b_seg in enumerate(segs):
        out_start = sum(seg_len(s, dead) for s in segs[:i])
        if i > 0:
            a_seg = segs[i - 1]
            a_t, b_t = float(a_seg["src_out"]), float(b_seg["src_in"])
            lock = None
            if a_seg.get("cut_lock") in ("out", "both") or b_seg.get("cut_lock") in ("in", "both"):
                lock = b_seg.get("cut_lock_note") or a_seg.get("cut_lock_note") or "cut_lock in storyboard"
            lim = mc.cut_limits(a_seg, b_seg, lock, cfg)
            ea, eb = _effect_span(a_seg), _effect_span(b_seg)
            a_in, b_out = float(a_seg["src_in"]), float(b_seg["src_out"])

            def allowed(r, s_, a_t=a_t, b_t=b_t, ea=ea, eb=eb, a_in=a_in, b_out=b_out):
                na, nb_in, nb_out = a_t + r * FRAME, b_t + (r + s_) * FRAME, b_out + s_ * FRAME
                if na - a_in < 0.5 or nb_out - nb_in < 0.5 or na > hi_ok or nb_in < lo_ok or nb_out > hi_ok:
                    return False
                if ea and na < ea[1] - 1e-6:
                    return False
                if eb and (nb_in > eb[0] + 1e-6 or nb_out < eb[1] - 1e-6):
                    return False
                return True
            res = mc.plan_cut(tracks, a_seg, a_t, b_seg, b_t, roll=lim["roll"], slip=lim["slip"], wide=lim["wide"],
                              out_t=out_start, beat=beat if period else (None, None),
                              speed_a=_edge_speed(a_seg, dead, True), locked=lock, allowed=allowed)
            r, s_ = res["roll_frames"] * FRAME, res["slip_frames"] * FRAME
            a_seg["src_out"] = round(a_t + r, 4)
            b_seg["src_in"] = round(b_t + r + s_, 4)
            b_seg["src_out"] = round(b_out + s_, 4)
            moved = ("stays" if not (res["roll_frames"] or res["slip_frames"]) else
                     f"roll {res['roll_frames']:+d} fr" + (f", slip in {res['slip_frames']:+d} fr" if res["slip_frames"] else ""))
            rows.append({"type": "clip", "seg": b_seg.get("id"), "src_t": b_seg["src_in"], "kind": res["kind"],
                         "from_to": f"{a_seg.get('id')} {a_seg['src_out']:.2f} -> {b_seg.get('id')} {b_seg['src_in']:.2f}",
                         "motion": res["motion"], "matched": res["matched"], "direction": res["direction"],
                         "beat": res["beat"], "moved": moved, "stillness_flag": res["stillness_flag"],
                         "first_third": res["in"]["first_third"]})
        # punch-ins (zoom cuts on continuous footage): start in the first third of a move, end on motion
        out_start = sum(seg_len(s, dead) for s in segs[:i])
        for e in b_seg["effects"]:
            if e["type"] != "punch_in":
                continue
            ps, t_out, sp = build_pieces(b_seg, dead), out_start, 1.0
            for p in ps:
                if p["src_a"] <= e["at"] < p["src_b"]:
                    t_out += (e["at"] - p["src_a"]) / p["speed"]
                    sp = p["speed"]
                    break
                t_out += (p["src_b"] - p["src_a"]) / p["speed"]
            z = mc.plan_zoom_edge(tracks, b_seg, float(e["at"]), float(e["dur"]), float(b_seg["src_in"]),
                                  float(b_seg["src_out"]), out_t=t_out, beat=beat if period else (None, None), speed=sp)
            e["at"], e["_beat_snapped"] = z["at"], z["beat_snapped"]
            for edge, st, t in (("punch in", z["start"], z["at"]), ("punch out", z["end"], z["at"] + float(e["dur"]))):
                rows.append({"type": edge, "seg": b_seg.get("id"), "src_t": round(t, 3), "kind": "zoom",
                             "from_to": f"{b_seg.get('id')} {t:.2f} (same footage, zoom {e.get('zoom', 1.2)})",
                             "motion": st["what"] + (", first third" if st["first_third"] else ""),
                             "matched": "yes" if st["moving"] else "no", "direction": st["dir"] or "-",
                             "beat": z["beat"], "moved": "stays" if not z["shift_frames"] else f"{z['shift_frames']:+d} fr",
                             "stillness_flag": "" if st["moving"] else "zoom cut on a still frame: no motion within 0.4 s of the planned key rep",
                             "first_third": st["first_third"]})
    # dead-time jump cuts inside a segment (remove_pauses): allowed on stillness, flagged
    for seg in segs:
        if not seg.get("remove_pauses"):
            continue
        keep = keep_ranges(float(seg["src_in"]), float(seg["src_out"]), dead)
        for (a0, a1), (b0, b1) in zip(keep, keep[1:]):
            ta = tracks.get(a1 - 1.6, a1 + 0.2, seg.get("crop_x", 0.5), seg.get("crop_y", 0.5), seg.get("exercise"))
            tb = tracks.get(b0 - 0.2, b0 + 1.6, seg.get("crop_x", 0.5), seg.get("crop_y", 0.5), seg.get("exercise"))
            sa, sb_ = ta.at(a1 - FRAME), tb.at(b0)
            rows.append({"type": "dead time", "seg": seg.get("id"), "src_t": b0, "kind": "same_angle",
                         "from_to": f"{seg.get('id')} {a1:.2f} -> {b0:.2f}", "motion": mc.motion_text(sa, sb_),
                         "matched": "yes" if mc.matched(sa, sb_, "same_angle") else "no",
                         "direction": f"{sa['dir'] or '-'} -> {sb_['dir'] or '-'}", "beat": "-", "moved": "stays",
                         "stillness_flag": mc.stillness_reason(sa, sb_, dead_time=True), "first_third": sb_["first_third"]})
    return segs, rows


def main():
    plan_only = "--plan-only" in sys.argv
    plan_dir = None
    if plan_only:
        k = sys.argv.index("--plan-only")
        plan_dir = Path(sys.argv[k + 1]) if len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith("--") \
            else WORK / "motion_plan_preview"
    sb = load_json(OUT / "storyboard.json")
    analysis = load_json(WORK / "analysis.json", default={})
    src = resolve(sb["source"])
    info = probe(src)
    errors, _, _ = validate(sb, info["duration"])
    if errors:
        die("storyboard.json is not valid, send it back to the Storyboard Agent:\n  - " + "\n  - ".join(errors))
    if sb.get("song") and SONGS.resolve() not in resolve(sb["song"]).resolve().parents:
        die("the song must be one of Alfonso's own mp3s in songs/ (no stock or AI music)")
    if not plan_only:
        for stale in ("multicam_version.mp4", "final_edit.mp4"):   # built on the old cut
            (OUT / stale).unlink(missing_ok=True)
        (WORK / "multicam_map.json").unlink(missing_ok=True)
    sw, sh, src_fps = info["video"]["width"], info["video"]["height"], info["video"]["fps"]
    has_audio = info["audio"] is not None
    dead = analysis.get("dead_ranges", []) if analysis.get("source") == rel(src) else []

    # beat grid on the output timeline
    period = phase = None
    if sb.get("song") and sb.get("song_bpm"):
        period = 60.0 / float(sb["song_bpm"])
        phase = (float(sb.get("song_beat_offset", 0.0)) - float(sb.get("song_start", 0.0))) % period

    # cut on motion (rules 1-9): move each planned cut / punch-in edge onto the nearest motion-safe frame
    motion = None
    if "--no-motion" not in sys.argv:
        usable = analysis.get("usable_range") if analysis.get("source") == rel(src) else None
        motion = plan_motion_cuts(sb, dead, period, phase, src, info, usable or (0.0, info["duration"]))
    cut_rows = []
    if motion:
        sb = {**sb, "segments": motion[0]}       # in memory only; storyboard.json is never rewritten
        cut_rows = motion[1]
        errors, _, _ = validate(sb, info["duration"])
        if errors:
            die("motion-snapped cuts broke the plan (report to the Director):\n  - " + "\n  - ".join(errors))

    tmp = WORK / "pieces"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)

    # exact_t = unquantised timeline; each piece ends on the frame nearest its exact end, so frame
    # rounding never accumulates (drift stays under half a frame for the whole cut)
    out_t, exact_t, all_pieces, seg_map, events, callouts, snapped = 0.0, 0.0, [], [], [], [], 0
    for seg in sb["segments"]:
        seg = dict(seg)
        if motion:   # punch-ins already placed on motion, beat snapped only within 3 frames (rule 6)
            snapped += sum(1 for e in seg.get("effects", []) if e.pop("_beat_snapped", False))
        # snap each punch-in so the zoom cut lands on a beat
        elif period:
            probe_pieces = build_pieces(seg, dead)
            for e in seg.get("effects", []):
                if e["type"] != "punch_in":
                    continue
                t, at_out = exact_t, None
                for p in probe_pieces:
                    if p["src_a"] <= e["at"] < p["src_b"]:
                        at_out = t + (e["at"] - p["src_a"]) / p["speed"]
                        local_speed = p["speed"]
                        break
                    t += (p["src_b"] - p["src_a"]) / p["speed"]
                if at_out is None:
                    continue
                beat = phase + round((at_out - phase) / period) * period
                shift = (beat - at_out) * local_speed
                new_at = e["at"] + shift
                if seg["src_in"] <= new_at and new_at + e["dur"] <= seg["src_out"]:
                    e["at"] = round(new_at, 3)
                    snapped += 1
        seg_start = out_t
        seg_pieces = build_pieces(seg, dead)
        for p in seg_pieces:
            exact_t += (p["src_b"] - p["src_a"]) / p["speed"]
            p["out_dur"] = round(q(exact_t) - out_t, 4)
            if p["out_dur"] < FRAME / 2:   # out_t is rounded to 4 decimals, so one frame can read 0.0333 < FRAME
                continue
            p["out_a"], p["out_b"] = round(out_t, 4), round(q(exact_t), 4)
            p["seg"] = seg
            out_t = p["out_b"]
            all_pieces.append(p)
        seg_map.append({"id": seg.get("id"), "type": seg["type"], "label": seg.get("label", seg["type"]),
                        "exercise": seg.get("exercise"), "sets_reps": seg.get("sets_reps"),
                        "out_start": round(seg_start, 3), "out_end": round(out_t, 3)})

    def src_to_out(t: float, seg_id):
        for p in all_pieces:
            if p["seg"].get("id") == seg_id and p["src_a"] - 1e-6 <= t <= p["src_b"] + 1e-6:
                return p["out_a"] + (t - p["src_a"]) / p["speed"]
        later = [p for p in all_pieces if p["seg"].get("id") == seg_id and p["src_a"] >= t]
        return later[0]["out_a"] if later else None

    # merge neighbouring pieces into timeline events for the visuals agent
    for p in all_pieces:
        for kind, on, extra in (("punch_in", p["punch"], {"zoom": p["zoom"]}),
                                (p["kind"], p["kind"] is not None, {"speed": p["speed"]})):
            if not on:
                continue
            last = events[-1] if events else None
            if last and last["kind"] == kind and abs(last["out_end"] - p["out_a"]) < 1e-3 and kind != "punch_in":
                last["out_end"] = p["out_b"]
                last["speed"] = min(last["speed"], p["speed"]) if kind in ("slow_mo", "hero") else max(last["speed"], p["speed"])
            elif last and last["kind"] == kind == "punch_in" and abs(last["out_end"] - p["out_a"]) < 1e-3 and last["zoom"] == p["zoom"]:
                last["out_end"] = p["out_b"]
            else:
                events.append({"kind": kind, "out_start": p["out_a"], "out_end": p["out_b"], **extra})
    # merge pieces of the same event that were split by another event's boundaries
    merged = []
    for e in sorted(events, key=lambda e: (e["kind"], e["out_start"])):
        last = merged[-1] if merged else None
        if (last and last["kind"] == e["kind"] and abs(last["out_end"] - e["out_start"]) < 1e-3
                and (e["kind"] != "punch_in" or last.get("zoom") == e.get("zoom"))):
            last["out_end"] = e["out_end"]
            if "speed" in e:
                last["speed"] = min(last["speed"], e["speed"]) if e["kind"] in ("slow_mo", "hero") else max(last["speed"], e["speed"])
        else:
            merged.append(dict(e))
    events = sorted(merged, key=lambda e: e["out_start"])
    for seg in sb["segments"]:
        for e in seg.get("effects", []):
            if e["type"] == "callout":
                a = src_to_out(e["at"], seg.get("id"))
                b = src_to_out(e["at"] + e["dur"], seg.get("id"))
                if a is not None:
                    callouts.append({"text": e["text"], "out_start": round(a, 3),
                                     "out_end": round(b if b and b > a else a + e["dur"], 3),
                                     "x": e.get("x"), "y": e.get("y")})

    # cut list (motion / matched / stillness_flag) on the final timeline
    seg_out = {m["id"]: m for m in seg_map}
    for r in cut_rows:
        if r["type"] == "clip" and r["seg"] in seg_out:
            r["cut_time"] = seg_out[r["seg"]]["out_start"]
        else:
            t = src_to_out(r["src_t"], r["seg"])
            r["cut_time"] = round(t, 3) if t is not None else seg_out.get(r["seg"], {}).get("out_start", 0.0)
    cut_rows.sort(key=lambda r: r["cut_time"])
    if plan_only:
        plan_dir.mkdir(parents=True, exist_ok=True)
        save_json(plan_dir / "cut_plan.json", {"source": rel(src), "body_end": round(out_t, 3), "segments": seg_map,
                                                "planned_segments": [{k: s.get(k) for k in ("id", "src_in", "src_out")} for s in sb["segments"]],
                                                "cut_list": cut_rows})
        (plan_dir / "cut_list.md").write_text(mc.cut_list_md(sb.get("title", ""), cut_rows, cut_list_intro(cut_rows)))
        print(f"plan only: {len(cut_rows)} cuts, body {out_t:.2f}s -> {rel(plan_dir)}/cut_list.md (nothing rendered)")
        return

    # render every piece, then join them (jump cuts)
    print(f"cutting {len(all_pieces)} pieces from {rel(src)} ...")
    listing = []
    for i, p in enumerate(all_pieces):
        out = tmp / f"p{i:03d}.mkv"
        dur_in = p["out_dur"] * p["speed"]
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{p['src_a']:.4f}", "-t", f"{dur_in + 0.2:.4f}", "-i", src]
        if not has_audio:
            cmd += ["-f", "lavfi", "-t", f"{p['out_dur']:.4f}", "-i", "anullsrc=r=48000:cl=stereo"]
            af = "anull"
        else:
            fade = min(0.012, p["out_dur"] / 4)
            af = (f"{atempo(p['speed'])},aresample=48000,aformat=channel_layouts=stereo,"
                  f"afade=t=in:d={fade},afade=t=out:st={p['out_dur'] - fade:.4f}:d={fade}")
        cmd += ["-filter_complex", f"[0:v]{video_filter(p['seg'], p, sw, sh, src_fps)}[v];[{0 if has_audio else 1}:a]{af}[a]",
                "-map", "[v]", "-map", "[a]", "-t", f"{p['out_dur']:.4f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-c:a", "pcm_s16le", "-ar", "48000", out]
        run(cmd)
        listing.append(f"file '{out}'")
    (tmp / "list.txt").write_text("\n".join(listing) + "\n")

    body = out_t
    tail = float(sb["end_card"].get("duration", 2.5))
    total = round(body + tail, 3)
    joined = WORK / "joined.mkv"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-c", "copy", joined])

    # final export: freeze tail for the end card, optional song under the voice
    voice_vol = float(sb.get("voice_volume", 1.0))
    # Alfonso (2026-11-15, config audio.mute_baked_music): always mute music baked into his uploads.
    # With his own song from songs/ the render step does not mute anything, so with no speech the
    # footage's baked-in audio is dropped here and the song is the only soundtrack.
    from common import load_config
    if ("voice_volume" not in sb and sb.get("song") and load_config().get("audio", {}).get("mute_baked_music")
            and analysis.get("source") == rel(src) and len(analysis.get("raw_words", [])) < 3):
        voice_vol = 0.0
        print("audio: no speech, baked-in footage audio muted (Alfonso's rule); song only")
    fc = [f"[0:v]tpad=stop_mode=clone:stop_duration={tail},fps={FPS},format=yuv420p[v]",
          f"[0:a]volume={voice_vol},apad=pad_dur={tail}[voice]"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", joined]
    if sb.get("song"):
        vol = float(sb.get("song_volume", 0.18))
        cmd += ["-stream_loop", "-1", "-ss", str(sb.get("song_start", 0.0)), "-i", resolve(sb["song"])]
        fc.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},afade=t=in:d=0.4,"
                  f"afade=t=out:st={total - 1.5:.3f}:d=1.5[music]")
        fc.append("[voice][music]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
    else:
        fc.append("[voice]anull[a]")
    final = OUT / "cut_version.mp4"
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", final]
    run(cmd)
    run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-vn", "-ac", "1", "-ar", "16000", WORK / "cut_voice.wav"])
    shutil.rmtree(tmp, ignore_errors=True)
    joined.unlink(missing_ok=True)

    info = probe(final)
    removed = sum(float(s["src_out"]) - float(s["src_in"]) for s in sb["segments"]) - sum(
        p["src_b"] - p["src_a"] for p in all_pieces)
    save_json(WORK / "cut_map.json", {
        "cut": rel(final), "duration": round(info["duration"], 3), "body_end": round(body, 3),
        "segments": seg_map, "events": [{**e, "out_start": round(e["out_start"], 3), "out_end": round(e["out_end"], 3)} for e in events],
        "callouts": callouts, "end_card": {"out_start": round(body, 3), "out_end": total},
        "beat": {"period": period, "phase": phase, "punch_ins_on_beat": snapped} if period else None,
        "pauses_removed_seconds": round(removed, 2),
        "pieces": [{k: round(p[k], 3) for k in ("src_a", "src_b", "out_a", "out_b", "speed", "zoom")} for p in all_pieces],
        "cut_list": cut_rows,
        "motion_cuts": bool(motion),
    })
    if motion:
        (OUT / "cut_list.md").write_text(mc.cut_list_md(sb.get("title", ""), cut_rows, cut_list_intro(cut_rows)))
        flagged = sum(1 for r in cut_rows if r["stillness_flag"])
        print(f"       cut list: {len(cut_rows)} cuts, {sum(r['matched'] == 'yes' for r in cut_rows)} matched, "
              f"{flagged} on stillness (flagged) -> output/cut_list.md")
    v = info["video"]
    print(f"wrote  {rel(final)}  {v['width']}x{v['height']} {v['fps']}fps {v['codec']}+"
          f"{info['audio']['codec'] if info['audio'] else 'NO AUDIO'}  {info['duration']:.2f}s")
    print(f"       {len(all_pieces)} pieces, {removed:.1f}s of pauses removed, "
          f"{sum(1 for e in events if e['kind'] == 'punch_in')} punch-ins"
          + (f" ({snapped} snapped to the beat)" if period else "")
          + f", {sum(1 for e in events if e['kind'] == 'slow_mo')} slow-mo, "
          f"{sum(1 for e in events if e['kind'] == 'speed_ramp')} speed ramps")
    lo, hi = sb.get("min_duration", 60), sb.get("max_duration", 90)
    if not lo <= info["duration"] <= hi:
        die(f"cut is {info['duration']:.1f}s but must be {lo}-{hi}s. Report this to the Director: "
            "the storyboard ranges need adjusting.", code=2)


def cut_list_intro(rows: list) -> list[str]:
    return ["Cut on motion (Alfonso 2026-11-23). `motion` = what moves on each side (out / in), `matched` = same",
            "rep point + direction (two angles), same direction (new exercise), or moving footage (zoom cut).",
            "`moved` = how far the planned cut went to land on motion. Any cut on stillness is flagged with why.",
            "", f"**{len(rows)} cuts, {sum(1 for r in rows if not r['stillness_flag'])} on motion, "
            f"{sum(1 for r in rows if r['stillness_flag'])} flagged.**", ""]


if __name__ == "__main__":
    main()
