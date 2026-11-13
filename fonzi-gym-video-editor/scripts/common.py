"""Shared helpers for the fonzi-gym-video-editor pipeline scripts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "input"
OUT = ROOT / "output"
WORK = OUT / "work"
SONGS = ROOT / "songs"
POSTED = ROOT / "posted"
LEDGER = POSTED / "ledger.json"
REMOTION = ROOT / "remotion"

W, H, FPS = 1080, 1920, 30


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def run(cmd: list, check: bool = True, **kw) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if check and p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-2500:]
        die(f"command failed ({p.returncode}): {' '.join(cmd[:6])} ...\n{tail}")
    return p


def resolve(path: str | Path) -> Path:
    """Paths in JSON files are relative to the project root."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def rel(path: str | Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        die(f"missing file: {rel(path)}")
    return json.loads(path.read_text())


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def probe(path: Path) -> dict:
    """ffprobe summary with display (rotation-corrected) dimensions."""
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    raw = json.loads(p.stdout)
    info = {"path": rel(path), "duration": float(raw["format"].get("duration", 0)), "video": None, "audio": None}
    for s in raw["streams"]:
        if s["codec_type"] == "video" and info["video"] is None:
            w, h = int(s["width"]), int(s["height"])
            rot = 0
            for sd in s.get("side_data_list", []):
                if "rotation" in sd:
                    rot = int(float(sd["rotation"]))
            if abs(rot) % 180 == 90:
                w, h = h, w
            num, den = (s.get("avg_frame_rate") or "0/1").split("/")
            fps = float(num) / float(den) if float(den) else 0.0
            info["video"] = {
                "codec": s.get("codec_name"),
                "width": w,
                "height": h,
                "fps": round(fps, 3),
                "pix_fmt": s.get("pix_fmt"),
                "duration": float(s.get("duration") or info["duration"]),
            }
        elif s["codec_type"] == "audio" and info["audio"] is None:
            info["audio"] = {
                "codec": s.get("codec_name"),
                "sample_rate": int(s.get("sample_rate") or 0),
                "channels": s.get("channels"),
                "duration": float(s.get("duration") or info["duration"]),
            }
    return info


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(path: Path, n: int = 16) -> list[str]:
    """Perceptual fingerprint: n evenly spaced frames -> 64-bit difference hashes.
    Survives re-encoding, so the same video exported twice is still caught."""
    dur = probe(path)["duration"]
    hashes = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        p = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
             "-vf", "scale=9:8,format=gray", "-f", "rawvideo", "-"],
            capture_output=True,
        )
        px = p.stdout
        if len(px) < 72:
            continue
        bits = 0
        for r in range(8):
            for c in range(8):
                bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
        hashes.append(f"{bits:016x}")
    return hashes


def fingerprint_distance(a: list[str], b: list[str]) -> float:
    """Mean hamming distance (0 = identical, ~32 = unrelated)."""
    n = min(len(a), len(b))
    if n == 0:
        return 64.0
    return sum(bin(int(x, 16) ^ int(y, 16)).count("1") for x, y in zip(a[:n], b[:n])) / n


def find_duplicate(final: Path | None, source_sha: str | None = None, threshold: float = 6.0):
    """Return the ledger entry this video duplicates, or None."""
    ledger = load_json(LEDGER, default={"posted": []})
    if not ledger["posted"]:
        return None
    fsha = sha256(final) if final else None
    fp = fingerprint(final) if final else None
    for e in ledger["posted"]:
        if fsha and e.get("sha256") == fsha:
            return {**e, "match": "identical file"}
        if source_sha and e.get("source_sha256") == source_sha:
            return {**e, "match": "same raw footage"}
        if fp and e.get("fingerprint") and fingerprint_distance(fp, e["fingerprint"]) <= threshold:
            return {**e, "match": "visually the same video"}
    return None


def check_generator(name: str, pcfg: dict, cfg: dict, purpose: str) -> None:
    """Sora: never. Omni: only Google Flow, only for multicam reframes. Everything else is refused."""
    text = f"{name} {pcfg.get('model', '')} {pcfg.get('reframe_model', '')}".lower()
    if any(b in text for b in cfg["generator"].get("blocked", [])) or "sora" in text:
        die(f"generator {name!r} is blocked: no Sora, ever")
    if "omni" in f"{name} {pcfg.get('model', '')}".lower() and name != "google-flow":
        die(f"{name!r}: Omni is allowed only inside Google Flow for multicam reframes")
    if name == "google-flow" and purpose not in ("multicam", "broll"):
        die("Google Flow is used only for multicam angles and B-roll")


def base_video() -> Path:
    """The picture the Text/Visuals Agent works on: the multicam version when that step ran, else the cut."""
    mc = OUT / "multicam_version.mp4"
    return mc if mc.exists() and (WORK / "multicam_map.json").exists() else OUT / "cut_version.mp4"


def brand() -> dict:
    return load_json(ROOT / "config" / "brand.json")
