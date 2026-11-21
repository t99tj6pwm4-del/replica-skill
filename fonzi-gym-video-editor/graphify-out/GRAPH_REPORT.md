# Graph Report - fonzi-gym-video-editor  (2026-11-21)

## Corpus Check
- 47 files · ~78,934 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .ttf 4, .example 1)

## Summary
- 635 nodes · 1555 edges · 37 communities (31 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a8b95608`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- round2/build.py
- Overlay.tsx
- round5/build.py
- shot_library.py
- multicam
- re
- cut_video.py
- numpy
- die
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
- sfx
- audio
- config.yaml
- run
- effects.py
- film_grade.py
- openfilm_library.sh
- intro

## God Nodes (most connected - your core abstractions)
1. `die()` - 59 edges
2. `load_json()` - 45 edges
3. `save_json()` - 43 edges
4. `run()` - 38 edges
5. `rel()` - 38 edges
6. `probe()` - 28 edges
7. `main()` - 22 edges
8. `main()` - 20 edges
9. `resolve()` - 19 edges
10. `build()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `contact_sheets()` --calls--> `run()`  [EXTRACTED]
  scripts/analyze_video.py → scripts/common.py
- `detect()` --calls--> `run()`  [EXTRACTED]
  scripts/analyze_video.py → scripts/common.py
- `main()` --calls--> `run()`  [EXTRACTED]
  scripts/analyze_video.py → scripts/common.py
- `main()` --calls--> `run()`  [EXTRACTED]
  scripts/cut_video.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (37 total, 6 thin omitted)

### Community 0 - "round2/build.py"
Cohesion: 0.09
Nodes (17): drip_layer(), drip_tips(), flicker(), logo_cards(), luma(), raw(), warm_leak(), zoom() (+9 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.05
Nodes (61): react, react-dom, remotion, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1 (+53 more)

### Community 2 - "round5/build.py"
Cohesion: 0.14
Nodes (15): build_layers(), Checker, ease_out(), encode(), gold_drips(), line(), load_frames(), main() (+7 more)

### Community 3 - "shot_library.py"
Cohesion: 0.26
Nodes (7): description(), last_video_shots(), load(), log_shots(), pick(), _pick(), top_down_rule()

### Community 4 - "multicam"
Cohesion: 0.20
Nodes (10): multicam, broll_seconds, flow_prompt, local_shot_seconds, max_shot_seconds, min_shot_seconds, require_top_down, shots (+2 more)

### Community 5 - "re"
Cohesion: 0.11
Nodes (19): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), caption_pages() (+11 more)

### Community 6 - "cut_video.py"
Cohesion: 0.17
Nodes (12): atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only(), fmt() (+4 more)

### Community 8 - "numpy"
Cohesion: 0.06
Nodes (51): beat_frames(), big_logo(), cutout(), drip_layer(), drip_tips(), _extract(), _fit(), _font() (+43 more)

### Community 9 - "die"
Cohesion: 0.07
Nodes (44): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), summary(), walk_text() (+36 more)

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
Cohesion: 0.12
Nodes (15): build(), build_exercise_titles(), cut_session(), depth_move(), drop_specks(), exercise_plans(), fit_font(), font_at() (+7 more)

### Community 23 - "titles"
Cohesion: 0.20
Nodes (10): back_push, drift_px, enabled, front_push, titles, cut_every, cut_model, max_back_cover (+2 more)

### Community 24 - "higgsfield"
Cohesion: 0.25
Nodes (8): higgsfield, aspect_ratio, clip_seconds, enabled, max_reference_images, mode, model, sound

### Community 25 - "generator"
Cohesion: 0.29
Nodes (7): generator, blocked, extend_provider, max_generated_seconds, order, paid_needs_yes_spend, provider

### Community 27 - "sfx"
Cohesion: 0.33
Nodes (6): sfx, enabled, hook, popup, title, volume_db

### Community 28 - "audio"
Cohesion: 0.40
Nodes (5): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir

### Community 29 - "config.yaml"
Cohesion: 0.29
Nodes (6): openfilm, allow_music, library_only, video_length, target_seconds, tolerance_seconds

### Community 30 - "run"
Cohesion: 0.13
Nodes (16): popup_text_ok(), base_video(), load_config(), run(), main(), add_sfx(), browser_args(), check_text() (+8 more)

### Community 33 - "effects.py"
Cohesion: 0.19
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 34 - "film_grade.py"
Cohesion: 0.24
Nodes (6): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight()

### Community 35 - "openfilm_library.sh"
Cohesion: 0.70
Nodes (4): install(), music_allowed(), of(), openfilm_library.sh script

### Community 36 - "intro"
Cohesion: 0.50
Nodes (4): intro, logo_sfx_db, max_dur, min_dur

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `die` to `effects.py`, `shot_library.py`, `re`, `cut_video.py`, `Graph`, `layered_title.py`, `run`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Should `round2/build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `providers` to `google-flow`, `seedance-2.5`, `wan-free`, `kling-multicam`, `ltx-cheap`, `minimax-h3`, `ltx-2.5`, `config.yaml`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05456095481670929 - nodes in this community are weakly interconnected._
- **Why does `run()` connect `run` to `effects.py`, `film_grade.py`, `re`, `cut_video.py`, `numpy`, `die`, `layered_title.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Should `round5/build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13768115942028986 - nodes in this community are weakly interconnected._
- **Should `re` be split into smaller, more focused modules?**
  _Cohesion score 0.11092436974789915 - nodes in this community are weakly interconnected._