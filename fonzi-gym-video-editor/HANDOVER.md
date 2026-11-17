# HANDOVER

## Done
- 6-agent editor built and pushed (Director, Storyboard, Cuts, Multicam/B-Roll, Text/Visuals, QA) + `/fonzi-edit` skill.
- Free AI angles (wan-free on Hugging Face, quota exhausted until ~16:00 UTC 11-16) with free-local crop fallback; Seedance only on Alfonso's yes.
- "Locked In / Bulking season" (input/drive_1E3BsV75.mp4, brief "1:30 second clip"): 91.9s. title_style layered-gold-plus: FONZI/STAYS FIT at 53.6-54.6 + 7 gold layered exercise titles (storyboard exercise_titles, each with sets x reps). Baked-in music muted by rule (work/audio_rule.json). No top-down shot this time (Alfonso: "Finish now, no top-down").
- Standing answers (2026-11-15): all his footage is his; always mute baked-in music; exercise-name guesses ok; make up sets x reps; Claude picks caption; at least one top-down multicam shot per video (config multicam.require_top_down).
- Graphify installed (code-only graph in fonzi-gym-video-editor/graphify-out/, hooks in root .claude/settings.json, verified firing; env setup script reinstalls it each session). Check the graph first; run `graphify update .` after structural changes.
- Montserrat everywhere (Alfonso 2026-11-16): remotion/src/fonts.ts DISPLAY = Montserrat Black; scripts/layered_title.py titles in Montserrat Black, small sets x reps line bigger (SemiBold). Committed b399eec.

## Left to do
- "No Days Off" (input/drive_1pnZDifS.mp4, brief "Random clicks some will always have font don't add any to those lets really make it cinematic and punchy"): 47.8s, QA PASS, staged at output/staged/final_edit.mp4 + post.json. Alfonso (2026-11-17): not approved, not posting it; doing a new video instead. Gets archived at the next job.py init. No-text windows (his baked titles) 9.6-16.733, 25.867-30.367 kept clean. 3 gold titles (EZ BAR front_only). 4 wan-free AI angles kept by his choice (fake shirt text angle_1, no real top-down). Muted.
- Locked In: dropped re-render, not approved.

## Next step
- Next video: run /fonzi-edit <link> <brief> when Alfonso sends it.

## Key files
- .claude/agents/fonzi-*.md, .claude/skills/fonzi-edit/SKILL.md, .claude/settings.json
- fonzi-gym-video-editor/config.yaml, config/brand.json, scripts/*.py (render_final, layered_title, qa_check, shot_library), remotion/src/Overlay.tsx, remotion/src/fonts.ts
- output/storyboard.json, output/work/overlay_props.json, output/staged/, posted/ledger.json

## Key decisions
- Only Alfonso's own footage and own songs; English-only text (except the Spanish lines of the gym-reel pop-up cards); his captions verbatim; no hashtags on screen.
- Stage first, show frames, never post without his yes; he posts himself; never post twice.
- Fully automatic: he uploads one video, nothing else. No Sora; Omni only in Google Flow. Remote Control allowed (Alfonso 2026-11-16: "PC + Remote Control" for free local AI angles); his PC TABLET-BK33DP824133M4 offers no usable folder yet (only Downloads, not_available) and likely lacks a GPU for local video AI; fonzi-ai folder added but still not_available (Windows app version or feature not on for his account). Claude in Chrome cannot reach this cloud session without that link. Alfonso (2026-11-16): stick to the regular method (free HF angles + free-local fallback) for now; offer Flow pack only if he asks; "check again" when he is at the PC.
- Camera angles never fail QA. Cheapest/free first. Fonts: Montserrat everywhere.
- Secrets only in .env (never printed or committed).
