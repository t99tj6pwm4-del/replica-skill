# HANDOVER

## Done
- 6-agent editor built and pushed (Director, Storyboard, Cuts, Multicam/B-Roll, Text/Visuals, QA) + `/fonzi-edit` skill.
- Free AI angles (wan-free on Hugging Face) with free-local crop fallback; Seedance only on Alfonso's yes.
- CapCut effects library, 100-shot multicam library, Layered Title (Documentary Gold) reading "FONZI" / "STAYS FIT".
- "A Week of Work" (input/drive_1f6cZwaA.mp4): QA PASS earlier; job archived in output/archive/20261115-160314/.
- "Locked In / Bulking season" (input/drive_1E3BsV75.mp4, brief "1:30 second clip"): 91.9s, QA PASS, staged at output/staged/final_edit.mp4, with layered title FONZI/STAYS FIT at 53.6-54.6 (Alfonso asked; title_style layered-gold-plus keeps other graphics; line positions first_y/intro_y/last_y). Exercise lower-thirds replaced by 7 gold layered exercise titles (storyboard exercise_titles; tool: hard matte, temporal smoothing, hold_mask). QA PASS, staged again.
- QA tooling fixes: optional layered_title/effects files no longer crash qa_check; angle timing ignores base-cut jump cuts. Remotion ListCard (compact) + layout.titleOffsetY added.
- Claude Code mods: auto-compact 500k + this handover hook (.claude/settings.json).

## Left to do
- "Locked In" waits on Alfonso: own footage (and who filmed the graded part), baked-in music licence (~raw 2:00 on; mute if not his), exercise names (seated machine shrug vs calf raise), sets x reps or skip, caption (suggested: "Bulking season: lifting heavy, whole food, creatine, sleep. Comment LOCKED IN if you're in."), optional redo of AI close-up angle 3 (55.2-59.1s, distorted shouting face).
- "A Week of Work" (archived) still waits on his yes + answers if he wants it.
- Optional: HF_TOKEN env var in environment settings.

## Next step
- On Alfonso's "approved" for Locked In: scripts/approve.py --alfonso-said-yes (+ --own-footage-confirmed if he confirms), scripts/export_final.py, send him the file + caption. He posts himself.

## Key files
- .claude/agents/fonzi-*.md, .claude/skills/fonzi-edit/SKILL.md, .claude/settings.json
- fonzi-gym-video-editor/config.yaml, config/brand.json, scripts/*.py, remotion/src/Overlay.tsx
- docs/multicam_shot_library.md, docs/capcut_effects_library.md
- output/multicam_shots_log.md, output/effects_log.md, posted/ledger.json

## Key decisions
- Only Alfonso's own footage and own songs; English-only text; his captions verbatim; no hashtags on screen.
- Stage first, show frames, never post without his yes; he posts himself; never post twice.
- Fully automatic: he uploads one video, nothing else. No Sora; Omni only in Google Flow.
- Camera angles never fail QA. Cheapest/free first. Layered title only when it fits.
- Secrets only in .env (never printed or committed).
