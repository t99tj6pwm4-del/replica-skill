# Colour grade + transitions spec (from Alfonso, 2026-11-19, verbatim intent)
Derived from his reference reels (Canyon Hepi, Brayan Jimenez, Jon Cudi, Brandon Bartley). We rebuild the
techniques on HIS footage only; never download or reuse their videos, overlays or LUT files.

## Colour grade: 5 steps, in this exact order (the LUT comes second, not last)
1. **Rec 709 conversion** (LOG > DaVinci Wide Gamut > Rec 709). Only if the footage is log; never grade log directly.
   His iPhone footage is normally already Rec 709, so this step is usually a no-op.
2. **Film look base: Kodak 2383 D60-style print emulation.** The foundation. We build our own 2383-style curve/LUT
   (no third-party LUT file unless he sends one he owns).
3. **Primaries:** white balance warm, fix exposure, saturation medium-high. Only teal and orange/wood/skin read as
   saturated; everything else pulled toward teal/grey.
4. **Teal & orange** (colour warper / hue curves). Shadows deep teal `#093647`, midtones teal `#1B4E5B`, skin warm
   `#6F4A37`, wood warm `#432418`. Crush blacks hard (dark walls near-black, almost no detail). Skin clearly warmer
   than the cool teal background: that split is the whole look.
5. **Film effects:** halation + glow (soft orange-white halo on bright edges: windows, skylights, bright logos),
   film grain throughout (stronger in shadows/flat areas), bleach bypass for contrast. Highlights warm-white and
   allowed to blow out at windows/doorways; don't recover them.

**Titles stay mustard gold `#D4A017`, Montserrat.**

## Transitions (in this order)
### Brayan Jimenez
1. **Fade to black (filmed):** gym item (tricep rope) pushed into the lens until black; next clip starts from black and fades in (e.g. blurred cable pole in foreground, lifter behind).
2. **Match cut (filmed):** one rep from two angles; hard cut on the exact same frame of the rep (low shot up at lights/rack -> face close-up).
3. **Cut-out zoom:** mask out a foreground item (black plate), invert the mask, next clip under it: plate fills the screen, goes dark, next clip revealed.
### Jon Cudi (about 2 s each)
1. **Luma fade:** highlights bloom/blow white first, dissolve through the highlights to the next shot (keyframe exposure up + cross-dissolve).
2. **Flicker mask:** a flickering film-frame / light-leak overlay (magenta/orange/purple bands, film-edge text) across the cut, opacity flickered a few frames. We synthesise our own overlay (no "KODAK" trademark text).
3. **Film burn:** a warm flare expands and burns white/orange across the frame into the next shot (Screen blend, scaled up). Own synthesised burn.
4. **Camera wipe (filmed):** whip-pan past a foreground object (weight stack, cables) so it covers the lens; cut while covered.
### Brandon Bartley
1. **Mask transition (filmed), "changing scenes":** foreground object (rack upright / plate) sweeps across as camera tracks; cut while covered.
2. **Rise effect, "revealing":** he rises up out of the top of frame and his body is the wipe; or keyframe the top clip's Y up off frame.
3. **Pin effect (stop motion, filmed locked-off), "establishing":** frozen poses jumping in stop-motion steps from one locked-off camera; clone shots (3 copies of him in one frame) by masking each pose in.

## Can do from any footage vs needs filming
- Any footage (editor alone): luma fade, flicker mask, film burn, cut-out zoom (rembg/birefnet mask), rise (keyframed), fade-to-black (synthetic).
- Needs him to film it: true fade-to-black lens touch, match cut (2 angles of one rep), whip-pan camera wipe, foreground-object mask transition, real rise, pin/stop-motion + clones (locked-off tripod).
