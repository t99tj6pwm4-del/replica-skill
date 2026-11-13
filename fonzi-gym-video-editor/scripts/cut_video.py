#!/usr/bin/env python3
"""CUTS AGENT tool. Cuts the raw video exactly as output/storyboard.json says. No text, ever.

    python3 scripts/cut_video.py

Does: trim to the planned ranges (black tail / dead ends never make it in), cut pauses over 0.5s,
jump cuts, punch-ins (110-130%, snapped to the beat when a song is set), slow-mo, speed ramps,
9:16 reframing, song mix, freeze-frame tail for the end card.

Writes:
  output/cut_version.mp4       1080x1920, 30fps, H.264 + AAC
  output/work/cut_voice.wav    voice only (for Whisper)
  output/work/cut_map.json     where every segment / effect landed on the final timeline
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, OUT, SONGS, W, WORK, die, load_json, probe, rel, resolve, run, save_json  # noqa: E402
from storyboard_md import validate  # noqa: E402

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
            # ramp = ease in, hold, ease out
            f, t, sp = e["from"], e["to"], float(e["speed"])
            edge = (t - f) * 0.2
            mid = sp ** 0.5 if base_speed == 1.0 else (sp * base_speed) ** 0.5
            speeds += [(f, f + edge, mid, "speed_ramp"), (f + edge, t - edge, sp, "speed_ramp"),
                       (t - edge, t, mid, "speed_ramp")]
    marks = sorted({x for k in keep for x in k} | {x for s in speeds for x in s[:2]} | {x for z in zooms for x in z[:2]})
    pieces = []
    for lo, hi in zip(marks, marks[1:]):
        mid = (lo + hi) / 2
        if not any(k0 <= mid <= k1 for k0, k1 in keep) or hi - lo < FRAME:
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


def main():
    sb = load_json(OUT / "storyboard.json")
    analysis = load_json(WORK / "analysis.json", default={})
    src = resolve(sb["source"])
    info = probe(src)
    errors, _, _ = validate(sb, info["duration"])
    if errors:
        die("storyboard.json is not valid, send it back to the Storyboard Agent:\n  - " + "\n  - ".join(errors))
    if sb.get("song") and SONGS.resolve() not in resolve(sb["song"]).resolve().parents:
        die("the song must be one of Alfonso's own mp3s in songs/ (no stock or AI music)")
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

    tmp = WORK / "pieces"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)

    out_t, all_pieces, seg_map, events, callouts, snapped = 0.0, [], [], [], [], 0
    for seg in sb["segments"]:
        seg = dict(seg)
        # snap each punch-in so the zoom cut lands on a beat
        if period:
            probe_pieces = build_pieces(seg, dead)
            for e in seg.get("effects", []):
                if e["type"] != "punch_in":
                    continue
                t, at_out = out_t, None
                for p in probe_pieces:
                    if p["src_a"] <= e["at"] < p["src_b"]:
                        at_out = t + (e["at"] - p["src_a"]) / p["speed"]
                        local_speed = p["speed"]
                        break
                    t += q((p["src_b"] - p["src_a"]) / p["speed"])
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
            p["out_dur"] = q((p["src_b"] - p["src_a"]) / p["speed"])
            if p["out_dur"] < FRAME:
                continue
            p["out_a"], p["out_b"] = round(out_t, 4), round(out_t + p["out_dur"], 4)
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
    })
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


if __name__ == "__main__":
    main()
