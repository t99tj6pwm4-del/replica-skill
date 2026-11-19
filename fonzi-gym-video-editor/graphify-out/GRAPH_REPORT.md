# Graph Report - fonzi-gym-video-editor  (2026-11-19)

## Corpus Check
- 36 files · ~46,376 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 6, .ttf 3, .example 1)

## Summary
- 449 nodes · 1096 edges · 24 communities (20 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `083627bc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- effects.py
- Overlay.tsx
- die
- load_json
- multicam
- multicam_generate.py
- cut_video.py
- run
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

## God Nodes (most connected - your core abstractions)
1. `die()` - 55 edges
2. `load_json()` - 40 edges
3. `save_json()` - 40 edges
4. `rel()` - 36 edges
5. `run()` - 34 edges
6. `probe()` - 26 edges
7. `main()` - 22 edges
8. `main()` - 20 edges
9. `build()` - 19 edges
10. `main()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `title_cfg()` --calls--> `load_config()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `layout()` --calls--> `die()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `build()` --calls--> `die()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `build()` --calls--> `probe()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py
- `build()` --calls--> `rel()`  [EXTRACTED]
  scripts/layered_title.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (24 total, 4 thin omitted)

### Community 0 - "effects.py"
Cohesion: 0.18
Nodes (11): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+3 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.08
Nodes (44): react, remotion, react@18.3.1, CarouselSlide(), pad(), BODY, DISPLAY, loadOnce() (+36 more)

### Community 2 - "die"
Cohesion: 0.13
Nodes (15): boundaries(), main(), mid_word(), overlap(), parse_time(), rep_points(), retime(), scene_cuts() (+7 more)

### Community 3 - "load_json"
Cohesion: 0.11
Nodes (19): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), popup_text_ok(), summary() (+11 more)

### Community 4 - "multicam"
Cohesion: 0.05
Nodes (41): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir, generator, blocked, extend_provider (+33 more)

### Community 5 - "multicam_generate.py"
Cohesion: 0.12
Nodes (19): check_generator(), die(), rel(), resolve(), sha256(), conform(), ltx_generate(), main() (+11 more)

### Community 6 - "cut_video.py"
Cohesion: 0.19
Nodes (12): load_config(), atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only() (+4 more)

### Community 8 - "run"
Cohesion: 0.11
Nodes (20): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), base_video() (+12 more)

### Community 9 - "layered_title.py"
Cohesion: 0.13
Nodes (14): build(), build_exercise_titles(), cut_session(), depth_move(), drop_specks(), exercise_plans(), fit_font(), font_at() (+6 more)

### Community 10 - "google-flow"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 11 - "main"
Cohesion: 0.17
Nodes (8): find_duplicate(), fingerprint(), fingerprint_distance(), save_json(), Graph, load_env(), main(), remember()

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
Cohesion: 0.14
Nodes (17): react-dom, @remotion/cli, @types/react, typescript, dependencies, react-dom@18.3.1, remotion@4.0.290, @remotion/cli@4.0.290 (+9 more)

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `multicam_generate.py` to `effects.py`, `die`, `load_json`, `cut_video.py`, `run`, `layered_title.py`, `main`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.08078431372549019 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `providers` to `multicam`, `google-flow`, `seedance-2.5`, `wan-free`, `kling-multicam`, `ltx-cheap`, `minimax-h3`, `ltx-2.5`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `die` be split into smaller, more focused modules?**
  _Cohesion score 0.12873563218390804 - nodes in this community are weakly interconnected._
- **Why does `load_json()` connect `load_json` to `effects.py`, `die`, `multicam_generate.py`, `cut_video.py`, `run`, `layered_title.py`, `main`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `load_json` be split into smaller, more focused modules?**
  _Cohesion score 0.10634920634920635 - nodes in this community are weakly interconnected._
- **Should `multicam` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._