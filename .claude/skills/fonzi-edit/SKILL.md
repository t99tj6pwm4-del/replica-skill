---
name: fonzi-edit
description: Run the fonzi-gym-video-editor team on a raw gym video. Use when Alfonso gives a gym video and a brief, e.g. "/fonzi-edit Friday gym video, Form Fix Friday, 60 seconds".
---

Act as the Director of fonzi-gym-video-editor for this request.

1. Read `.claude/agents/fonzi-director.md` and follow it exactly: you allocate the work, you never edit
   video yourself, you never post without Alfonso's yes.
2. Delegate each step, in the locked order, to its own subagent with the Agent tool:
   `fonzi-storyboard` -> `fonzi-cuts` -> `fonzi-multicam` -> `fonzi-text-visuals` -> `fonzi-qa`.
   If one of those agent types is not available in this session, start a general-purpose agent and tell it
   to read `.claude/agents/<name>.md` first and follow it as its instructions.
3. Report after each step: "Storyboard done", "Cuts done", "Multicam done", "Text done",
   "Waiting for approval".
4. If a step fails, stop and tell Alfonso exactly what failed. Never post a broken file.

Brief from Alfonso: $ARGUMENTS
