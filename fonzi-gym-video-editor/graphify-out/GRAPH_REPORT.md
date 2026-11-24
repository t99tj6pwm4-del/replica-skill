# Graph Report - fonzi-gym-video-editor  (2026-11-24)

## Corpus Check
- 68 files · ~126,889 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .ttf 4, .example 1)

## Summary
- 1195 nodes · 2644 edges · 95 communities (82 shown, 13 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9d221910`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- roles
- package.json
- round5/build.py
- hyperframes_setup.sh
- multicam
- re
- rel
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
- cut_video.py
- config.yaml
- load_json
- text_look.py
- layers
- json
- intro_smash.py
- openfilm_library.sh
- intro_video_text.py
- intro_glitch.py
- Logo3D
- style_fx.py
- multicam_generate.py
- run
- die
- track
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
- round6/build.py
- Track
- intro_glitch_gold.py
- motion_cuts.py
- video_text
- Overlay.tsx
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
- OverlayLegacy.tsx
- effects.py
- numpy
- opener
- intro
- Carousel.tsx
- Glow
- intro_checks
- film_grade.py
- plan_zoom_edge
- opener_checks
- storyboard_md.py
- clamp
- look.tsx

## God Nodes (most connected - your core abstractions)
1. `die()` - 69 edges
2. `load_json()` - 49 edges
3. `rel()` - 48 edges
4. `save_json()` - 45 edges
5. `run()` - 40 edges
6. `probe()` - 34 edges
7. `load_config()` - 25 edges
8. `main()` - 24 edges
9. `finish()` - 23 edges
10. `intro()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `b_shared()` --calls--> `load_json()`  [INFERRED]
  style-lab/round8/build.py → scripts/common.py
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `render()` --indirect_call--> `beats()`  [INFERRED]
  scripts/intro_smash.py → scripts/finish_fx.py
- `sound()` --calls--> `sfx_log_entry()`  [EXTRACTED]
  scripts/style_fx.py → scripts/common.py
- `intro()` --calls--> `Logo3D`  [EXTRACTED]
  scripts/style_fx.py → scripts/intro_logo3d.py

## Import Cycles
- None detected.

## Communities (95 total, 13 thin omitted)

### Community 0 - "roles"
Cohesion: 0.50
Nodes (4): fallback, sound, cutout_click, roles

### Community 1 - "package.json"
Cohesion: 0.13
Nodes (18): react-dom, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1, react-dom@18.3.1, remotion@4.0.290 (+10 more)

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
Cohesion: 0.08
Nodes (26): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), caption_pages() (+18 more)

### Community 6 - "rel"
Cohesion: 0.22
Nodes (13): load_config(), rel(), sfx_info(), sfx_log_entry(), audition(), card(), mont(), cfg() (+5 more)

### Community 8 - "round1/build.py"
Cohesion: 0.18
Nodes (20): clip(), finish(), frames(), grade_cards(), leak_frame(), logo_bg(), logo_cards(), logo_layers() (+12 more)

### Community 9 - "common.py"
Cohesion: 0.12
Nodes (10): find_duplicate(), fingerprint(), fingerprint_distance(), resolve(), sfx_file(), sha256(), main(), show() (+2 more)

### Community 10 - "google-flow"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 11 - "Graph"
Cohesion: 0.32
Nodes (4): Graph, load_env(), main(), remember()

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

### Community 28 - "cut_video.py"
Cohesion: 0.19
Nodes (12): atempo(), build_pieces(), cut_list_intro(), _edge_speed(), _effect_span(), keep_ranges(), main(), plan_motion_cuts() (+4 more)

### Community 29 - "config.yaml"
Cohesion: 0.17
Nodes (11): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir, openfilm, allow_music, library_only (+3 more)

### Community 30 - "load_json"
Cohesion: 0.11
Nodes (18): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), popup_text_ok(), summary() (+10 more)

### Community 31 - "text_look.py"
Cohesion: 0.12
Nodes (13): box_pixels(), _demo(), enabled(), for_remotion(), hex_rgb(), look(), pad(), stack() (+5 more)

### Community 32 - "layers"
Cohesion: 0.40
Nodes (5): blur, color, name, opacity, layers

### Community 33 - "json"
Cohesion: 0.17
Nodes (17): a_child(), a_segments(), b_child(), b_shared(), env_for(), grab(), grid(), main() (+9 more)

### Community 34 - "intro_smash.py"
Cohesion: 0.06
Nodes (24): auto_side(), _back_out(), _box(), _cubic_out(), _frame_boxes(), _gap(), IntroUnfit, _layout() (+16 more)

### Community 35 - "openfilm_library.sh"
Cohesion: 0.70
Nodes (4): install(), music_allowed(), of(), openfilm_library.sh script

### Community 36 - "intro_video_text.py"
Cohesion: 0.12
Nodes (11): cfg(), checks(), clean_title(), _font(), Layout, _luma(), matte_frame(), render() (+3 more)

### Community 37 - "intro_glitch.py"
Cohesion: 0.13
Nodes (12): _beat_index(), _edge_keep(), glitch_fits(), glitch_frames(), glitch_offset(), glitch_stats(), glitch_title(), _parts() (+4 more)

### Community 38 - "Logo3D"
Cohesion: 0.15
Nodes (6): ease_in_out(), fade(), Logo3D, _rot(), _selftest(), run()

### Community 39 - "style_fx.py"
Cohesion: 0.06
Nodes (40): assert_no_pad(), beat_frames(), big_logo(), _black_frac(), crop_box(), cutout(), drip_layer(), drip_tips() (+32 more)

### Community 40 - "multicam_generate.py"
Cohesion: 0.12
Nodes (16): check_generator(), probe(), run(), conform(), ltx_generate(), main(), main(), audio_md5() (+8 more)

### Community 41 - "run"
Cohesion: 0.17
Nodes (12): base_video(), save_json(), add_sfx(), browser_args(), flag(), main(), measure_text_look(), mute_if_rule() (+4 more)

### Community 42 - "die"
Cohesion: 0.16
Nodes (16): die(), beat_grid(), beats(), _box(), cfg(), _cycle(), finish(), intro_end() (+8 more)

### Community 43 - "track"
Cohesion: 0.16
Nodes (9): audit_md(), _blur(), crop_filter(), frame_measures(), part_for(), _phase_shift(), _smooth(), stream_frames() (+1 more)

### Community 44 - "text_look"
Cohesion: 0.18
Nodes (11): behind, color, opacity, radius, text_look, box_alpha_max, card, color (+3 more)

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

### Community 54 - "round6/build.py"
Cohesion: 0.29
Nodes (6): big_logo(), brighten(), main(), option(), recolor(), title_state()

### Community 55 - "Track"
Cohesion: 0.29
Nodes (4): Move, propose(), _segment(), Track

### Community 56 - "intro_glitch_gold.py"
Cohesion: 0.13
Nodes (12): _edge_keep(), glitch_fits(), glitch_frames(), glitch_offset(), glitch_stats(), glitch_title(), _selftest(), _sheet() (+4 more)

### Community 57 - "motion_cuts.py"
Cohesion: 0.13
Nodes (13): beat_snap(), cut_kind(), cut_limits(), cuts_from_map(), hard_rules_ok(), _locked_in_map(), matched(), motion_text() (+5 more)

### Community 58 - "video_text"
Cohesion: 0.20
Nodes (10): video_text, dur, force_gain, hold_end, margin, max_dur, max_gain, min_dur (+2 more)

### Community 61 - "Overlay.tsx"
Cohesion: 0.20
Nodes (14): clamp, Brand, Callout, CaptionPage, CaptionWord, ChecklistPopup, ExerciseBarPopup, FormTipPopup (+6 more)

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

### Community 78 - "OverlayLegacy.tsx"
Cohesion: 0.19
Nodes (17): MONTSERRAT, WEIGHT, CalloutMark(), Captions(), cardStyle, clamp, EndCard(), EventAccent() (+9 more)

### Community 79 - "effects.py"
Cohesion: 0.19
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 80 - "numpy"
Cohesion: 0.16
Nodes (11): drip_layer(), drip_tips(), flicker(), logo_cards(), luma(), raw(), warm_leak(), zoom() (+3 more)

### Community 81 - "opener"
Cohesion: 0.25
Nodes (8): opener, beats, enabled, lead_frames, max_beats, min_beats, sfx_db, target

### Community 82 - "intro"
Cohesion: 0.29
Nodes (7): intro, default_style, logo_sfx_db, logo_styles, max_dur, min_dur, title_styles

### Community 83 - "Carousel.tsx"
Cohesion: 0.19
Nodes (18): react, remotion, CarouselSlide(), CarouselWhite(), pad(), CarouselSlideLegacy(), pad(), BODY (+10 more)

### Community 84 - "Glow"
Cohesion: 0.25
Nodes (16): cardFor(), Glow(), useLook(), CalloutMark(), Captions(), EndCard(), EventAccent(), ExerciseBar() (+8 more)

### Community 86 - "film_grade.py"
Cohesion: 0.24
Nodes (6): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight()

### Community 89 - "storyboard_md.py"
Cohesion: 0.39
Nodes (6): english_only(), fmt(), main(), render(), render_plan_extras(), validate()

### Community 91 - "look.tsx"
Cohesion: 0.33
Nodes (5): DEFAULT_LOOK, LookCard, LookCtx, LookLayer, TextLook

## Knowledge Gaps
- **2 isolated node(s):** `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 529 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `die` to `storyboard_md.py`, `re`, `rel`, `multicam_generate.py`, `common.py`, `run`, `Graph`, `effects.py`, `layered_title.py`, `motion_cuts.py`, `cut_video.py`, `load_json`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **What connects `DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY` to the rest of the system?**
  _2 weakly-connected nodes found - possible missing edges._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._
- **Why does `main()` connect `load_json` to `re`, `rel`, `multicam_generate.py`, `common.py`, `run`, `intro_checks`, `opener_checks`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `round5/build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Why does `sfx` connect `library` to `roles`, `config.yaml`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Should `re` be split into smaller, more focused modules?**
  _Cohesion score 0.07955596669750231 - nodes in this community are weakly interconnected._