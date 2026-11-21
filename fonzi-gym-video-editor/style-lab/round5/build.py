#!/usr/bin/env python3
"""Style Lab round 5: the new intro card (Alfonso's pick: Rubik Dirt title, gold #D4A017, the same drips as his
Fonzi logo, the Fonzi logo behind the title).

    python3 style-lab/round5/build.py [r5-01 ... r5-06]

Base for every option: the first 3.0 s (90 frames) of output/multicam_version.mp4 (him curling, face upper-middle,
hard cut to the leg-extension shot at 2.0 s). Same words everywhere: "LOCKED IN" / "5 LIFTS. ONE SONG."
Audio: the cut's own song for those 3 s, untouched, with our sfx/*.wav under it. No grade, no scrim.

Section "Logo behind the title" (title drips fixed at heavy):
  r5-01  logo flat behind the title, white 85 %, lower-middle; logo + title land together on beat 1
  r5-02  same, but the logo is layered BEHIND HIM (rembg cut-out, as layered_title.py); title in front of him
  r5-03  same as 01, but the logo arrives with the locked round-2 flicker-on (clicks); title slams on beat 1 after it
Section "Drip on the title" (logo fixed as in r5-01):
  r5-04  slow drips   r5-05  heavy drips   r5-06  wet paint (drips creep and stay)
Drips are gold and start at the real bottom edges of the Rubik Dirt letters (drip tips found on the title alpha).

Writes output/style_lab/r5/<id>_full.mp4, <id>_prev.mp4, <id>.jpg and prints a per-frame face / safe-area report.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import layered_title as lt  # noqa: E402
import style_fx as sf       # noqa: E402  (drip_layer: the logo's slow / heavy / wet drips)

W, H, FPS, N = 1080, 1920, 30, 90
SRC = ROOT / "output" / "multicam_version.mp4"
OUT = ROOT / "output" / "style_lab" / "r5"
TMP = OUT / "tmp"
SFX = ROOT / "sfx"
LOGO = ROOT / "brand" / "fonzi_logo.png"
TITLE_FONT = ROOT / "brand" / "fonts" / "RubikDirt-Regular.ttf"
SUB_FONT = ROOT / "remotion" / "public" / "fonts" / "Montserrat.ttf"
GOLD = (212, 160, 23)                      # #D4A017
TITLE, SUB = ("LOCKED", "IN"), "5 LIFTS. ONE SONG."
LAND = 20                                  # beat 1 (0.667 s, cut_map beat period 0.6676)
SHOT_CUT = 60                              # hard cut to the leg shot at 2.0 s (no face after it)
FACE = (400, 170, 900, 730)                # cap + face + beard over ALL of shot 1, +20 px margin (re-measured this
                                           # round: head drops on f45-59, chin reaches y ~710, x up to ~880)
SAFE_TOP, SAFE_BOTTOM = 110, H - 420
FLICKER = [0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1]   # the locked round-2 flicker-on
FLICKER_AT = 3                             # flicker runs f3-f16, logo solid from f16, title slams on beat f20
DRIPS = {"slow": (6, 2.4, 90, True), "heavy": (14, 1.7, 150, True), "wet": (14, 0, 170, False)}  # = style_fx.logo

# layout (px, 1080x1920)
LOGO_SIZE, LOGO_TOP = 1098, 552            # the art inside the png (x 139-867, y 180-865 of 1024) spans
                                           # x ~150-930, y ~745-1479: below the face box, inside the safe area
TITLE_W = 700                              # LOCKED width: the logo is slightly bigger than the title block
Y1, Y2 = 1000, 1165                         # LOCKED / IN centres
Y_SUB = 1305


# ---------------- layers ----------------
def title_font(width):
    lo, hi = 10, 600
    while lo < hi:
        mid = (lo + hi + 1) // 2
        bb = ImageFont.truetype(str(TITLE_FONT), mid).getbbox("LOCKED")
        lo, hi = (mid, hi) if bb[2] - bb[0] <= width else (lo, mid - 1)
    return ImageFont.truetype(str(TITLE_FONT), lo)


def line(layer, text, f, cy, color, track=0):
    d = ImageDraw.Draw(layer)
    hb = f.getbbox("H")
    y = cy - (hb[3] + hb[1]) // 2
    if not track:
        bb = f.getbbox(text)
        d.text((W // 2 - (bb[2] - bb[0]) // 2 - bb[0], y), text, font=f, fill=color)
        return
    x = W / 2 - (sum(f.getlength(c) for c in text) + track * (len(text) - 1)) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=color)
        x += f.getlength(c) + track


def build_layers():
    big = title_font(TITLE_W)
    title = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    line(title, TITLE[0], big, Y1, GOLD + (255,))
    line(title, TITLE[1], big, Y2, GOLD + (255,))
    sub_f = ImageFont.truetype(str(SUB_FONT), 46)
    sub_f.set_variation_by_name("ExtraBold")
    sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    line(sub, SUB, sub_f, Y_SUB, (255, 255, 255, 255), track=8)
    lg = Image.open(LOGO).convert("RGBA").resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    a = lg.getchannel("A").point(lambda v: int(v * 0.85))          # white at 85 %
    lg = Image.merge("RGBA", (*[Image.new("L", lg.size, 255)] * 3, a))
    logo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    logo.paste(lg, ((W - LOGO_SIZE) // 2, LOGO_TOP), lg)
    return title, sub, logo, big.size


def title_tips(alpha: np.ndarray, n: int, length: int, seed=5):
    """Drip starts on the title: the real bottom edges of the Rubik Dirt letters. Same idea as round 2's
    drip_tips (a bottom edge with nothing lower right next to it), but the letters are block letters with a
    dirt texture, not drip stems: fill the dirt specks first so a speck is never read as a bottom edge, and
    allow any stem width (the drip width comes from the 14-26 px range the logo's drips use)."""
    sil = Image.fromarray((alpha > 0.5).astype(np.uint8) * 255, "L")
    sil = sil.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))     # close the dirt holes
    op = np.array(sil) > 128
    edge = op & ~np.roll(op, -1, 0)
    ys, xs = np.nonzero(edge)
    rng = np.random.default_rng(seed)
    cand = []
    for y, x in zip(ys, xs):
        if y < 20 or y > H - 30 or not op[y - 14, x]:
            continue
        if ((np.abs(xs - x) <= 22) & (ys > y) & (ys <= y + 30)).any():     # something just below: not a bottom
            continue
        if op[y + 1: y + length + 30, max(0, x - 26): x + 27].any():          # would run into the line below
            continue
        if not (op[y - 4, max(0, x - 8)] and op[y - 4, min(W - 1, x + 8)]):  # not on a letter's outer corner
            continue
        cand.append((y, x))
    rng.shuffle(cand)
    cand.sort(key=lambda c: -c[0])                                          # lowest edges first (IN, then LOCKED)
    tips = []
    for y, x in cand:
        if all(abs(x - tx) > 38 for tx, ty, _ in tips if abs(y - ty) < 60):
            tips.append((int(x), int(y), int(rng.integers(16, 27))))
    rng.shuffle(tips)
    return tips[:n]


def gold_drips(tips, k, ph, kind):
    _, period, length, drops = DRIPS[kind]
    d = sf.drip_layer(tips, k, ph, period, length, drops)
    d[..., :3] = np.array(GOLD, np.float32) / 255
    fade = np.clip((SAFE_BOTTOM - 12 - np.arange(H, dtype=np.float32)) / 30, 0, 1)   # falling drops end at 1488
    d[..., 3] *= fade[:, None]
    return Image.fromarray((d * 255).astype(np.uint8), "RGBA")


def scaled(layer, s, cx, cy):
    if abs(s - 1) < 1e-3:
        return layer
    w, h = int(round(W * s)), int(round(H * s))
    big = layer.resize((w, h), Image.BICUBIC)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(big, (int(round(cx - cx * s)), int(round(cy - cy * s))), big)
    return out


def with_alpha(layer, a):
    if a >= 1:
        return layer
    r = layer.copy()
    r.putalpha(r.getchannel("A").point(lambda v: int(v * a)))
    return r


def shadow_of(layer, blur=10, opacity=0.6):
    """Tight soft shadow behind the title only (fills the dirt specks so the gold reads over the white logo).
    Not a scrim: it follows the letters."""
    a = layer.getchannel("A").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: int(min(255, v * 1.6) * opacity))
    sh = Image.new("RGBA", (W, H), (8, 8, 10, 0))
    sh.putalpha(a)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(sh, (0, 6), sh)
    return out


def ease_out(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 3


# ---------------- source ----------------
def load_frames():
    src = TMP / "src"
    if len(list(src.glob("f*.png"))) != N:
        src.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vf",
                        f"trim=end_frame={N},setpts=PTS-STARTPTS,scale={W}:{H}", "-fps_mode", "passthrough",
                        src / "f%04d.png"], check=True)
    return sorted(src.glob("f*.png"))


_MASKS = None


def person_masks(srcs):
    """His cut-out on every frame, per shot (so the in-between frames never mix the two shots)."""
    global _MASKS
    if _MASKS is None:
        session, model = lt.cut_session()
        a = lt.smooth_masks(lt.raw_masks(session, model, srcs[:SHOT_CUT]))
        b = lt.smooth_masks(lt.raw_masks(session, model, srcs[SHOT_CUT:]))
        _MASKS = (a + b, model)
    return _MASKS


# ---------------- checks ----------------
class Checker:
    """Every frame: every drawn pixel (title, subtitle, drips, VISIBLE logo) inside the safe area, none in the
    face box while his face is on screen (shot 1)."""
    def __init__(self, cid):
        self.cid, self.issues, self.yr, self.frames = cid, [], [H, 0], 0

    def __call__(self, k, alpha):
        self.frames += 1
        ys, xs = np.nonzero(alpha > 20)
        if not len(ys):
            return
        self.yr = [min(self.yr[0], int(ys.min())), max(self.yr[1], int(ys.max()))]
        if ys.min() < SAFE_TOP or ys.max() > SAFE_BOTTOM:
            self.issues.append(f"f{k}: graphics y {ys.min()}-{ys.max()} outside safe area")
        if k < SHOT_CUT:
            x0, y0, x1, y1 = FACE
            n = int(((xs >= x0) & (xs < x1) & (ys >= y0) & (ys < y1)).sum())
            if n:
                self.issues.append(f"f{k}: {n} px in face box")

    def result(self):
        ok = not self.issues
        msg = (f"{self.frames} frames checked, graphics y {self.yr[0]}-{self.yr[1]} "
               f"(safe {SAFE_TOP}-{SAFE_BOTTOM}), face box {FACE} clear" if ok
               else f"{len(self.issues)} issues: {self.issues[:6]}")
        print(f"[{self.cid}] {'OK' if ok else 'FAIL'}: {msg}")
        return {"ok": ok, "frames": self.frames, "y_range": self.yr, "issues": self.issues[:20]}


# ---------------- one option ----------------
def option(cid, srcs, logo_mode="flat", logo_in="land", drips="heavy"):
    title, sub, logo, size = build_layers()
    tips = title_tips(np.asarray(title, np.float32)[..., 3] / 255, DRIPS[drips][0], DRIPS[drips][2])
    ph = np.random.default_rng(11).uniform(0, max(DRIPS[drips][1], 1), len(tips))
    masks = person_masks(srcs)[0] if logo_mode == "behind" else None
    chk = Checker(cid)
    gcx, gcy = W / 2, (Y1 + Y2) / 2
    slam = [1.4, 1.27, 1.15, 1.06, 1.0]       # 4 frames 1.4 -> 1.0 into the beat (last round's clean slam)
    logo_a = np.asarray(logo)[..., 3]
    covered = []
    out = []
    for k, p in enumerate(srcs):
        img = Image.open(p).convert("RGBA")
        # logo
        if logo_in == "flicker":
            i = k - FLICKER_AT
            la = 0.0 if i < 0 else (FLICKER[i] if i < len(FLICKER) else 1.0)
        else:
            la = min(1.0, max(0.0, (k - (LAND - 4)) / 4))          # fades up under the slam, full on the beat
        vis = np.zeros((H, W), np.uint8)
        comp = img
        if la > 0:
            comp = Image.alpha_composite(comp, with_alpha(logo, la))
            vis = (logo_a * la).astype(np.uint8)
            if masks is not None:
                m = masks[k]
                person = img.copy()
                person.putalpha(m)
                comp = Image.alpha_composite(comp, person)
                ma = np.array(m) > 128
                vis = np.where(ma, 0, vis).astype(np.uint8)
                if k in (40, 75):
                    covered.append(round(float((ma & (logo_a > 20)).sum()) / float((logo_a > 20).sum()), 3))
        # title + subtitle + drips
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = k - (LAND - 4)
        if d >= 0:
            s = slam[d] if d < len(slam) else 1.0
            txt = Image.alpha_composite(txt, with_alpha(scaled(title, s, gcx, gcy), 0.5 + 0.5 * min(1, d / 2)))
        if k > LAND:
            dl = gold_drips(tips, k - LAND, ph, drips)
            txt = Image.alpha_composite(dl, txt)                   # drips run out from under the letters
        sd = k - (LAND + 8)
        if sd >= 0:
            e = ease_out(sd / 6)
            sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sl.paste(sub, (0, int(18 * (1 - e))), sub)
            txt = Image.alpha_composite(txt, with_alpha(sl, e))
        if d >= 0:
            comp = Image.alpha_composite(Image.alpha_composite(comp, shadow_of(txt)), txt)
        chk(k, np.maximum(vis, np.array(txt.getchannel("A"))))
        out.append(comp)
    res = chk.result()
    res["tips"] = len(tips)
    if covered:
        res["logo_covered_by_him"] = {"f40": covered[0], "f75": covered[1]}
        res["cut_model"] = person_masks(srcs)[1]
        print(f"[{cid}] logo covered by him: {res['logo_covered_by_him']}")
    sounds = [("whoosh", LAND / FPS - 0.30, -14), ("impact", LAND / FPS - 0.02, -5)]
    if logo_in == "flicker":
        sounds += [("click", (FLICKER_AT + i) / FPS, -10) for i in range(len(FLICKER))
                   if FLICKER[i] and (i == 0 or not FLICKER[i - 1])]
    return out, sounds, res


# ---------------- encode ----------------
def encode(frames, cid, sounds):
    pic = TMP / f"{cid}.pic.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                          "-pix_fmt", "yuv420p", str(pic)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.asarray(f.convert("RGB"), np.uint8).tobytes())
    p.stdin.close()
    assert p.wait() == 0
    dur = N / FPS
    full, prev = OUT / f"{cid}_full.mp4", OUT / f"{cid}_prev.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", SRC]
    parts, labels = [f"[1:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS[song]"], ["[song]"]
    for i, (name, at, db) in enumerate(sounds):
        cmd += ["-i", SFX / f"{name}.wav"]
        ms = max(0, int(at * 1000))
        parts.append(f"[{i + 2}:a]volume={db}dB,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fc = ";".join(parts + [f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
                           f"alimiter=limit=0.8:level=0,atrim=0:{dur:.3f}[a]"])     # limit 0.8 = -1.9 dB
    subprocess.run([str(c) for c in cmd + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                                           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}",
                                           "-movflags", "+faststart", full]], check=True)
    # same small muted preview as round 1's finish()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(full), "-an", "-vf", "scale=360:640,fps=30",
                    "-c:v", "libx264", "-crf", "30", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(prev)], check=True)
    pic.unlink()
    print(f"{cid}: full {full.stat().st_size // 1024} KB  preview {prev.stat().st_size // 1024} KB")


OPTIONS = {
    "r5-01": dict(logo_mode="flat", logo_in="land", drips="heavy"),
    "r5-02": dict(logo_mode="behind", logo_in="land", drips="heavy"),
    "r5-03": dict(logo_mode="flat", logo_in="flicker", drips="heavy"),
    "r5-04": dict(logo_mode="flat", logo_in="land", drips="slow"),
    "r5-05": dict(logo_mode="flat", logo_in="land", drips="heavy"),
    "r5-06": dict(logo_mode="flat", logo_in="land", drips="wet"),
}
STILL = 56          # 1.87 s: title settled, drips running, still on his face shot


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    srcs = load_frames()
    report_p = OUT / "check_report.json"
    report = json.loads(report_p.read_text()) if report_p.exists() else {}
    for cid in sys.argv[1:] or OPTIONS:
        frames, sounds, res = option(cid, srcs, **OPTIONS[cid])
        assert len(frames) == N
        encode(frames, cid, sounds)
        frames[STILL].convert("RGB").save(OUT / f"{cid}.jpg", quality=90)
        report[cid] = res
    report_p.write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
