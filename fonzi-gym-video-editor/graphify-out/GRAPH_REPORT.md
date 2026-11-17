# Graph Report - fonzi-gym-video-editor  (2026-11-17)

## Corpus Check
- 35 files · ~43,809 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 6, .ttf 3, .example 1)

## Summary
- 416 nodes · 1029 edges · 25 communities (21 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `14e070c5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- load_json
- Overlay.tsx
- die
- run
- multicam
- die
- cut_video.py
- effects.py
- layered_title.py
- google-flow
- main
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
- shot_library.py

## God Nodes (most connected - your core abstractions)
1. `die()` - 54 edges
2. `load_json()` - 40 edges
3. `save_json()` - 39 edges
4. `rel()` - 35 edges
5. `run()` - 31 edges
6. `probe()` - 25 edges
7. `main()` - 21 edges
8. `main()` - 20 edges
9. `resolve()` - 19 edges
10. `main()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `build_popups()` --calls--> `die()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `rel()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `save_json()`  [EXTRACTED]
  scripts/add_popups.py → scripts/common.py
- `main()` --calls--> `rel()`  [EXTRACTED]
  scripts/build_overlay_props.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (25 total, 4 thin omitted)

### Community 0 - "load_json"
Cohesion: 0.11
Nodes (19): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), popup_text_ok(), summary() (+11 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.08
Nodes (45): react, remotion, react@18.3.1, remotion@4.0.290, CarouselSlide(), pad(), BODY, DISPLAY (+37 more)

### Community 2 - "die"
Cohesion: 0.19
Nodes (10): boundaries(), main(), mid_word(), overlap(), parse_time(), rep_points(), retime(), scene_cuts() (+2 more)

### Community 3 - "run"
Cohesion: 0.11
Nodes (20): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), base_video() (+12 more)

### Community 4 - "multicam"
Cohesion: 0.08
Nodes (24): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir, generator, blocked, extend_provider (+16 more)

### Community 5 - "die"
Cohesion: 0.12
Nodes (19): check_generator(), die(), rel(), resolve(), save_json(), conform(), ltx_generate(), main() (+11 more)

### Community 6 - "cut_video.py"
Cohesion: 0.18
Nodes (11): atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only(), fmt() (+3 more)

### Community 8 - "effects.py"
Cohesion: 0.18
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 9 - "layered_title.py"
Cohesion: 0.18
Nodes (9): build(), build_exercise_titles(), exercise_plans(), fit_font(), font_at(), layout(), person_mask(), smooth_masks() (+1 more)

### Community 10 - "google-flow"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 11 - "main"
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

### Community 22 - "package.json"
Cohesion: 0.15
Nodes (16): react-dom, @remotion/cli, @types/react, typescript, dependencies, react-dom@18.3.1, @remotion/cli@4.0.290, description (+8 more)

### Community 23 - "shot_library.py"
Cohesion: 0.24
Nodes (8): load_config(), description(), last_video_shots(), load(), log_shots(), pick(), _pick(), top_down_rule()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `die` to `load_json`, `die`, `run`, `cut_video.py`, `effects.py`, `layered_title.py`, `main`, `shot_library.py`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Should `load_json` be split into smaller, more focused modules?**
  _Cohesion score 0.10695187165775401 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `providers` to `multicam`, `google-flow`, `seedance-2.5`, `wan-free`, `kling-multicam`, `ltx-cheap`, `minimax-h3`, `ltx-2.5`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.0784313725490196 - nodes in this community are weakly interconnected._
- **Why does `load_json()` connect `load_json` to `die`, `run`, `die`, `cut_video.py`, `effects.py`, `layered_title.py`, `main`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Should `run` be split into smaller, more focused modules?**
  _Cohesion score 0.10606060606060606 - nodes in this community are weakly interconnected._
- **Should `multicam` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._