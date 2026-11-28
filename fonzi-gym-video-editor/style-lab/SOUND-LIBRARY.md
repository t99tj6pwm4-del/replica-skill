# Sound library
Since 2026-11-23 (Alfonso: "start swapping the sound effects with the ones in the new folder") every sound effect
comes from OpenFilm's free CC0 library. Picks: config.yaml `sfx.library`; roles: `sfx.roles`; list them with
`python3 scripts/library_sfx.py list`, hear OLD vs NEW in output/sfx_audition.mp4 (`library_sfx.py audition`).
- originals (as taken): `sfx/library/*.mp3`
- prepared (trimmed, level-matched to the old sound): `sfx/library/fonzi/<sound>.wav`
- fallback (synthesised, used only when a library file is missing or `sfx.source: own`): `sfx/*.wav`
Library music stays off (config openfilm.allow_music: false).
