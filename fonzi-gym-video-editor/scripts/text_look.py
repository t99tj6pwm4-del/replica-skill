#!/usr/bin/env python3
"""THE text look (Alfonso, 2026-11-23, Director answer 24; replaces gold everywhere).

Pure white text, no colour, no stroke / outline, no box, no background bar. Under the sharp text, bottom to top:
    1. dark shadow   black, gaussian blur 40 px, 35 %, no offset (hugs the letters, keeps white readable on bright footage)
    2. wide glow     white, blur 22 px, 45 %
    3. tight glow    white, blur 6 px, 80 %
    4. sharp text    white, 100 %
The numbers live in ONE place, config.yaml `text_look:`; this module (Python: style_fx intro, layered_title) and
Remotion (props.textLook, injected by render_final.py; remotion/src/Overlay.tsx <Glow>) both read them.
Blur = gaussian standard deviation in px at 1080x1920 (PIL GaussianBlur(radius) == CSS filter: blur(radius)).

    python3 scripts/text_look.py show        # print the look as config gives it
    python3 scripts/text_look.py demo OUT.png  # a sample word over a bright + a dark half, for a quick look
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))

DEFAULT = {
    "color": "#FFFFFF",
    "layers": [
        {"name": "shadow", "color": "#000000", "blur": 40, "opacity": 0.35},
        {"name": "wide_glow", "color": "#FFFFFF", "blur": 22, "opacity": 0.45},
        {"name": "tight_glow", "color": "#FFFFFF", "blur": 6, "opacity": 0.80},
    ],
    "neutral_max_spread": 12,
    "box_alpha_max": 0.5,
    "pulse_glow_boost": 0.6,
}


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


@lru_cache(maxsize=1)
def look() -> dict:
    """config.yaml text_look merged over the defaults (the defaults ARE Alfonso's numbers)."""
    try:
        from common import load_config
        cfg = load_config().get("text_look") or {}
    except Exception:
        cfg = {}
    out = dict(DEFAULT)
    out.update({k: v for k, v in cfg.items() if v is not None})
    return out


def text_rgb() -> tuple[int, int, int]:
    return hex_rgb(look()["color"])


def pad() -> int:
    """How far the look reaches past the letters (3 sigma of the widest blur)."""
    return int(3 * max(float(l["blur"]) for l in look()["layers"])) + 2


def _tinted(alpha: Image.Image, rgb, opacity: float) -> Image.Image:
    a = alpha.point(lambda v: int(round(min(255.0, v * opacity))))
    lay = Image.new("RGBA", alpha.size, tuple(rgb) + (0,))
    lay.putalpha(a)
    return lay


def under(layer: Image.Image, boost: float = 0.0) -> Image.Image:
    """Shadow + wide glow + tight glow for `layer` (RGBA, any size), WITHOUT the sharp text. `boost` raises the two
    glow opacities by x(1 + boost) (the intro pulse on a beat). Same size as `layer`, transparent elsewhere."""
    bb = layer.getchannel("A").getbbox()
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    if not bb:
        return out
    p = pad()
    x0, y0 = max(0, bb[0] - p), max(0, bb[1] - p)
    x1, y1 = min(layer.width, bb[2] + p), min(layer.height, bb[3] + p)
    a = layer.getchannel("A").crop((x0, y0, x1, y1))
    crop = Image.new("RGBA", a.size, (0, 0, 0, 0))
    for l in look()["layers"]:
        op = float(l["opacity"])
        if l["name"] != "shadow" and boost:
            op = min(1.0, op * (1 + boost))
        blurred = a.filter(ImageFilter.GaussianBlur(float(l["blur"])))
        crop = Image.alpha_composite(crop, _tinted(blurred, hex_rgb(l["color"]), op))
    out.paste(crop, (x0, y0))
    return out


def white(layer: Image.Image) -> Image.Image:
    """The sharp text: the layer's own alpha in the look's text colour (pure white)."""
    return _tinted(layer.getchannel("A"), text_rgb(), 1.0)


def stack(layer: Image.Image, boost: float = 0.0, keep_rgb: bool = False) -> Image.Image:
    """The full look for one text layer: shadow -> wide glow -> tight glow -> sharp white text, as ONE RGBA layer.
    keep_rgb=True keeps the layer's own RGB on top (it is already white / neutral, e.g. glitch ghost copies)."""
    return Image.alpha_composite(under(layer, boost), layer if keep_rgb else white(layer))


def for_remotion() -> dict:
    """props.textLook for Overlay.tsx (<Glow>): the same numbers, nothing else."""
    lk = look()
    return {"color": lk["color"], "layers": [{"name": l["name"], "color": l["color"], "blur": float(l["blur"]),
                                              "opacity": float(l["opacity"])} for l in lk["layers"]]}


def tint_spread(rgba: np.ndarray, min_alpha: int = 128) -> int:
    """Largest channel spread (max - min of R, G, B) over the pixels with alpha >= min_alpha: 0 = pure grey/white."""
    on = rgba[..., 3] >= min_alpha
    if not on.any():
        return 0
    px = rgba[..., :3][on].astype(np.int16)
    return int((px.max(-1) - px.min(-1)).max())


def box_pixels(rgba: np.ndarray, alpha_max: float | None = None) -> int:
    """Dark (luma < 128) pixels more opaque than box_alpha_max: a card / bar / panel. The look's shadow peaks well
    under it (35 %), so any hit means something drew a box behind the text."""
    am = int(255 * (alpha_max if alpha_max is not None else float(look()["box_alpha_max"])))
    rgb = rgba[..., :3].astype(np.float32)
    luma = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    return int(((rgba[..., 3] > am) & (luma < 128)).sum())


def _demo(out: Path):
    from PIL import ImageDraw, ImageFont
    root = Path(__file__).resolve().parent.parent
    W, H = 1080, 700
    bg = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    ImageDraw.Draw(bg).rectangle((0, 0, W, H // 2), fill=(236, 232, 224, 255))
    f = ImageFont.truetype(str(root / "remotion" / "public" / "fonts" / "Montserrat.ttf"), 150)
    try:
        f.set_variation_by_name("Black")
    except Exception:
        pass
    for cy in (H // 4, 3 * H // 4):
        t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((W // 2, cy), "GRIND DAY", font=f, anchor="mm", fill=(255, 255, 255, 255))
        bg = Image.alpha_composite(bg, stack(t))
    bg.convert("RGB").save(out)
    print(out)


if __name__ == "__main__":
    import json
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        _demo(Path(sys.argv[2] if len(sys.argv) > 2 else "text_look_demo.png"))
    else:
        print(json.dumps(look(), indent=1))
