# Style Lab round 7: HyperFrames intro options (plan)

These are upgrades of the locked intro (STYLE.md rule 0, round 6 r6-01 / r6-03), not replacements. Alfonso keeps or
drops each one. The production intro (`style_fx.py intro`, `finish_fx.py`) does not change in this round.

- Shared values: `style_sheet.json`. Orders: `work_orders.json`. Outputs go only to `output/style_lab/r7/<id>/`.
- Same hook shot and song window as round 6: the first 3.0 s (90 frames) of `output/multicam_version.mp4`. Beats
  are at frames 20 / 40 / 60 / 80. The shot cuts at frame 60. Whoosh is at 0.367 s (-14 dB) and impact at 0.647 s
  (-5 dB), both under his song.
- **r7-00 (shared base, runs first, alone):** source frames, birefnet cut-out masks (about 14 min), the plate
  (footage, then the logo, then him), the shared audio mix, a reference title PNG, and `composite.py`. All five
  options use this identical base and compositor, so the only difference between them is the title or logo motion.
- **Options (run in parallel after r7-00).** Each is one HyperFrames RGBA png-sequence overlay, composited by
  `r7-00/composite.py`:
  - r7-01 title slams in on beat 1 (headline-slam), then the locked strobe
  - r7-02 a gold sheen sweeps through the letters (text-shimmer), with the locked strobe
  - r7-03 an RGB split of the gold's own channels on each beat (rgb-glitch-text), after the locked burst
  - r7-04 the logo behind him gets 3D depth and swings in (CSS 3D on the PNG), with the locked strobe title
  - r7-05 scattered letters smash together on beat 1 (char-slam-explode), then the locked pulse
- Blocks left out on purpose: beat-accent (flash on the hit), texture-mask-text (stock texture images),
  glass-shard-title (fog/tint), shutter-slam (too busy), neon / kinetic captions (not this look). The registry
  extruded-logo block works only on text, so r7-04 uses its swing timing as a reference only.

## Review checklist (supervisor, per option and side by side)
1. `check.json` is all OK: safe area 110-1500, title band 860-1380 and face box [400,170,900,730] clear on f0-59,
   and the title at rest sits within 6 px of `r7-00/ref/title_ref.png`.
2. ffprobe: 1080x1920, 30 fps, h264 + aac, 3.000 s. The `.jpg` is frame 30.
3. Same gold #D4A017, Rubik Dirt 166 px, the same subtitle (Montserrat ExtraBold 46, +8 tracking, y 1305, in at
   f28) in all five. Put the frame 50 stills next to each other.
4. On the beat: the landing or burst hits exactly f20 with the impact. Later accents hit only f40/60/80. Check
   frames 19/20/21 and 39/40/41.
5. Never-list: no white flash on a beat (title never brighter than #ECD497), no drips, no logo flicker-on, no
   dark tint / scrim / grade, no registry demo media or remote fonts, footage not shaken.
6. Logo: whole logo in the frame, behind him (he is always in front), no more than 2500 px on his face. For
   r7-04, its own plate also passes this.
7. Audio is byte-identical across the options (`r7-00/audio_mix.wav`), and his song level is untouched.
8. A fix goes back to the one worker that owns it, then I check again. Only then do the options go to Alfonso.
