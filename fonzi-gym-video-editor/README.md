# fonzi-gym-video-editor

A 6-agent gym video editor for **Fonzi.stays.fit** (Facebook Page) and **@fonzi.stays.fit** (Instagram).
Raw gym video in, YouTube-style vertical edit out: animated word-by-word captions, title card,
lower-thirds, progress bar, callouts, punch-ins, slow-mo, multicam angle changes / B-roll, and a
"Save this" end card.

## The team

| Agent | File | One job |
|---|---|---|
| Director (the boss) | `.claude/agents/fonzi-director.md` | Allocates the work, tracks it, reports to Alfonso. Never edits, never posts on its own. |
| Storyboard | `.claude/agents/fonzi-storyboard.md` | Plans the video: `output/storyboard.md` |
| Cuts | `.claude/agents/fonzi-cuts.md` | ffmpeg cuts only: `output/cut_version.mp4` |
| Multicam / B-Roll | `.claude/agents/fonzi-multicam.md` | (a) writes the one frozen prompt `output/multicam_prompt.txt`; (b) sends it + your clip to the generator and cuts the angles in: `output/multicam_version.mp4` |
| Text / Visuals | `.claude/agents/fonzi-text-visuals.md` | Whisper captions + Remotion motion graphics: `output/final_edit.mp4` |
| Final Approval / QA | `.claude/agents/fonzi-qa.md` | Read-only pass/fail: `output/qa_report.md` |

Locked order:

```
Director -> Storyboard -> Cuts -> Multicam/B-Roll -> Text/Visuals -> Final Approval
-> Alfonso approves -> post to Meta
```

If a step fails, the Director stops and tells you exactly what failed; on your go it re-assigns that one
job only. A failed QA goes back to the one agent that must fix it, with the exact fix.

## Run it

One-time setup (needs ffmpeg, Python 3.10+, Node 18+):

```bash
bash fonzi-gym-video-editor/scripts/setup.sh
```

1. Put the raw video in `fonzi-gym-video-editor/input/`
2. (Optional) put your mp3s in `fonzi-gym-video-editor/songs/`
3. From the repo root, talk to the Director:

```bash
claude --agent fonzi-director "Friday gym video, Form Fix Friday, 60 seconds. Video: input/my_video.mp4. It is my own footage."
```

Inside the Claude app or a Claude Code session, the same thing is:

```
/fonzi-edit Friday gym video, Form Fix Friday, 60 seconds. Video: input/my_video.mp4. It is my own footage.
```

Add B-roll and your own caption in the same message, for example:
`B-roll at 0:23, bench press lockout. Caption: "Form Fix Friday. Save this one."`
(B-roll times are times in the cut version; your caption is posted word for word.)

The Director reports after each step ("Storyboard done", "Cuts done", "Multicam done", "Text done",
"Waiting for approval") and stops for your yes before anything is posted.

### Multicam / B-roll generator

Set in `config.yaml`. Default **Seedance 2.5**, second choice **Kling Multi-Cam**. Google Omni and Sora
are blocked. It needs your own key: put `FAL_KEY=...` in `.env`. Without a key the Multicam step stops and
says so; it never fakes a clip. Your original audio is always kept as the truth.

## What you get in `output/`

| File | From |
|---|---|
| `storyboard.md`, `storyboard.json` | Storyboard Agent |
| `cut_version.mp4` | Cuts Agent (1080x1920, 30fps, H.264 + AAC, 60-90s) |
| `multicam_prompt.txt` (+ `broll_prompt.txt`) | Multicam/B-Roll Agent, prompt-maker job |
| `multicam/*.mp4`, `multicam_version.mp4` | Multicam/B-Roll Agent, generator job |
| `final_edit.mp4` | Text/Visuals Agent |
| `carousel/` | slide images + `carousel.json` (exercises + sets x reps) when the video has 2+ exercises |
| `qa/frame_1.jpg` .. `frame_3.jpg`, `qa/compare_*.jpg`, `qa_report.md` | Final Approval Agent |
| `staged/` | the passed video waiting for your yes |

Starting a new job archives the previous one to `output/archive/`.

## Posting to Meta

```bash
cp .env.example .env        # then fill in your Page ID, Page token and Instagram user ID
python3 scripts/post_to_meta.py --dry-run     # shows exactly what would go out; posts nothing
python3 scripts/post_to_meta.py               # posts the Reel to the Page + Instagram
python3 scripts/post_to_meta.py --carousel    # also posts the exercises carousel
```

Built-in safety:

- tokens are read from `.env` only (git-ignored); nothing is hardcoded
- it refuses to post unless QA passed **and** your approval is recorded for that exact file
- it never posts the same video twice: `posted/ledger.json` remembers every post and catches the same
  file, the same raw footage, or a visually identical re-export

## Safety rules (locked into the agents and the scripts)

- Only your own footage, from `input/`. Nothing is downloaded from other creators.
- Only your own audio: the video's sound plus your mp3s in `songs/`. No stock or AI music.
- English only for all text the team writes; your own caption posts verbatim.
- Every edit is staged in `output/` and you see preview frames before anything is posted.
- If a step fails, everything stops and you are told exactly what failed. A broken file is never posted.

## Make it yours

- **Brand colour / handle:** `config/brand.json` (`color` is the caption highlight and graphics colour)
- **Graphics and animation:** `remotion/src/Overlay.tsx` (preview with `cd remotion && npm run studio`)
- **Generator, angles, shot length, spend guard:** `config.yaml`
- **Optional add-ons** (OpenMontage, Open Generative AI, VoiceStudio, memory / docs / skills tools, the
  free OpenCode option): `docs/TOOLS.md`, installed one at a time with `bash scripts/install_extras.sh <name>`
- **Caption accuracy:** set `WHISPER_MODEL=medium.en` in `.env` for better transcription (slower)

## Notes

- Motion graphics are rendered with [Remotion](https://www.remotion.dev), the composition engine
  [OpenMontage](https://github.com/OpenMontageInc/OpenMontage) also uses. OpenMontage's own code is
  AGPL-licensed and is not copied into this project. Remotion is free for individuals and small teams;
  larger companies need a Remotion licence.
- Fonts (Anton, Montserrat) are bundled under the SIL Open Font License, so renders work offline.
- Whisper runs locally through `faster-whisper`; the first run downloads the model.
