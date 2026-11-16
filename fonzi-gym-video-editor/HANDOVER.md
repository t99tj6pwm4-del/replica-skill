# HANDOVER

## Done
- 6-agent editor built and pushed (Director, Storyboard, Cuts, Multicam/B-Roll, Text/Visuals, QA) + `/fonzi-edit` skill.
- Free AI angles (wan-free on Hugging Face, quota exhausted until ~16:00 UTC 11-16) with free-local crop fallback; Seedance only on Alfonso's yes.
- "Locked In / Bulking season" (input/drive_1E3BsV75.mp4, brief "1:30 second clip"): 91.9s. title_style layered-gold-plus: FONZI/STAYS FIT at 53.6-54.6 + 7 gold layered exercise titles (storyboard exercise_titles, each with sets x reps). Baked-in music muted by rule (work/audio_rule.json). No top-down shot this time (Alfonso: "Finish now, no top-down").
- Standing answers (2026-11-15): all his footage is his; always mute baked-in music; exercise-name guesses ok; make up sets x reps; Claude picks caption; at least one top-down multicam shot per video (config multicam.require_top_down).
- Graphify installed (code-only graph in fonzi-gym-video-editor/graphify-out/, hooks in root .claude/settings.json, verified firing; env setup script reinstalls it each session). Check the graph first; run `graphify update .` after structural changes.
- Montserrat everywhere (Alfonso 2026-11-16): remotion/src/fonts.ts DISPLAY = Montserrat Black; scripts/layered_title.py titles in Montserrat Black, small sets x reps line bigger (SemiBold). Committed b399eec.

## Left to do
- Re-render Locked In with Montserrat: `python3 scripts/render_final.py --title-style layered-gold-plus` (do NOT re-run build_overlay_props.py; overlay_props.json has hand edits).
- Check all 8 gold title frames (work/layered_title*_frame.png) fit: back word partly behind him, nothing on face, clear of progress bar. Check mute + sets x reps.
- Run QA, stage, send Alfonso video + frames; remind him sound is muted (add a sound in-app).
- "A Week of Work" (archived) still waits on his yes if he wants it.

## Next step
- Re-render with Montserrat (above). Then on Alfonso's "approved": scripts/approve.py --alfonso-said-yes --own-footage-confirmed, scripts/export_final.py, send file + caption "Bulking season: lifting heavy, whole food, creatine, sleep. Comment LOCKED IN if you're in.", job.py set posted done. He posts himself.

## Key files
- .claude/agents/fonzi-*.md, .claude/skills/fonzi-edit/SKILL.md, .claude/settings.json
- fonzi-gym-video-editor/config.yaml, config/brand.json, scripts/*.py (render_final, layered_title, qa_check, shot_library), remotion/src/Overlay.tsx, remotion/src/fonts.ts
- output/storyboard.json, output/work/overlay_props.json, output/staged/, posted/ledger.json

## Key decisions
- Only Alfonso's own footage and own songs; English-only text; his captions verbatim; no hashtags on screen.
- Stage first, show frames, never post without his yes; he posts himself; never post twice.
- Fully automatic: he uploads one video, nothing else. No Sora; Omni only in Google Flow. No Remote Control.
- Camera angles never fail QA. Cheapest/free first. Fonts: Montserrat everywhere.
- Secrets only in .env (never printed or committed).
