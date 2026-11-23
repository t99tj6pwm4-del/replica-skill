# HyperFrames (Alfonso, 2026-11-21)

HeyGen's open-source HTML-to-video renderer (Apache-2.0, https://github.com/heygen-com/hyperframes). We use it
only to build **motion graphics layers** (intro card, gold titles, pop-ups, logo end card) that our own tools then
composite over his footage. Setup: `source scripts/hyperframes_setup.sh` then `hf <command>` (CLI 0.9.78 pinned,
telemetry off). Owner: the Text/Visuals supervisor; built by `fonzi-vfx-worker` agents on its work orders.

## Allowed
`init`, `add` / `catalog` (blocks and components from the registry: text slams, glitch, neon glow, light sweep,
beat accents, camera shake, 3D logo, etc.), `render` (MP4, or WebM / PNG sequence with alpha for overlays),
`lint`, `check`, `validate`, `snapshot`, `inspect`, `beats` (on HIS song only), `audio`, `compare`, `measure`,
`compositions`, `timeline`, `info`, `docs`, `doctor`, `remove-background` (local, on his footage).

## Never
- `share`, `publish`, `cloud`, `lambda`, `cloudrun`: they upload his project or footage.
- `templates`, `billing`, Pro plan, HeyGen's AI video / image / voice / music models, `tts`, local MusicGen BGM.
  No AI or stock music, no generated voices: his songs only (standing rule).
- `reverse` (sends a video to HeyGen), `capture` (other websites).
- Any registry block's demo footage, stock images or sample audio in a final video. Only the motion code is used;
  every picture is his footage or our own brand files (`brand/`).
- Telemetry on.

## House style every composition must follow
`style-lab/STYLE.md` (rule 0 intro, white text look since 2026-11-23 (config `text_look`, STYLE.md rule zero-A, A2 picked 2026-11-23; was gold #D4A017), Rubik Dirt for the intro title, Montserrat for the rest, safe
area, never over his face, no colour grade, no dark tint, no white flash on the beat), and the supervisor's
`output/visuals/style_sheet.json` for the video.

## Production intro (Director, round 7 to production, 2026-11-22)
HyperFrames is the **Style Lab design tool**. Once a motion is locked, production ports it to Python / PIL / numpy
in `scripts/style_fx.py intro` (helpers `intro_glitch.py`, `intro_smash.py`, `intro_logo3d.py`) and never calls
`hf`, Node or Chrome at render time. The round-7 HyperFrames builds `output/style_lab/r7/r7-03|04|05/` are the
read-only golden frames the port is checked against (glitch, 3D logo, letters smash). Why
(`output/visuals/round7_prod/style_sheet.json` "decision"): one engine keeps every title style and both logos
inside the same per-frame face guard, safe-area check, logo-in-frame check and `intro_card.json` report; the r7
references were already mostly Python (scatter solver, edge masking, logo recombination, edge fixes), with Chrome
only rasterising text and a perspective transform; the HF projects are hard-wired to one title while production
titles move per video under his face; a render must not depend on Node, an unpinned system Chrome and network
fetches; and PIL + numpy re-renders are byte-identical, so a re-render that keeps its rotation picks gives the
same picture. Production rules from the port: the logo front is 72 % effective white (flat and 3D front face are
the same `big_logo` layer, 3D sides 30 %); logo-on-face pixels (`logo_on_face_px_max`) are report only (soft);
`title_max_rgb` is a hard check only for glitch (smash frames outside the pulse are checked per frame inside
`style_fx.intro`); the smash keep-out side is automatic (the side with more of his body at chest height) unless
the storyboard sets `intro.smash_keep_out`.
