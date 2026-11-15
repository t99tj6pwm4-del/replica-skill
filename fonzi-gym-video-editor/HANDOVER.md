# HANDOVER

## Done
- 6-agent editor built and pushed (Director, Storyboard, Cuts, Multicam/B-Roll, Text/Visuals, QA) + `/fonzi-edit` skill.
- Free AI angles (wan-free on Hugging Face) with free-local crop fallback; Seedance only on Alfonso's yes.
- CapCut effects library, 100-shot multicam library, Layered Title (Documentary Gold) reading "FONZI" / "STAYS FIT".
- "A Week of Work" (input/drive_1f6cZwaA.mp4): QA PASS, staged at output/staged/final_edit.mp4.
- Claude Code mods: auto-compact 500k + this handover hook (.claude/settings.json).

## Left to do
- "A Week of Work" waits on Alfonso: (1) confirm all footage is his (esp. squat clip at 0:17, NY cap); (2) sets/reps per lift or "skip"; (3) caption (suggested: "A week of work in one minute. Which lift are you hitting today?") or his own; then "approved".
- Optional: add HF_TOKEN env var in the environment settings so new sessions get AI angles.
- Layered title not yet tried on a real video.

## Next step
- On Alfonso's "approved": run scripts/approve.py then scripts/export_final.py and send him the file + caption from exports/. He posts it himself.

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
