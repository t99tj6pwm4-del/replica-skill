# HANDOVER

## Done
Running the fonzi-gym-video-editor team (`/fonzi-edit`) on Alfonso's gym videos and adding the features he asked for along the way.
Branch `claude/blissful-hamilton-k7clws` (push only there, no PRs). All code is committed and pushed.

- **"After Hours" 41.8s** (iCloud footage `input/icloud_0efbfJGz.mov` + his song `songs/alfonso_music_089_obcAC.mp3`): approved and exported as `exports/2026-11-17_after-hours.mp4` (+ .txt caption, carousel). Logged in `posted/ledger.json`.
- **"After Hours" 90s re-cut**: QA PASS. The job is marked `job.py replaces exports/2026-11-17_after-hours.mp4`. Staged at `output/staged/final_edit.mp4` (89.7s, song 59.087-148.84). Sent to Alfonso.
- **New features**, all committed:
  - Three gym-reel pop-up cards: Exercise Bar, Form Tip and Routine Checklist (`remotion/src/Overlay.tsx`, `scripts/add_popups.py`, plus QA checks).
  - Montserrat everywhere.
  - Frame-exact multicam inserts.
  - Beat-exact speed ramps in `cut_video.py`.
  - Footage audio is dropped under a chosen song.
  - Frame-exact angle timing check in QA.
  - The `front_only` gold title option.
  - `job.py replaces`.
  - A 90s length rule enforced in `storyboard_md.py` and `qa_check.py`.
- **Graphify** (code knowledge graph): `graphify-out/`, with hooks in the repo-root `.claude/settings.json`. The env setup script reinstalls it.
- **Not approved**: "No Days Off" and "Locked In" are archived and were not posted.

## Left to do
- **90s "After Hours" re-cut: NOT APPROVED** (Alfonso, 2026-11-19). Not exported. The 41.8s version stays the only After Hours export.
- **"Locked In" (2026-11-21): APPROVED and exported** as `exports/2026-11-21_locked-in.mp4` (+ .txt, carousel), sent to him. Relight still (top light, deadlift raw 239-243) shown: `output/relight/before_after.jpg`; media ids frame 19d0e23f-a686-44f9-af6b-68b279db4e78, clip d2001c04-cd85-4e3b-a03b-33f5e517eec4, still job 7620bfd8-8f4f-4dc3-ab58-0b8c5447a131. He said go: relit clip made (Wan 3.0 480p 4 s, 6 credits with the video reference; still 2) at `output/relight/top_light_deadlift.mp4` (job 37cbe294-c99b-4070-8661-ed470f9af93e), sent to him. He said yes to a v2: relit clip spliced at cut 68.967-72.967, plus a layered_title 30 fps sync fix; v2 QA PASS, staged at output/staged/final_edit.mp4 (job marked replaces exports/2026-11-21_locked-in.mp4). APPROVED (he posts v2 himself); exported over exports/2026-11-21_locked-in.mp4 (v1 backup at output/work/final_edit_v1.mp4). Done. History of the job:
  - Job: iCloud video `input/icloud_0241S7yc.mov` (raw 114.3-234.7 is an old edit with a copyrighted rap track: excluded) + his song `songs/alfonso_music_063BT4Xb.mp3`.
  - Storyboard done, Cuts done (`output/cut_version.mp4` 89.467 s). Multicam working.
  - 3 Kling angles submitted on Higgsfield (job ids 94067b1c-20fb-44cb-a313-c5ef8dd4b26c, ce7a9a55-41c4-48ca-ad02-7628ef327ab4, f0488184-142e-42f0-9579-8f6f14458df6; ~9 credits). Slots: 17.30 #91 low hero, 36.57 #13 top-down, 55.87 #28 left profile (3 s each). Media ids in the scratchpad `hf_ids.json`.
  - Left: download to `output/flow_pack/returned/angle_1..3.mp4` -> multicam agent `--use-clips` (+ log shots in `output/multicam_shots_log.md`) -> Text/Visuals (gold titles, snap on LOCKED IN hook at 0.668, pop-ups, logo end card `--drips heavy` over 86.1-89.467) -> QA -> Waiting for approval.
  - Hand-off must suggest a relight: Top light on the deadlift, raw 239-243, Wan 3.0 480p 4 s, ~6 credits; only on his yes.
- **Style Lab (2026-11-19)**: published at https://claude.ai/artifact/Xez5Sv5JbCzCsqC7oz1Chc (db/user/assets). Steps in `style-lab/SETUP_PROMPT.md`, brief in `style-lab/STYLE.md`. Brief done (`style-lab/STYLE.md`, `GRADE_AND_TRANSITIONS.md`). Round 1 loaded (15 cards: grade, title, transitions, logo; built by `style-lab/round1/build.py`, outputs in `output/style_lab/r1/`). Style locked after round 4 (rules in `style-lab/STYLE.md`, tool `scripts/style_fx.py`, Director answer 16). White-flicker cut-out = occasional alternate (about 1 video in 4). Nothing open.
- **Effects added (2026-11-19)**: x-ray hit and film-strip flash cut recipes in `docs/effects/`, Director standing answer 13. Waiting on his selfies for the flash cut (balance 908 on 2026-11-20).
- **"Full Send" (2026-11-18)**: NOT APPROVED by Alfonso (2026-11-19), not exported, not posted. Files kept in output/ and output/archive/.
- **"Shh" (2026-11-18)**: NOT APPROVED by Alfonso (2026-11-19), not exported, not posted. Files kept in output/ and output/archive/.
- **New standing answer 11**: gold title back word always behind him, unreadable is fine (config `titles.max_back_cover` 0.95).

## Next step
- **Intro LOCKED + BUILT (2026-11-21):** r6-01 strobe + r6-03 burst+pulse (rotate per video, recorded in `posted/style_rotation.json` from the first real render; first = strobe + heavy drips). Rule in `style-lab/STYLE.md` rule 0 + Director answer 18. Production: `style_fx.py intro`, run automatically by `render_final.py` -> `scripts/finish_fx.py` (also bakes the logo drip end card; `output/work/finish_fx.sh` is retired). `build_overlay_props.py` defaults `title.style: fonzi_intro`. Test on Locked In passed QA: `output/intro_test/final_edit_test.mp4` + frames. Sent to Alfonso. Exported Locked In is unchanged.
- **Intro card restyle (2026-11-21):** Alfonso hates Montserrat on the intro; picked font 11 **Rubik Dirt** (`brand/fonts/`, OFL) + drips like his logo + Fonzi logo behind. Round 5 notes: keep r5-02 (logo behind him) but no drips on the font, logo near full-screen (never clipped), font flickers to the beat; drips all dropped. **Round 6** loaded (r6-01 strobe, r6-02 white flash, r6-03 burst+pulse; `style-lab/round6/build.py`, `output/style_lab/r6/`). 
- **OpenFilm (2026-11-21):** installed (outside the repo, ~/tools/openfilm, rev a1b8d75) for its free media library ONLY: `scripts/openfilm_library.sh`, Director answer 19. SFX + stickers allowed; library music OFF: his music only unless he says so (his answer 2026-11-21). He edits in CapCut.
- **Hook effects (2026-11-21, `docs/effects/hook_effects.md`, standing answer 17):** first test = **Effect 3 Speed jump**: TEST BUILT (15x rep burst, drop on frame 46), staged at ~/workspace/upload_staging/2026-11-21_speed_test.mp4 + output/hooks/, build script scripts/hook_speed.py. Alfonso: "test worked", not going live (stays unposted). Effect 3 is proven; use it as a hook in a future video only when he picks it. Was: on a NEW clip Alfonso will send (tripod, run/jump in and out of frame, 60 fps if possible). When the link arrives: download, build ONE 3 s hook test, stage `~/workspace/upload_staging/<day>_speed_test.mp4` (1080x1920, 30fps, H.264+AAC), ffprobe + frames, send file + frame, wait for his yes.
- **On his "yes"**, from `fonzi-gym-video-editor/`:
  1. Run `python3 scripts/approve.py --alfonso-said-yes --own-footage-confirmed`.
  2. Run `python3 scripts/export_final.py`.
  3. Send him the exported mp4, the caption .txt and the carousel slides.
  4. Run `python3 scripts/job.py set posted done`.
  5. Tell him: if he adds the sound in the app, it starts at 0:59. He posts it himself.
- **If he asks for changes**, send them to the one agent that owns that part, then re-run QA.
- **New video**: `/fonzi-edit <Drive or iCloud link> <brief>`.
  - iCloud shared albums (`photos.icloud.com/shared/album/…`) download via Playwright: capture the `ckdatabasews` records responses and use `resOriginalRes.downloadURL`.

## Key files
- **Moving to another account**: `MOVE_TO_NEW_ACCOUNT.md` (fork, environment + setup script, secrets, first prompt).
- **Identity references**: `references/` (9 character sheets, pose sheets, LEFT-arm sleeve sheets; master tattoo sheet `tattoo_left_arm_master.jpg` added 2026-11-21, the default tattoo reference). Used in every Flow pack.
- **Agents and skill**: `.claude/agents/fonzi-*.md` (director standing answers 1-17), `.claude/skills/fonzi-edit/SKILL.md`, `.claude/settings.json`.
- **Config**: `fonzi-gym-video-editor/config.yaml`, `config/brand.json`.
- **Scripts** (`scripts/`): `job.py`, `cut_video.py`, `multicam_prompt.py`, `multicam_generate.py`, `layered_title.py`, `add_popups.py`, `build_overlay_props.py`, `render_final.py`, `qa_check.py`, `qa_verdict.py`, `approve.py`, `export_final.py`.
- **Overlay**: `remotion/src/Overlay.tsx`, `types.ts`, `fonts.ts`.
- **Current job**: `output/` (`job.json`, `storyboard.json`, `staged/`, `qa_report.md`). The saved Flow top-down clip is at `input/flow_topdown_dbcurl_alfonso.mp4`.

## Key decisions
- **AI angles = Higgsfield Kling 3.0 Omni image-reference 720p** (`kling_o3_image_reference`, std, 3 s, silent) on his credits; Director runs it (standing answer 12). Balance 2026-11-20: 908 credits (plus plan). (Alfonso's standing rules)
- **90 seconds, hard rule.** Every video is 90s ±1s (`config.yaml` `video_length`).
- **Footage and music**: all footage he gives is his. Only his own songs. The footage's baked-in music is always muted; his chosen song never is.
- **Exercises**: name guesses are fine; sets x reps are made up. Every lift gets a gold layered title (Montserrat Black; `front_only` when no back word can read behind him) **and** the pop-up cards.
- **Language**: English only. The one exception is the Spanish lines in the pop-ups. No hashtags on screen.
- **Clips with baked-in text** (`no_text_windows`): nothing is added on top.
- **Camera angles**: at least one top-down angle per video. Free Wan rarely produces a real top-down, so the fallback is a Flow pack that Alfonso makes in Google Flow and sends back (that worked). Angles never fail QA; tell him about any oddities.
- **Spending**: free first (wan-free, then a free-local crop). Paid Seedance only with his yes. No Sora. Apinex was cancelled (the key he pasted should be rotated).
- **Posting**: stage the video and show frames first. He posts it himself. Never post twice.
- **Secrets**: only in `.env`. Never printed or committed.
