# Style Lab round 8 (2026-11-23): white text look + video-inside-text intro

Alfonso: "Run both through Style Lab so I can help pick." Both are BUILT and wired into production behind config
flags, and neither is the shipped default until he picks:
- white text look (Director answer 24): `config.yaml text_look.enabled: false` (shipped = gold). One render:
  `render_final.py --text-look white`.
- video-inside-text intro (Director answer 25): `config.yaml intro.default_style: rotation` (shipped = the round 7
  strobe / pulse / glitch / smash cycle). One render: `render_final.py --intro-style video_text`.
Picking a card = set that flag (+ for A2-A4 the layer numbers in `text_look.layers`; for B2-B4 the keys in
`intro.video_text`), then STYLE.md is updated.

- Shared values: `style_sheet.json`. Orders: `work_orders.json`. Cards: `cards.json` (id, section, title,
  description, mp4, jpg). Build: `python3 style-lab/round8/build.py all` (or `A2 B3 ...`).
- Outputs only in `output/style_lab/r8/<id>/`: `card.mp4` (1080x1920 h264 + aac, his song), `card.jpg`, `meta.json`.
- Source: Grind Day, the opener-test copy `output/white_look_test/` (hook 0-4.133 s, clean multicam picture).
  Every card is made by production code (style_fx / layered_title / Remotion Overlay.tsx / intro_video_text.py).

## Section A: white text look (same Grind Day moments in all four)
Card video = the intro title (strobe, Grind Day's pick, after the opener) | the SEATED / CALF RAISE layered title
(bright gym ceiling behind, back word behind his head) | Routine Checklist + Exercise Bar + CAM 2 tag, no box |
the brightest pop-up moment (picked by measuring the footage behind the text). Song from the intro's start.
- r8-A1 his exact spec: tight 6 px / 80 %, wide 22 px / 45 %, shadow 40 px / 35 %
- r8-A2 softer: tight 4 / 60 %, wide 16 / 30 %, same shadow
- r8-A3 stronger: tight 8 / 90 %, wide 30 / 60 %, shadow 50 / 45 %
- r8-A4 his spec without the dark shadow (shows what the shadow does)
Every A card: progress bar = a thin white line in the same glow look (done 4 px, still to come 2 px at 35 %);
glitch intro = white-only (2-frame burst: white ghost copies 8 / 4 px on the letter edges + 2-band slice jitter).

## Section B: video-inside-text intro, GRIND DAY on the Grind Day opening, after the logo opener (3 beats, 1.77 s)
Card video = opener | intro 2.6 s | 1 s of the normal video. Never over 3 s.
- r8-B1 his exact spec: type 0-1.2 s, hold + 2 cursor blinks to 1.8 s, split 1.8-2.6 s ease-out (cubic)
- r8-B2 thinner cursor (5 % of the size), 4 faster blinks, expo-out split
- r8-B3 footage under the letters brightened x1.5 (the only brightening allowed)
- r8-B4 a thin 8 px line of video opens at the seam for 2 frames, then the same split

## Review checklist (supervisor)
1. ffprobe 1080x1920, 30 fps, h264 + aac on every card; B intros exactly 2.6 s.
2. A: glow white, never tinted; shadow hugs the text (no box); nothing over his face; back-word glow behind him.
3. B: outside the letters black 0-1.8 s; footage through the letters; split on time; no jump after 2.6 s
   (`meta.json` intro_report).
