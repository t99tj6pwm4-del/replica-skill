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
- **Waiting for Alfonso's yes** on the 90s "After Hours". If a new `/fonzi-edit` job starts first, `job.py init` archives it to `output/archive/<time>/` (staged mp4 + post.json kept there).

## Next step
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
- **Agents and skill**: `.claude/agents/fonzi-*.md` (director standing answers 1-10), `.claude/skills/fonzi-edit/SKILL.md`, `.claude/settings.json`.
- **Config**: `fonzi-gym-video-editor/config.yaml`, `config/brand.json`.
- **Scripts** (`scripts/`): `job.py`, `cut_video.py`, `multicam_prompt.py`, `multicam_generate.py`, `layered_title.py`, `add_popups.py`, `build_overlay_props.py`, `render_final.py`, `qa_check.py`, `qa_verdict.py`, `approve.py`, `export_final.py`.
- **Overlay**: `remotion/src/Overlay.tsx`, `types.ts`, `fonts.ts`.
- **Current job**: `output/` (`job.json`, `storyboard.json`, `staged/`, `qa_report.md`). The saved Flow top-down clip is at `input/flow_topdown_dbcurl_alfonso.mp4`.

## Key decisions (Alfonso's standing rules)
- **90 seconds, hard rule.** Every video is 90s ±1s (`config.yaml` `video_length`).
- **Footage and music**: all footage he gives is his. Only his own songs. The footage's baked-in music is always muted; his chosen song never is.
- **Exercises**: name guesses are fine; sets x reps are made up. Every lift gets a gold layered title (Montserrat Black; `front_only` when no back word can read behind him) **and** the pop-up cards.
- **Language**: English only. The one exception is the Spanish lines in the pop-ups. No hashtags on screen.
- **Clips with baked-in text** (`no_text_windows`): nothing is added on top.
- **Camera angles**: at least one top-down angle per video. Free Wan rarely produces a real top-down, so the fallback is a Flow pack that Alfonso makes in Google Flow and sends back (that worked). Angles never fail QA; tell him about any oddities.
- **Spending**: free first (wan-free, then a free-local crop). Paid Seedance only with his yes. No Sora. Apinex was cancelled (the key he pasted should be rotated).
- **Posting**: stage the video and show frames first. He posts it himself. Never post twice.
- **Secrets**: only in `.env`. Never printed or committed.
