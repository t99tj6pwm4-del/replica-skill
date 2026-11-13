#!/usr/bin/env python3
"""Full /fonzi-edit render from a recipe: cuts, transitions, slow-mo, b-roll cutaways,
grade, then motion graphics (title card, HUD, lower thirds, tracked callouts, captions,
end card). Output is 1080x1920.

    python3 fonzi_recipe.py SOURCE recipe.json --out final.mp4
    python3 fonzi_recipe.py SOURCE recipe.json --out final.mp4 --stage base   # stop after the cut
    python3 fonzi_recipe.py SOURCE recipe.json --out final.mp4 --stage graphics  # reuse the base

SOURCE is a video file or a Google Drive link. See recipe.example.json for every field.
Times in the recipe: clip "start"/"end" are source seconds; everything else inside a clip
("at", broll "at", captions, callouts) is seconds from the start of that clip in the edit.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fonzi_edit as fe  # noqa: E402

W, H, FPS = 1080, 1920, 30
GRADE = "eq=contrast=1.07:saturation=0.9:gamma=0.97,vignette=angle=PI/4.5"


def out_len(c):
    return (c["end"] - c["start"]) / float(c.get("speed", 1))


def timeline(recipe):
    """Annotate clips with edit-time start/end and group numbering. Returns total seconds."""
    t, groups, seen = 0.0, [], {}
    for c in recipe["clips"]:
        c["_start"], c["_end"] = t, t + out_len(c)
        t = c["_end"]
        g = c.get("group")
        if g:
            if g not in seen:
                seen[g] = {"name": g, "start": c["_start"], "end": c["_end"]}
                groups.append(seen[g])
                c["_first"] = True
            else:
                seen[g]["end"] = c["_end"]
    for i, g in enumerate(groups):
        g["index"] = i + 1
    return t, groups


def joins_for(recipe):
    return fe.join_plan(len(recipe["clips"]), recipe.get("transitions", "cut"),
                        recipe.get("transition_seconds", 0.3))


def crop_expr(z, cx, cy):
    if z == 1:
        return ""
    return "crop=iw/%s:ih/%s:(iw-iw/%s)*%s:(ih-ih/%s)*%s," % (z, z, z, cx, z, cy)


def cam_label(z):
    return "CAM 1" if z <= 1.01 else ("CAM 2" if z < 1.45 else "CAM 3")


def cam_plan(c):
    """The virtual cameras of a clip, in order: [{at, zoom, cx, cy, label}]. A clip without
    "cams" is one full-frame camera."""
    cams = [dict(k) for k in c.get("cams", [])] or [{"at": 0}]
    cams.sort(key=lambda k: k["at"])
    if cams[0]["at"] > 0:
        cams.insert(0, {"at": 0})
    for k in cams:
        k.setdefault("zoom", 1.0)
        k.setdefault("cx", 0.5)
        k.setdefault("cy", 0.5)
        k.setdefault("label", cam_label(k["zoom"]))
    return cams


def cam_graph(cams, speed, length):
    """One clip as several hard-cut angles cropped from the same footage."""
    n = len(cams)
    parts = ["[0:v]setpts=(PTS-STARTPTS)/%s,fps=%d,split=%d%s" % (speed, FPS, n, "".join("[s%d]" % i for i in range(n)))]
    for i, k in enumerate(cams):
        end = cams[i + 1]["at"] if i + 1 < n else length + 1
        parts.append("[s%d]trim=%.3f:%.3f,setpts=PTS-STARTPTS,%sscale=%d:%d:flags=lanczos,setsar=1[c%d]"
                     % (i, k["at"], end, crop_expr(k["zoom"], k["cx"], k["cy"]), W, H, i))
    parts.append("%sconcat=n=%d:v=1:a=0[v]" % ("".join("[c%d]" % i for i in range(n)), n))
    return ";".join(parts)


def render_pieces(src, recipe, workdir, has_audio):
    """Cut every clip and b-roll insert to its own small file. Doing it this way (rather than
    one giant filter over the whole source) keeps memory flat."""
    os.makedirs(workdir, exist_ok=True)
    clips, joins, files = recipe["clips"], joins_for(recipe), {"clips": [], "broll": []}
    for i, c in enumerate(clips):
        s = float(c.get("speed", 1))
        ext = (joins[i][1] * s) if i < len(clips) - 1 else 0
        path = os.path.join(workdir, "clip%02d.mp4" % i)
        length = out_len(c) + (joins[i][1] if i < len(clips) - 1 else 0)
        cams = cam_plan(c)
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % c["start"], "-t", "%.3f" % (c["end"] - c["start"] + ext),
               "-i", src]
        if len(cams) > 1:
            cmd += ["-filter_complex", cam_graph(cams, s, length), "-map", "[v]"]
            if has_audio:
                cmd += ["-map", "0:a"]
        else:
            z, cx, cy = cams[0]["zoom"], cams[0]["cx"], cams[0]["cy"]
            vf = ("setpts=(PTS-STARTPTS)/%s,fps=%d,%sscale=%d:%d:flags=lanczos,setsar=1"
                  % (s, FPS, crop_expr(z, cx, cy), W, H))
            cmd += ["-vf", vf]
        if has_audio:
            cmd += ["-af", ("atempo=%s," % s if s != 1 else "") + "aresample=48000,aformat=channel_layouts=stereo"]
        else:
            cmd += ["-an"]
        fe.run(cmd + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-b:a", "192k", path])
        files["clips"].append(path)
    for j, b in enumerate(recipe.get("broll", [])):
        path = os.path.join(workdir, "broll%02d.mp4" % j)
        z, cx, cy = b.get("zoom", 1.3), b.get("cx", 0.5), b.get("cy", 0.5)
        vf = ("fps=%d,crop=iw/%s:ih/%s:(iw-iw/%s)*%s:(ih-ih/%s)*%s,scale=%d:%d:flags=lanczos,setsar=1"
              % (FPS, z, z, z, cx, z, cy, W, H))
        fe.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % b["src"], "-t", "%.3f" % b["dur"], "-i", src,
                "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
                "-pix_fmt", "yuv420p", path])
        files["broll"].append(path)
    return files


def join_graph(recipe, nclips, has_audio):
    clips, joins = recipe["clips"], joins_for(recipe)
    parts, vl, al, at = [], "0:v", "0:a", 0.0
    for k in range(nclips - 1):
        kind, td = joins[k]
        at += out_len(clips[k])
        parts.append("[%s][%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]"
                     % (vl, k + 1, kind, td, at, k))
        vl = "x%d" % k
        if has_audio:
            parts.append("[%s][%d:a]acrossfade=d=%.3f[y%d]" % (al, k + 1, td, k))
            al = "y%d" % k
    # b-roll cutaways: other footage over the picture, the clip's own sound keeps playing
    for j, b in enumerate(recipe.get("broll", [])):
        T = clips[b["clip"]]["_start"] + b["at"]
        parts.append("[%d:v]setpts=PTS-STARTPTS+%.3f/TB,format=yuva420p,fade=t=in:st=%.3f:d=0.1:alpha=1,"
                     "fade=t=out:st=%.3f:d=0.1:alpha=1[b%d]" % (nclips + j, T, T, T + b["dur"] - 0.1, j))
        parts.append("[%s][b%d]overlay=eof_action=pass:enable='between(t,%.3f,%.3f)'[o%d]"
                     % (vl, j, T, T + b["dur"], j))
        vl = "o%d" % j
    parts.append("[%s]%s,format=yuv420p[v]" % (vl, GRADE))
    if has_audio:
        parts.append("[%s]loudnorm=I=-14:TP=-1.5:LRA=11[a]" % al)
    return ";".join(parts)


def render_base(src, recipe, out, has_audio):
    files = render_pieces(src, recipe, os.path.splitext(out)[0] + "-pieces", has_audio)
    inputs = []
    for f in files["clips"] + files["broll"]:
        inputs += ["-i", f]
    graph = join_graph(recipe, len(files["clips"]), has_audio)
    maps = ["-map", "[v]"] + (["-map", "[a]"] if has_audio else [])
    fe.run(["ffmpeg", "-v", "error", "-y", "-filter_threads", "2"] + inputs +
           ["-filter_complex", graph] + maps +
           ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])


def cam_tags(c, first=False):
    """When the CAM badge shows: at every angle change, and on the very first shot."""
    cams = cam_plan(c)
    tags = []
    for k, cam in enumerate(cams):
        if k > 0 or first:
            tags.append({"label": cam["label"], "at": cam["at"] + 0.1, "dur": 2.2})
    return tags


def overlay_plan(recipe, total, groups):
    clips, callouts, captions = [], [], []
    for c in recipe["clips"]:
        clips.append({"start": c["_start"], "end": c["_end"], "group": c.get("group"),
                      "first_of_group": bool(c.get("_first")),
                      "group_index": next((g["index"] for g in groups if g["name"] == c.get("group")), 0),
                      "bracket": c.get("bracket"), "cams": cam_tags(c, first=not clips),
                      "slow": c.get("speed") if float(c.get("speed", 1)) != 1 else None})
        for k in c.get("callouts", []):
            callouts.append(dict(k, abs_at=c["_start"] + k["at"]))
        for k in c.get("captions", []):
            captions.append(dict(k, abs_at=c["_start"] + k["at"]))
    plan = {k: recipe[k] for k in ("title", "subtitle", "title_seconds", "cta", "cta_sub",
                                   "handle", "end_seconds") if k in recipe}
    plan.update(total=total, groups=groups, clips=clips, callouts=callouts, captions=captions)
    return plan


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source")
    ap.add_argument("recipe")
    ap.add_argument("--out", default="fonzi-final.mp4")
    ap.add_argument("--stage", choices=["all", "base", "graphics"], default="all")
    args = ap.parse_args(argv)

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base = os.path.splitext(out)[0] + ".base.mp4"
    with open(args.recipe) as fh:
        recipe = json.load(fh)
    src = fe.fetch(args.source, os.path.join(os.path.dirname(out), "fonzi-source"))
    duration, fps, has_audio = fe.probe(src)
    total, groups = timeline(recipe)

    if args.stage in ("all", "base"):
        render_base(src, recipe, base, has_audio)
    if args.stage == "base":
        print(json.dumps({"base": base, "seconds": round(total, 2)}))
        return

    import fonzi_overlay as ov
    plan = overlay_plan(recipe, total, groups)
    tracks = ov.track_callouts(base, plan["callouts"])
    frames = ov.compose(base, out, plan, tracks, int(round(total * FPS)))
    print(json.dumps({"output": out, "seconds": round(frames / FPS, 2), "base": base,
                      "callouts_tracked": len(tracks)}))


if __name__ == "__main__":
    main()
