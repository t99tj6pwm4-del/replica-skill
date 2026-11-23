# Graph Report - fonzi-gym-video-editor  (2026-11-23)

## Corpus Check
- 55 files · ~97,697 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .ttf 4, .example 1)

## Summary
- 911 nodes · 2005 edges · 54 communities (49 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39d3227f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- roles
- Overlay.tsx
- round5/build.py
- hyperframes_setup.sh
- multicam
- re
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
- rel
- effects.py
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
- load_json
- cutout_hit
- intro_impact
- intro_whoosh
- logo_click
- logo_crackle
- popup_pop
- riser
- title_whoosh
- zoom_whoosh

## God Nodes (most connected - your core abstractions)
1. `die()` - 67 edges
2. `load_json()` - 46 edges
3. `save_json()` - 44 edges
4. `rel()` - 43 edges
5. `run()` - 40 edges
6. `probe()` - 30 edges
7. `main()` - 23 edges
8. `intro()` - 20 edges
9. `main()` - 20 edges
10. `resolve()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `render()` --indirect_call--> `beats()`  [INFERRED]
  scripts/intro_smash.py → scripts/finish_fx.py
- `build_popups()` --calls--> `die()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `die()`  [EXTRACTED]
  scripts/analyze_video.py → scripts/common.py
- `main()` --calls--> `die()`  [EXTRACTED]
  scripts/cut_video.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (54 total, 5 thin omitted)

### Community 0 - "roles"
Cohesion: 0.05
Nodes (43): fallback, sound, fallback, sound, fallback, sound, fallback, sound (+35 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.05
Nodes (61): react, react-dom, remotion, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1 (+53 more)

### Community 2 - "round5/build.py"
Cohesion: 0.13
Nodes (15): build_layers(), Checker, ease_out(), encode(), gold_drips(), line(), load_frames(), main() (+7 more)

### Community 3 - "hyperframes_setup.sh"
Cohesion: 0.40
Nodes (3): DO_NOT_TRACK, HYPERFRAMES_NO_TELEMETRY, hyperframes_setup.sh script

### Community 4 - "multicam"
Cohesion: 0.20
Nodes (10): multicam, broll_seconds, flow_prompt, local_shot_seconds, max_shot_seconds, min_shot_seconds, require_top_down, shots (+2 more)

### Community 5 - "re"
Cohesion: 0.10
Nodes (22): boundaries(), main(), mid_word(), overlap(), parse_time(), rep_points(), retime(), scene_cuts() (+14 more)

### Community 6 - "cut_video.py"
Cohesion: 0.27
Nodes (6): atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter()

### Community 8 - "round1/build.py"
Cohesion: 0.06
Nodes (43): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight(), clip(), finish() (+35 more)

### Community 9 - "common.py"
Cohesion: 0.14
Nodes (9): find_duplicate(), fingerprint(), resolve(), save_json(), sfx_file(), sha256(), main(), show() (+1 more)

### Community 10 - "google-flow"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 11 - "Graph"
Cohesion: 0.26
Nodes (5): fingerprint_distance(), Graph, load_env(), main(), remember()

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
Cohesion: 0.11
Nodes (12): build_popups(), clip(), is_song_video(), no_text_windows(), place(), popup_text_ok(), walk_text(), intro_checks() (+4 more)

### Community 32 - "rel"
Cohesion: 0.22
Nodes (13): load_config(), rel(), sfx_info(), sfx_log_entry(), audition(), card(), mont(), cfg() (+5 more)

### Community 33 - "effects.py"
Cohesion: 0.19
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 34 - "intro_smash.py"
Cohesion: 0.06
Nodes (24): auto_side(), _back_out(), _box(), _cubic_out(), _frame_boxes(), _gap(), IntroUnfit, _layout() (+16 more)

### Community 35 - "openfilm_library.sh"
Cohesion: 0.70
Nodes (4): install(), music_allowed(), of(), openfilm_library.sh script

### Community 36 - "intro"
Cohesion: 0.33
Nodes (6): intro, logo_sfx_db, logo_styles, max_dur, min_dur, title_styles

### Community 37 - "intro_glitch.py"
Cohesion: 0.13
Nodes (12): _edge_keep(), glitch_fits(), glitch_frames(), glitch_offset(), glitch_stats(), glitch_title(), _selftest(), _sheet() (+4 more)

### Community 38 - "Logo3D"
Cohesion: 0.15
Nodes (6): ease_in_out(), fade(), Logo3D, _rot(), _selftest(), run()

### Community 39 - "style_fx.py"
Cohesion: 0.07
Nodes (34): beat_frames(), big_logo(), cutout(), drip_layer(), drip_tips(), _extract(), _fit(), _font() (+26 more)

### Community 40 - "multicam_generate.py"
Cohesion: 0.16
Nodes (12): check_generator(), conform(), ltx_generate(), main(), audio_md5(), env_key(), fal_generate(), flow_handoff() (+4 more)

### Community 41 - "run"
Cohesion: 0.15
Nodes (13): base_video(), probe(), run(), add_sfx(), browser_args(), flag(), main(), mute_if_rule() (+5 more)

### Community 42 - "die"
Cohesion: 0.18
Nodes (13): die(), beats(), _box(), cfg(), _cycle(), finish(), intro_window(), _keep_out() (+5 more)

### Community 43 - "subprocess"
Cohesion: 0.23
Nodes (8): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), main()

### Community 44 - "load_json"
Cohesion: 0.28
Nodes (9): main(), summary(), caption_pages(), clean(), main(), brand(), load_json(), plan_from_storyboard() (+1 more)

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

## Knowledge Gaps
- **2 isolated node(s):** `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 407 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sfx` connect `library` to `roles`, `config.yaml`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **What connects `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY` to the rest of the system?**
  _2 weakly-connected nodes found - possible missing edges._
- **Should `roles` be split into smaller, more focused modules?**
  _Cohesion score 0.046511627906976744 - nodes in this community are weakly interconnected._
- **Why does `die()` connect `die` to `rel`, `effects.py`, `re`, `cut_video.py`, `multicam_generate.py`, `common.py`, `run`, `subprocess`, `load_json`, `Graph`, `layered_title.py`, `load_json`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05456095481670929 - nodes in this community are weakly interconnected._
- **Why does `library` connect `library` to `cutout_hit`, `intro_impact`, `intro_whoosh`, `logo_click`, `logo_crackle`, `popup_pop`, `riser`, `title_whoosh`, `zoom_whoosh`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Should `round5/build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._