# HANDOVER

## Done
- 6-agent editor built and pushed (Director, Storyboard, Cuts, Multicam/B-Roll, Text/Visuals, QA) + `/fonzi-edit` skill.
- Free AI angles (wan-free on Hugging Face, quota exhausted until ~16:00 UTC 11-16) with free-local crop fallback; Seedance only on Alfonso's yes.
- "Locked In / Bulking season" (input/drive_1E3BsV75.mp4, brief "1:30 second clip"): 91.9s. title_style layered-gold-plus: FONZI/STAYS FIT at 53.6-54.6 + 7 gold layered exercise titles (storyboard exercise_titles, each with sets x reps). Baked-in music muted by rule (work/audio_rule.json). No top-down shot this time (Alfonso: "Finish now, no top-down").
- Standing answers (2026-11-15): all his footage is his; always mute baked-in music; exercise-name guesses ok; make up sets x reps; Claude picks caption; at least one top-down multicam shot per video (config multicam.require_top_down).
- Graphify installed (code-only graph in fonzi-gym-video-editor/graphify-out/, hooks in root .claude/settings.json, verified firing; env setup script reinstalls it each session). Check the graph first; run `graphify update .` after structural changes.
- Montserrat everywhere (Alfonso 2026-11-16): remotion/src/fonts.ts DISPLAY = Montserrat Black; scripts/layered_title.py titles in Montserrat Black, small sets x reps line bigger (SemiBold). Committed b399eec.

## Left to do
- "After Hours" 90s re-cut (job.py replaces exports/2026-11-17_after-hours.mp4): QA PASS, staged at output/staged/final_edit.mp4 (89.7s, song 59.087-148.84). WAITING for Alfonso's yes.

## Next step
- On his yes: approve.py --alfonso-said-yes --own-footage-confirmed; export_final.py; send file + caption "After hours, no shortcuts. Arms, back, shoulders, chest and legs in one session. Save it for your next gym day." + 9 carousel slides; job.py set posted done. Song in app: start at 0:59.

## Key files
- .claude/agents/fonzi-*.md, .claude/skills/fonzi-edit/SKILL.md, .claude/settings.json
- fonzi-gym-video-editor/config.yaml, config/brand.json, scripts/*.py (render_final, layered_title, qa_check, shot_library), remotion/src/Overlay.tsx, remotion/src/fonts.ts
- output/storyboard.json, output/work/overlay_props.json, output/staged/, posted/ledger.json

## Key decisions
- HARD RULE (2026-11-17): every video is 90 seconds (+/-1s, config video_length; enforced by storyboard_md.py and qa_check.py).
- Only Alfonso's own footage and own songs; English-only text (except the Spanish lines of the gym-reel pop-up cards); his captions verbatim; no hashtags on screen.
- Stage first, show frames, never post without his yes; he posts himself; never post twice.
- Fully automatic: he uploads one video, nothing else. No Sora; Omni only in Google Flow. Remote Control allowed (Alfonso 2026-11-16: "PC + Remote Control" for free local AI angles); his PC TABLET-BK33DP824133M4 offers no usable folder yet (only Downloads, not_available) and likely lacks a GPU for local video AI; fonzi-ai folder added but still not_available (Windows app version or feature not on for his account). Claude in Chrome cannot reach this cloud session without that link. Alfonso (2026-11-16): stick to the regular method (free HF angles + free-local fallback) for now; offer Flow pack only if he asks; "check again" when he is at the PC.
- Camera angles never fail QA. Cheapest/free first. Fonts: Montserrat everywhere.
- Secrets only in .env (never printed or committed).
