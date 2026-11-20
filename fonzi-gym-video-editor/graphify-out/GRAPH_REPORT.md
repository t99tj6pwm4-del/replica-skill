# Graph Report - fonzi-gym-video-editor  (2026-11-20)

## Corpus Check
- 42 files · ~66,821 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 6, .ttf 3, .example 1)

## Summary
- 537 nodes · 1332 edges · 30 communities (26 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5a37c819`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- effects.py
- Overlay.tsx
- re
- common.py
- multicam
- die
- cut_video.py
- numpy
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
- run
- titles
- higgsfield
- generator
- sfx
- audio
- config.yaml

## God Nodes (most connected - your core abstractions)
1. `die()` - 55 edges
2. `load_json()` - 40 edges
3. `save_json()` - 40 edges
4. `run()` - 36 edges
5. `rel()` - 36 edges
6. `probe()` - 26 edges
7. `main()` - 22 edges
8. `main()` - 20 edges
9. `resolve()` - 19 edges
10. `main()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `remember()` --calls--> `save_json()`  [EXTRACTED]
  scripts/post_to_meta.py → scripts/common.py
- `grade()` --calls--> `run()`  [EXTRACTED]
  scripts/film_grade.py → scripts/common.py
- `main()` --calls--> `run()`  [EXTRACTED]
  scripts/cut_video.py → scripts/common.py
- `apply()` --calls--> `run()`  [EXTRACTED]
  scripts/effects.py → scripts/common.py
- `conform()` --calls--> `run()`  [EXTRACTED]
  scripts/extend_footage.py → scripts/common.py

## Import Cycles
- None detected.

## Communities (30 total, 4 thin omitted)

### Community 0 - "effects.py"
Cohesion: 0.19
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 1 - "Overlay.tsx"
Cohesion: 0.05
Nodes (61): react, react-dom, remotion, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1 (+53 more)

### Community 2 - "re"
Cohesion: 0.11
Nodes (19): caption_pages(), clean(), main(), boundaries(), main(), mid_word(), overlap(), parse_time() (+11 more)

### Community 3 - "common.py"
Cohesion: 0.09
Nodes (23): build_popups(), clip(), is_song_video(), main(), no_text_windows(), place(), summary(), walk_text() (+15 more)

### Community 4 - "multicam"
Cohesion: 0.20
Nodes (10): multicam, broll_seconds, flow_prompt, local_shot_seconds, max_shot_seconds, min_shot_seconds, require_top_down, shots (+2 more)

### Community 5 - "die"
Cohesion: 0.14
Nodes (16): check_generator(), die(), resolve(), conform(), ltx_generate(), main(), main(), show() (+8 more)

### Community 6 - "cut_video.py"
Cohesion: 0.19
Nodes (12): load_config(), atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only() (+4 more)

### Community 8 - "numpy"
Cohesion: 0.06
Nodes (49): filter_chain(), grade(), grade_rgb(), make_lut(), _sig(), warm_weight(), cutout(), drip_layer() (+41 more)

### Community 9 - "layered_title.py"
Cohesion: 0.13
Nodes (12): build(), cut_session(), depth_move(), drop_specks(), fit_font(), font_at(), layout(), person_mask() (+4 more)

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

### Community 22 - "run"
Cohesion: 0.10
Nodes (22): popup_text_ok(), contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo() (+14 more)

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

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `die` to `effects.py`, `re`, `common.py`, `cut_video.py`, `layered_title.py`, `Graph`, `run`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Should `Overlay.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05456095481670929 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `providers` to `google-flow`, `seedance-2.5`, `wan-free`, `kling-multicam`, `ltx-cheap`, `minimax-h3`, `ltx-2.5`, `config.yaml`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Should `re` be split into smaller, more focused modules?**
  _Cohesion score 0.1051693404634581 - nodes in this community are weakly interconnected._
- **Why does `run()` connect `run` to `effects.py`, `re`, `common.py`, `die`, `cut_video.py`, `numpy`, `layered_title.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `common.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08846153846153847 - nodes in this community are weakly interconnected._
- **Should `die` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._