#!/usr/bin/env python3
"""Cut raw gym footage down to a short vertical edit. Needs ffmpeg and ffprobe.

The raw file is usually a string of clips shot back to back (one per lift).
This finds where each clip starts, keeps every real clip in its original
order, trims each to a stretch of reps, and joins them with hard cuts. No
music, no captions: the original sound, levelled, with a short fade at the end.

    python3 fonzi_edit.py SOURCE                      # 90 second edit
    python3 fonzi_edit.py SOURCE --seconds 60 --out reel.mp4
    python3 fonzi_edit.py SOURCE --plan-only          # plan + contact sheet, no render
    python3 fonzi_edit.py SOURCE --segments 4-12,30-36,47-56

SOURCE is a video file or a Google Drive share link (the file must be shared
as "anyone with the link"). Next to the output it writes NAME.plan.json (what
was kept) and NAME.sheet.jpg (a timestamped contact sheet to check the cut).
"""

import argparse
import json
import os
import re
import subprocess
import sys

MIN_CLIP = 5.0     # a source clip shorter than this is camera setup, not a lift
MARGIN = 0.5       # keep this far from each clip boundary
MIN_PIECE = 2.0    # shortest piece worth showing
SCENE = 0.3        # ffmpeg scene-change score that counts as a new clip
PLACE = 0.4        # where the kept window sits in the clip's slack (0 start, 1 end)


def drive_id(source):
    """The file id in a Google Drive link, or None if it is not one."""
    if "drive.google.com" not in source and "docs.google.com" not in source:
        return None
    m = re.search(r"/d/([\w-]{10,})", source) or re.search(r"[?&]id=([\w-]{10,})", source)
    return m.group(1) if m else None


def merge_cuts(cuts, gap=0.5):
    """Scene cuts that land within `gap` seconds of each other are one cut."""
    out = []
    for t in sorted(cuts):
        if not out or t - out[-1] > gap:
            out.append(t)
    return out


def clips_from_cuts(cuts, duration, min_clip=MIN_CLIP):
    """Source clips as (start, end), dropping the ones too short to be a lift."""
    edges = [0.0] + [t for t in merge_cuts(cuts) if 0 < t < duration] + [duration]
    clips = [(a, b) for a, b in zip(edges, edges[1:]) if b - a >= min_clip]
    return clips or [(0.0, duration)]


def allot(lengths, target):
    """Share `target` seconds between clips: equal shares, capped at each length."""
    give = [0.0] * len(lengths)
    left = min(target, sum(lengths))
    open_ = list(range(len(lengths)))
    while open_ and left > 1e-6:
        share = left / len(open_)
        full = [i for i in open_ if lengths[i] - give[i] <= share]
        if not full:
            for i in open_:
                give[i] += share
            break
        for i in full:
            left -= lengths[i] - give[i]
            give[i] = lengths[i]
            open_.remove(i)
    return give


def plan(cuts, duration, target, fps=30.0):
    """Pick one window per clip. Returns a list of (start, end) in source time."""
    clips = clips_from_cuts(cuts, duration)
    # with too many clips to give each a real piece, keep the longest ones
    most = max(1, int(target // MIN_PIECE))
    if len(clips) > most:
        keep = sorted(sorted(clips, key=lambda c: c[0] - c[1])[:most])
        clips = keep
    usable = [max(0.0, (b - a) - 2 * MARGIN) for a, b in clips]
    give = [int(g * fps + 1e-6) / fps for g in allot(usable, target)]
    # rounding down to whole frames leaves a few frames over: hand them back
    spare = int(round((min(target, sum(usable)) - sum(give)) * fps))
    for i in sorted(range(len(give)), key=lambda i: give[i] - usable[i]):
        if spare <= 0:
            break
        add = min(spare, int((usable[i] - give[i]) * fps + 1e-6))
        give[i] += add / fps
        spare -= add
    segs = []
    for (a, b), room, g in zip(clips, usable, give):
        g = round(g * fps) / fps
        if g < 1.0 / fps:
            continue
        start = a + MARGIN + (room - g) * PLACE
        start = round(start * fps) / fps
        segs.append((round(start, 3), round(start + g, 3)))
    return segs


def parse_segments(text):
    """'4-12,30-36.5' -> [(4.0, 12.0), (30.0, 36.5)]"""
    segs = []
    for part in text.split(","):
        a, b = part.strip().split("-")
        a, b = float(a), float(b)
        if b <= a:
            raise ValueError("segment %s ends before it starts" % part)
        segs.append((a, b))
    return segs


FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def label_filters(segs, labels, hold=3.0, fontsize=44):
    """drawtext filters: each label fades in near the start of its clip, lower third."""
    out, t = [], 0.0
    for (a, b), label in zip(segs, labels):
        if label:
            text = re.sub(r"[^A-Za-z0-9 \-+&!?.,]", "", label.upper())
            s0 = t + 0.4
            e0 = min(s0 + hold, t + (b - a))
            alpha = ("if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/0.3,if(lt(t,%.2f),1,"
                     "if(lt(t,%.2f),(%.2f-t)/0.3,0))))" % (s0, s0 + 0.3, s0, e0 - 0.3, e0, e0))
            out.append("drawtext=fontfile=%s:text='%s':fontsize=%d:fontcolor=white:alpha='%s':"
                       "borderw=3:bordercolor=black@0.85:x=(w-text_w)/2:y=h*0.80"
                       % (FONT, text, fontsize, alpha))
        t += b - a
    return out


XFADES = {"fade", "fadeblack", "fadewhite", "dissolve", "slideleft", "slideright", "wipeleft",
          "wiperight", "zoomin", "circleopen", "smoothleft", "smoothright", "pixelize"}
ONE_FRAME = 1 / 30.0


def join_plan(count, transitions, seconds):
    """One (type, seconds) per join between clips. 'cut' is a one frame fade."""
    kinds = list(transitions) if isinstance(transitions, (list, tuple)) else [transitions or "cut"]
    if len(kinds) == 1:
        kinds = kinds * (count - 1)
    kinds = (kinds + ["cut"] * (count - 1))[:count - 1]
    out = []
    for k in kinds:
        k = (k or "cut").strip()
        if k not in XFADES | {"cut"}:
            raise ValueError("unknown transition %r (use cut or one of %s)" % (k, sorted(XFADES)))
        out.append(("fade", ONE_FRAME) if k == "cut" else (k, seconds))
    return out


def filtergraph_joined(segs, joins, fade=0.6, labels=None, audio=True):
    """Like filtergraph, but clips overlap at each join. Every clip but the last is
    read `td` seconds longer so the overlap eats the extra and the length is unchanged."""
    parts = []
    n = len(segs)
    for i, (a, b) in enumerate(segs):
        end = b + (joins[i][1] if i < n - 1 else 0)
        parts.append("[0:v]trim=%s:%.3f,setpts=PTS-STARTPTS[v%d]" % (a, end, i))
        if audio:
            parts.append("[0:a]atrim=%s:%.3f,asetpts=PTS-STARTPTS[a%d]" % (a, end, i))
    vl, al, at = "v0", "a0", 0.0
    for k in range(n - 1):
        kind, td = joins[k]
        at += segs[k][1] - segs[k][0]
        parts.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]"
                     % (vl, k + 1, kind, td, at, k))
        vl = "x%d" % k
        if audio:
            parts.append("[%s][a%d]acrossfade=d=%.3f[y%d]" % (al, k + 1, td, k))
            al = "y%d" % k
    total = sum(b - a for a, b in segs)
    chain = label_filters(segs, labels or []) + [
        "fade=t=out:st=%.3f:d=%s" % (max(0.0, total - fade), fade)]
    parts.append("[%s]%s[v]" % (vl, ",".join(chain)))
    if audio:
        parts.append("[%s]afade=t=out:st=%.3f:d=%s,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
                     % (al, max(0.0, total - fade - 0.2), fade + 0.2))
    return ";".join(parts)


def filtergraph(segs, fade=0.6, labels=None):
    """The ffmpeg filter that trims each segment, joins them and levels the sound."""
    parts, labels = [], ""
    for i, (a, b) in enumerate(segs):
        d = b - a
        parts.append("[0:v]trim=%s:%s,setpts=PTS-STARTPTS[v%d]" % (a, b, i))
        parts.append("[0:a]atrim=%s:%s,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,"
                     "afade=t=out:st=%.3f:d=0.04[a%d]" % (a, b, max(0.0, d - 0.04), i))
        labels += "[v%d][a%d]" % (i, i)
    total = sum(b - a for a, b in segs)
    parts.append("%sconcat=n=%d:v=1:a=1[vc][ac]" % (labels, len(segs)))
    chain = label_filters(segs, labels or []) + [
        "fade=t=out:st=%.3f:d=%s" % (max(0.0, total - fade), fade)]
    parts.append("[vc]%s[v]" % ",".join(chain))
    parts.append("[ac]afade=t=out:st=%.3f:d=%s,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
                 % (max(0.0, total - fade - 0.2), fade + 0.2))
    return ";".join(parts)


# ---- everything below runs ffmpeg ----

def run(cmd, capture=False):
    res = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        sys.exit("failed: %s\n%s" % (" ".join(cmd[:3]), res.stderr[-2000:]))
    return (res.stdout or "") + (res.stderr or "")


def fetch(source, workdir):
    """Return a local path for the source, downloading a Drive link if needed."""
    fid = drive_id(source)
    if not fid:
        if not os.path.isfile(source):
            sys.exit("no such file: %s" % source)
        return source
    os.makedirs(workdir, exist_ok=True)
    path = os.path.join(workdir, "source-%s.mp4" % fid)
    if not os.path.isfile(path):
        url = "https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t" % fid
        run(["curl", "-sSfL", "-o", path, url])
    return path


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,r_frame_rate", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if out.returncode != 0:
        sys.exit("not a video ffmpeg can read: %s\n(a Drive link must be shared as "
                 "'anyone with the link')" % path)
    info = json.loads(out.stdout)
    kinds = [s["codec_type"] for s in info["streams"]]
    if "video" not in kinds:
        sys.exit("no video stream in %s" % path)
    fps = 30.0
    for s in info["streams"]:
        if s["codec_type"] == "video":
            n, _, d = s["r_frame_rate"].partition("/")
            if float(d or 1):
                fps = float(n) / float(d or 1)
            break
    return float(info["format"]["duration"]), fps, "audio" in kinds


def scene_cuts(path):
    log = run(["ffmpeg", "-hide_banner", "-i", path, "-an", "-vf",
               "scale=160:-2,select='gt(scene,%s)',showinfo" % SCENE, "-f", "null", "-"])
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", log)]


def sheet(path, out, duration):
    """A contact sheet with a timestamp on every frame."""
    step = max(1.0, duration / 60.0)
    draw = ("drawtext=text='%{pts\\:hms}':fontcolor=yellow:fontsize=16:"
            "box=1:boxcolor=black@0.6:x=3:y=3,")
    for stamp in (draw, ""):   # some ffmpeg builds have no drawtext
        res = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", path, "-vf",
             "fps=1/%s,scale=150:-2,%stile=10x6" % (step, stamp), "-frames:v", "1", out],
            stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return out
    return None


def render(path, segs, out, fps, has_audio, labels=None, joins=None):
    graph = filtergraph(segs, labels=labels)
    maps = ["-map", "[v]", "-map", "[a]"]
    if joins:
        graph = filtergraph_joined(segs, joins, labels=labels, audio=has_audio)
        maps = maps if has_audio else ["-map", "[v]"]
    elif not has_audio:
        graph = ";".join(p for p in graph.split(";") if "[0:a]" not in p and "[ac]" not in p)
        graph = re.sub(r"\[a\d+\]", "", graph).replace(":a=1[vc][ac]", ":a=0[vc]")
        maps = ["-map", "[v]"]
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-filter_complex", graph] + maps +
        ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", "%g" % fps, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", out])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", help="video file or Google Drive share link")
    ap.add_argument("--seconds", type=float, default=90.0, help="length of the edit (default 90)")
    ap.add_argument("--out", default="fonzi-edit.mp4")
    ap.add_argument("--segments", help="keep exactly these, e.g. 4-12,30-36 (source seconds)")
    ap.add_argument("--labels", help="text overlay per clip, in order, separated by |, e.g. "
                    "'BENCH PRESS|SQUATS||ROWS' (empty = no text on that clip)")
    ap.add_argument("--transitions", help="how clips join: 'cut' (default), one type for all joins "
                    "(fade, fadeblack, dissolve, slideleft, wipeleft, zoomin...), or one per join "
                    "separated by commas, e.g. fade,cut,fade")
    ap.add_argument("--transition-seconds", type=float, default=0.3)
    ap.add_argument("--plan-only", action="store_true", help="plan and source sheet, no render")
    args = ap.parse_args(argv)

    out = os.path.abspath(args.out)
    base = os.path.splitext(out)[0]
    src = fetch(args.source, os.path.join(os.path.dirname(out), "fonzi-source"))
    duration, fps, has_audio = probe(src)

    if args.segments:
        segs = [(a, min(b, duration)) for a, b in parse_segments(args.segments)]
        cuts = []
    else:
        cuts = merge_cuts(scene_cuts(src))
        segs = plan(cuts, duration, args.seconds, fps)
    total = sum(b - a for a, b in segs)

    report = {"source": src, "source_seconds": round(duration, 2), "cuts_found": cuts,
              "segments": [{"start": a, "end": b, "seconds": round(b - a, 2)} for a, b in segs],
              "edit_seconds": round(total, 2), "output": out}
    with open(base + ".plan.json", "w") as fh:
        json.dump(report, fh, indent=2)

    if args.plan_only:
        report["sheet"] = sheet(src, base + ".source-sheet.jpg", duration)
    else:
        labels = args.labels.split("|") if args.labels else None
        joins = None
        if args.transitions and args.transitions != "cut":
            joins = join_plan(len(segs), args.transitions.split(","), args.transition_seconds)
        render(src, segs, out, fps, has_audio, labels, joins)
        report["sheet"] = sheet(out, base + ".sheet.jpg", total)
    json.dump(report, sys.stdout, indent=2)
    print()
    if duration < args.seconds and not args.segments:
        print("note: the source is only %.0f s, shorter than the %.0f s asked for"
              % (duration, args.seconds), file=sys.stderr)


if __name__ == "__main__":
    main()
