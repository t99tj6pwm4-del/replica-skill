# Graph Report - fonzi-gym-video-editor  (2026-11-19)

## Corpus Check
- 38 files · ~60,317 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 6, .ttf 3, .example 1)

## Summary
- 498 nodes · 1228 edges · 31 communities (27 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eddea684`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- effects.py
- Overlay.tsx
- die
- load_json
- multicam
- die
- cut_video.py
- build.py
- layered_title.py
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
- package.json
- titles
- higgsfield
- generator
- sfx
- audio
- config.yaml
- shot_library.py

## God Nodes (most connected - your core abstractions)
1. `die()` - 55 edges
2. `load_json()` - 40 edges
3. `save_json()` - 40 edges
4. `run()` - 36 edges
5. `rel()` - 36 edges
6. `probe()` - 26 edges
7. `main()` - 22 edges
8. `main()` - 20 edges
9. `build()` - 19 edges
10. `resolve()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `grade()` --calls--> `run()`  [EXTRACTED]
  scripts/film_grade.py → scripts/common.py
- `title_cfg()` --calls--> `load_config()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `layout()` --calls--> `die()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `build()` --calls--> `die()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (31 total, 4 thin omitted)

### Community 0 - "effects.py"
Cohesion: 0.19
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.08
Nodes (43): react, remotion, CarouselSlide(), pad(), BODY, DISPLAY, loadOnce(), MONTSERRAT (+35 more)

### Community 2 - "die"
Cohesion: 0.11
Nodes (19): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), fingerprint() (+11 more)

### Community 3 - "load_json"
Cohesion: 0.09
Nodes (19): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), popup_text_ok(), summary() (+11 more)

### Community 4 - "multicam"
Cohesion: 0.20
Nodes (10): multicam, broll_seconds, flow_prompt, local_shot_seconds, max_shot_seconds, min_shot_seconds, require_top_down, shots (+2 more)

### Community 5 - "die"
Cohesion: 0.09
Nodes (31): base_video(), check_generator(), die(), load_json(), rel(), run(), save_json(), sha256() (+23 more)

### Community 6 - "cut_video.py"
Cohesion: 0.18
Nodes (13): load_config(), resolve(), atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter() (+5 more)

### Community 8 - "build.py"
Cohesion: 0.12
Nodes (26): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight(), clip(), finish() (+18 more)

### Community 9 - "layered_title.py"
Cohesion: 0.13
Nodes (14): build(), build_exercise_titles(), cut_session(), depth_move(), drop_specks(), exercise_plans(), fit_font(), font_at() (+6 more)

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

### Community 22 - "package.json"
Cohesion: 0.13
Nodes (18): react-dom, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1, react-dom@18.3.1, remotion@4.0.290 (+10 more)

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
Cohesion: 0.50
Nodes (3): video_length, target_seconds, tolerance_seconds

### Community 30 - "shot_library.py"
Cohesion: 0.26
Nodes (7): description(), last_video_shots(), load(), log_shots(), pick(), _pick(), top_down_rule()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `die` to `effects.py`, `die`, `load_json`, `cut_video.py`, `layered_title.py`, `Graph`, `shot_library.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.08326530612244898 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `providers` to `google-flow`, `seedance-2.5`, `wan-free`, `kling-multicam`, `ltx-cheap`, `minimax-h3`, `ltx-2.5`, `config.yaml`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `die` be split into smaller, more focused modules?**
  _Cohesion score 0.1066066066066066 - nodes in this community are weakly interconnected._
- **Why does `run()` connect `die` to `effects.py`, `die`, `load_json`, `cut_video.py`, `build.py`, `layered_title.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Should `load_json` be split into smaller, more focused modules?**
  _Cohesion score 0.09309309309309309 - nodes in this community are weakly interconnected._
- **Should `die` be split into smaller, more focused modules?**
  _Cohesion score 0.08860759493670886 - nodes in this community are weakly interconnected._