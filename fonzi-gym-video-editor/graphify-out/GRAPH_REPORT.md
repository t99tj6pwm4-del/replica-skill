# Graph Report - fonzi-gym-video-editor  (2026-11-23)

## Corpus Check
- 57 files · ~102,308 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .ttf 4, .example 1)

## Summary
- 990 nodes · 2157 edges · 73 communities (66 shown, 7 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f637d72b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- roles
- Overlay.tsx
- round5/build.py
- hyperframes_setup.sh
- multicam
- effects.py
- cut_video.py
- round1/build.py
- common.py
- google-flow
- Graph
- compilerOptions
- seedance-2.5
- wan-free
- providers
- kling-multicam
- ltx-cheap
- minimax-h3
- ltx-2.5
- install_extras.sh
- setup.sh
- layered_title.py
- titles
- higgsfield
- generator
- library
- audio
- config.yaml
- load_json
- text_look.py
- library_sfx.py
- common.py
- intro_smash.py
- openfilm_library.sh
- intro
- intro_glitch.py
- Logo3D
- style_fx.py
- multicam_generate.py
- run
- die
- subprocess
- text_look
- cutout_hit
- intro_impact
- intro_whoosh
- logo_click
- logo_crackle
- popup_pop
- riser
- title_whoosh
- zoom_whoosh
- opener
- cutout_hit
- cutout_pop
- cutout_whoosh
- intro_impact
- intro_whoosh
- logo_click
- logo_crackle
- opener_click
- opener_crackle
- opener_impact
- popup_pop
- riser
- snap_hit
- title_whoosh
- zoom_impact
- zoom_whoosh

## God Nodes (most connected - your core abstractions)
1. `die()` - 67 edges
2. `load_json()` - 46 edges
3. `save_json()` - 45 edges
4. `rel()` - 44 edges
5. `run()` - 40 edges
6. `probe()` - 30 edges
7. `main()` - 24 edges
8. `load_config()` - 22 edges
9. `finish()` - 22 edges
10. `main()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `build_popups()` --calls--> `die()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `load_json()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `rel()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `save_json()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `load_json()`  [EXTRACTED]
  scripts/build_overlay_props.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (73 total, 7 thin omitted)

### Community 0 - "roles"
Cohesion: 0.50
Nodes (4): fallback, sound, cutout_click, roles

### Community 1 - "Overlay.tsx"
Cohesion: 0.06
Nodes (67): react, react-dom, remotion, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1 (+59 more)

### Community 2 - "round5/build.py"
Cohesion: 0.13
Nodes (15): build_layers(), Checker, ease_out(), encode(), gold_drips(), line(), load_frames(), main() (+7 more)

### Community 3 - "hyperframes_setup.sh"
Cohesion: 0.40
Nodes (3): DO_NOT_TRACK, HYPERFRAMES_NO_TELEMETRY, hyperframes_setup.sh script

### Community 4 - "multicam"
Cohesion: 0.20
Nodes (10): multicam, broll_seconds, flow_prompt, local_shot_seconds, max_shot_seconds, min_shot_seconds, require_top_down, shots (+2 more)

### Community 5 - "effects.py"
Cohesion: 0.08
Nodes (26): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+18 more)

### Community 6 - "cut_video.py"
Cohesion: 0.17
Nodes (13): load_config(), atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only() (+5 more)

### Community 8 - "round1/build.py"
Cohesion: 0.06
Nodes (43): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight(), clip(), finish() (+35 more)

### Community 9 - "common.py"
Cohesion: 0.16
Nodes (15): find_duplicate(), fingerprint(), fingerprint_distance(), load_json(), probe(), rel(), save_json(), sha256() (+7 more)

### Community 10 - "google-flow"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 12 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, skipLibCheck (+3 more)

### Community 13 - "seedance-2.5"
Cohesion: 0.18
Nodes (11): seedance-2.5, api, aspect_ratio, cost_per_second_usd, key_env, max_clip_seconds, min_clip_seconds, model (+3 more)

### Community 14 - "wan-free"
Cohesion: 0.22
Nodes (9): wan-free, api, key_env, max_clip_seconds, min_clip_seconds, model, seed, space (+1 more)

### Community 15 - "providers"
Cohesion: 0.29
Nodes (7): api, cost_per_second_usd, api, cost_per_second_usd, providers, free-local, local-reframe

### Community 16 - "kling-multicam"
Cohesion: 0.29
Nodes (7): api, aspect_ratio, key_env, max_clip_seconds, min_clip_seconds, model, kling-multicam

### Community 17 - "ltx-cheap"
Cohesion: 0.29
Nodes (7): api, aspect_ratio, cost_per_second_usd, key_env, model, resolution, ltx-cheap

### Community 18 - "minimax-h3"
Cohesion: 0.29
Nodes (7): api, generate_audio, key_env, max_clip_seconds, min_clip_seconds, model, minimax-h3

### Community 19 - "ltx-2.5"
Cohesion: 0.40
Nodes (5): api, broll_only, key_env, model, ltx-2.5

### Community 22 - "layered_title.py"
Cohesion: 0.13
Nodes (14): build(), build_exercise_titles(), cut_session(), depth_move(), drop_specks(), exercise_plans(), fit_font(), font_at() (+6 more)

### Community 23 - "titles"
Cohesion: 0.20
Nodes (10): back_push, drift_px, enabled, front_push, titles, cut_every, cut_model, max_back_cover (+2 more)

### Community 24 - "higgsfield"
Cohesion: 0.25
Nodes (8): higgsfield, aspect_ratio, clip_seconds, enabled, max_reference_images, mode, model, sound

### Community 25 - "generator"
Cohesion: 0.29
Nodes (7): generator, blocked, extend_provider, max_generated_seconds, order, paid_needs_yes_spend, provider

### Community 27 - "library"
Cohesion: 0.20
Nodes (10): hook, popup, title, sfx, enabled, events, library, licence (+2 more)

### Community 28 - "audio"
Cohesion: 0.40
Nodes (5): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir

### Community 29 - "config.yaml"
Cohesion: 0.29
Nodes (6): openfilm, allow_music, library_only, video_length, target_seconds, tolerance_seconds

### Community 30 - "load_json"
Cohesion: 0.08
Nodes (21): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), popup_text_ok(), summary() (+13 more)

### Community 31 - "text_look.py"
Cohesion: 0.13
Nodes (12): box_pixels(), _demo(), for_remotion(), hex_rgb(), look(), pad(), stack(), text_rgb() (+4 more)

### Community 32 - "library_sfx.py"
Cohesion: 0.26
Nodes (9): audition(), card(), mont(), cfg(), listing(), loudest_rms(), main(), pcm() (+1 more)

### Community 33 - "common.py"
Cohesion: 0.24
Nodes (3): sfx_file(), sfx_info(), sfx_log_entry()

### Community 34 - "intro_smash.py"
Cohesion: 0.06
Nodes (23): auto_side(), _back_out(), _box(), _cubic_out(), _frame_boxes(), _gap(), IntroUnfit, _layout() (+15 more)

### Community 35 - "openfilm_library.sh"
Cohesion: 0.70
Nodes (4): install(), music_allowed(), of(), openfilm_library.sh script

### Community 36 - "intro"
Cohesion: 0.33
Nodes (6): intro, logo_sfx_db, logo_styles, max_dur, min_dur, title_styles

### Community 37 - "intro_glitch.py"
Cohesion: 0.13
Nodes (12): _beat_index(), _edge_keep(), glitch_fits(), glitch_frames(), glitch_offset(), glitch_stats(), glitch_title(), _parts() (+4 more)

### Community 38 - "Logo3D"
Cohesion: 0.15
Nodes (6): ease_in_out(), fade(), Logo3D, _rot(), _selftest(), run()

### Community 39 - "style_fx.py"
Cohesion: 0.07
Nodes (35): beat_frames(), big_logo(), cutout(), drip_layer(), drip_tips(), _extract(), _fit(), _font() (+27 more)

### Community 40 - "multicam_generate.py"
Cohesion: 0.17
Nodes (13): check_generator(), die(), conform(), ltx_generate(), main(), audio_md5(), env_key(), fal_generate() (+5 more)

### Community 41 - "run"
Cohesion: 0.16
Nodes (11): base_video(), add_sfx(), browser_args(), flag(), main(), measure_text_look(), mute_if_rule(), remotion() (+3 more)

### Community 42 - "die"
Cohesion: 0.14
Nodes (15): beat_grid(), beats(), _box(), cfg(), _cycle(), finish(), intro_end(), intro_window() (+7 more)

### Community 43 - "subprocess"
Cohesion: 0.15
Nodes (12): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), resolve() (+4 more)

### Community 44 - "text_look"
Cohesion: 0.20
Nodes (10): blur, color, name, opacity, text_look, box_alpha_max, color, layers (+2 more)

### Community 45 - "cutout_hit"
Cohesion: 0.25
Nodes (8): dur, fade_out, id, match, name, original, start, cutout_hit

### Community 46 - "intro_impact"
Cohesion: 0.25
Nodes (8): dur, fade_out, id, match, name, original, start, intro_impact

### Community 47 - "intro_whoosh"
Cohesion: 0.25
Nodes (8): dur, fade_out, id, match, name, original, start, intro_whoosh

### Community 48 - "logo_click"
Cohesion: 0.25
Nodes (8): logo_click, dur, fade_out, id, match, name, original, start

### Community 49 - "logo_crackle"
Cohesion: 0.25
Nodes (8): logo_crackle, dur, fade_out, id, match, name, original, start

### Community 50 - "popup_pop"
Cohesion: 0.25
Nodes (8): popup_pop, dur, fade_out, id, match, name, original, start

### Community 51 - "riser"
Cohesion: 0.25
Nodes (8): riser, dur, fade_out, id, match, name, original, start

### Community 52 - "title_whoosh"
Cohesion: 0.25
Nodes (8): title_whoosh, dur, fade_out, id, match, name, original, start

### Community 53 - "zoom_whoosh"
Cohesion: 0.25
Nodes (8): zoom_whoosh, dur, fade_out, id, match, name, original, start

### Community 58 - "opener"
Cohesion: 0.25
Nodes (8): opener, beats, enabled, lead_frames, max_beats, min_beats, sfx_db, target

### Community 62 - "cutout_hit"
Cohesion: 0.67
Nodes (3): fallback, sound, cutout_hit

### Community 63 - "cutout_pop"
Cohesion: 0.67
Nodes (3): fallback, sound, cutout_pop

### Community 64 - "cutout_whoosh"
Cohesion: 0.67
Nodes (3): fallback, sound, cutout_whoosh

### Community 65 - "intro_impact"
Cohesion: 0.67
Nodes (3): fallback, sound, intro_impact

### Community 66 - "intro_whoosh"
Cohesion: 0.67
Nodes (3): fallback, sound, intro_whoosh

### Community 67 - "logo_click"
Cohesion: 0.67
Nodes (3): fallback, sound, logo_click

### Community 68 - "logo_crackle"
Cohesion: 0.67
Nodes (3): fallback, sound, logo_crackle

### Community 69 - "opener_click"
Cohesion: 0.67
Nodes (3): fallback, sound, opener_click

### Community 70 - "opener_crackle"
Cohesion: 0.67
Nodes (3): fallback, sound, opener_crackle

### Community 71 - "opener_impact"
Cohesion: 0.67
Nodes (3): fallback, sound, opener_impact

### Community 72 - "popup_pop"
Cohesion: 0.67
Nodes (3): fallback, sound, popup_pop

### Community 73 - "riser"
Cohesion: 0.67
Nodes (3): fallback, sound, riser

### Community 74 - "snap_hit"
Cohesion: 0.67
Nodes (3): snap_hit, fallback, sound

### Community 75 - "title_whoosh"
Cohesion: 0.67
Nodes (3): title_whoosh, fallback, sound

### Community 76 - "zoom_impact"
Cohesion: 0.67
Nodes (3): zoom_impact, fallback, sound

### Community 77 - "zoom_whoosh"
Cohesion: 0.67
Nodes (3): zoom_whoosh, fallback, sound

## Knowledge Gaps
- **2 isolated node(s):** `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 450 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sfx` connect `library` to `roles`, `config.yaml`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **What connects `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY` to the rest of the system?**
  _2 weakly-connected nodes found - possible missing edges._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.056140350877192984 - nodes in this community are weakly interconnected._
- **Why does `die()` connect `multicam_generate.py` to `library_sfx.py`, `common.py`, `effects.py`, `cut_video.py`, `common.py`, `die`, `subprocess`, `Graph`, `run`, `layered_title.py`, `load_json`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `round5/build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Why does `library` connect `library` to `cutout_hit`, `intro_impact`, `intro_whoosh`, `logo_click`, `logo_crackle`, `popup_pop`, `riser`, `title_whoosh`, `zoom_whoosh`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `effects.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07678075855689177 - nodes in this community are weakly interconnected._