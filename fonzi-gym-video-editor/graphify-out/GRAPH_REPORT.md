# Graph Report - fonzi-gym-video-editor  (2026-11-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 389 nodes · 952 edges · 22 communities (20 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `519936b7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21

## God Nodes (most connected - your core abstractions)
1. `die()` - 52 edges
2. `load_json()` - 38 edges
3. `save_json()` - 37 edges
4. `rel()` - 33 edges
5. `run()` - 31 edges
6. `probe()` - 25 edges
7. `main()` - 20 edges
8. `resolve()` - 19 edges
9. `main()` - 19 edges
10. `main()` - 17 edges

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

## Communities (22 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (22): main(), brand(), find_duplicate(), fingerprint(), fingerprint_distance(), load_json(), rel(), save_json() (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (32): react, remotion, CarouselSlide(), pad(), BODY, DISPLAY, loadOnce(), useFonts() (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (20): caption_pages(), clean(), die(), load_config(), boundaries(), main(), mid_word(), overlap() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (13): base_video(), probe(), run(), main(), walk(), browser_args(), check_text(), walk() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (24): audio, allow_generated_music, mute_baked_music, original_audio_is_truth, songs_dir, generator, blocked, extend_provider (+16 more)

### Community 5 - "Community 5"
Cohesion: 0.16
Nodes (12): check_generator(), conform(), ltx_generate(), main(), audio_md5(), env_key(), fal_generate(), flow_handoff() (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (12): resolve(), atempo(), build_pieces(), keep_ranges(), main(), q(), video_filter(), english_only() (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (18): react-dom, @remotion/cli, @types/react, typescript, dependencies, react@18.3.1, react-dom@18.3.1, remotion@4.0.290 (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (10): apply(), combo_key(), in_library(), library_names(), log(), log_title_style(), previous_combo(), recipe() (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.25
Nodes (8): contact_sheets(), detect(), intersect(), main(), motion_curve(), ranges_where(), song_tempo(), transcribe()

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (15): api, aspect_ratio, broll_model, clip_seconds, daily_credits, if_blocked_at_peak, max_clip_seconds, min_clip_seconds (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.32
Nodes (4): Graph, load_env(), main(), remember()

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, skipLibCheck (+3 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (11): seedance-2.5, api, aspect_ratio, cost_per_second_usd, key_env, max_clip_seconds, min_clip_seconds, model (+3 more)

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (9): wan-free, api, key_env, max_clip_seconds, min_clip_seconds, model, seed, space (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.29
Nodes (7): api, cost_per_second_usd, api, cost_per_second_usd, providers, free-local, local-reframe

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (7): api, aspect_ratio, key_env, max_clip_seconds, min_clip_seconds, model, kling-multicam

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (7): api, aspect_ratio, cost_per_second_usd, key_env, model, resolution, ltx-cheap

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (7): api, generate_audio, key_env, max_clip_seconds, min_clip_seconds, model, minimax-h3

### Community 19 - "Community 19"
Cohesion: 0.40
Nodes (5): api, broll_only, key_env, model, ltx-2.5

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `die()` connect `Community 2` to `Community 0`, `Community 3`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 11`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09275793650793651 - nodes in this community are weakly interconnected._
- **Why does `providers` connect `Community 15` to `Community 4`, `Community 10`, `Community 13`, `Community 14`, `Community 16`, `Community 17`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.10796221322537113 - nodes in this community are weakly interconnected._
- **Why does `load_json()` connect `Community 0` to `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 8`, `Community 11`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.1126984126984127 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.1225071225071225 - nodes in this community are weakly interconnected._