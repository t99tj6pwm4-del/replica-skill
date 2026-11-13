# fonzi-gym-video-editor

A 5-agent gym video editor for **Fonzi.stays.fit** (Facebook Page) and **@fonzi.stays.fit** (Instagram).
Raw gym video in, YouTube-style vertical edit out: animated word-by-word captions, title card,
lower-thirds, progress bar, callouts, punch-ins, slow-mo, and a "Save this" end card.

## The team

| Agent | File | One job |
|---|---|---|
| Director (the boss) | `.claude/agents/fonzi-director.md` | Allocates the work, tracks it, reports to Alfonso. Never edits, never posts on its own. |
| Storyboard | `.claude/agents/fonzi-storyboard.md` | Plans the video: `output/storyboard.md` |
| Cuts | `.claude/agents/fonzi-cuts.md` | ffmpeg cuts only: `output/cut_version.mp4` |
| Text / Visuals | `.claude/agents/fonzi-text-visuals.md` | Whisper captions + Remotion motion graphics: `output/final_edit.mp4` |
| Final Approval / QA | `.claude/agents/fonzi-qa.md` | Read-only pass/fail: `output/qa_report.md` |

Locked order:

```
Director receives video -> Storyboard plans -> Cuts cuts -> Text/Visuals adds captions + visuals
-> Final Approval checks -> Alfonso approves -> post to Meta
```

If a step fails, the Director re-assigns that one job only. A failed QA goes back to the one agent that
must fix it, with the exact fix.

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

The Director reports after each step ("Storyboard done", "Cuts done", "Text done", "Waiting for approval")
and stops for your yes before anything is posted.

## What you get in `output/`

| File | From |
|---|---|
| `storyboard.md`, `storyboard.json` | Storyboard Agent |
| `cut_version.mp4` | Cuts Agent (1080x1920, 30fps, H.264 + AAC, 60-90s) |
| `final_edit.mp4` | Text/Visuals Agent |
| `carousel/` | slide images + `carousel.json` (exercises + sets x reps) when the video has 2+ exercises |
| `qa/frame_1.jpg` .. `frame_3.jpg`, `qa_report.md` | Final Approval Agent |
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

## Make it yours

- **Brand colour / handle:** `config/brand.json` (`color` is the caption highlight and graphics colour)
- **Graphics and animation:** `remotion/src/Overlay.tsx` (preview with `cd remotion && npm run studio`)
- **Caption accuracy:** set `WHISPER_MODEL=medium.en` in `.env` for better transcription (slower)

## Notes

- Motion graphics are rendered with [Remotion](https://www.remotion.dev), the composition engine
  [OpenMontage](https://github.com/OpenMontageInc/OpenMontage) also uses. OpenMontage's own code is
  AGPL-licensed and is not copied into this project. Remotion is free for individuals and small teams;
  larger companies need a Remotion licence.
- Fonts (Anton, Montserrat) are bundled under the SIL Open Font License, so renders work offline.
- Whisper runs locally through `faster-whisper`; the first run downloads the model.
