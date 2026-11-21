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
`style-lab/STYLE.md` (rule 0 intro, gold #D4A017, Rubik Dirt for the intro title, Montserrat for the rest, safe
area, never over his face, no colour grade, no dark tint, no white flash on the beat), and the supervisor's
`output/visuals/style_sheet.json` for the video.
