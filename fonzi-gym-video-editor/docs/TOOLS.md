# Tools and add-ons

What the editor uses out of the box, and the optional repos Alfonso picked. Every repo below was checked
to exist. Add-ons are other people's software: each is installed only when you name it with
`bash scripts/install_extras.sh <name>`, never automatically.

## Built in (nothing to install beyond `scripts/setup.sh`)

| Job | Tool |
|---|---|
| Cuts | ffmpeg / ffprobe |
| Transcription | Whisper (`faster-whisper`, runs on your machine) |
| Motion graphics | Remotion (the composition engine OpenMontage uses) |
| Multicam prompt templates | skills `kinetic-multicam` and `cine-multicam-capcut`, cloned to `~/.claude/skills/` by `setup.sh` |
| Multicam / B-roll generation | Order in `config.yaml`: Google Flow (free, default; you run it at flow.google.com), Seedance 2.5, Kling Multi-Cam, LTX-2.5, MiniMax H3; `free-local` crops as last resort. **No Sora. Omni only inside Google Flow for multicam reframes.** |
| Posting | Meta Graph API (`scripts/post_to_meta.py`) |

## Video add-ons

| Name | Repo | What it is for | Notes |
|---|---|---|---|
| `openmontage` | [OpenMontageInc/OpenMontage](https://github.com/OpenMontageInc/OpenMontage) | Full agentic video studio: research, script, assets, edit, render | AGPL-3.0. Cloned to `vendor/` and used as a separate tool; its code is not copied into this project. |
| `open-generative-ai` | [Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) | AI images and cinematic video for B-roll and missing shots | Cloud models need your own API key. Only ever fed your own footage. Omni and Sora stay blocked. |
| `voicestudio` | [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) | Local voice cloning for narration, on your own machine | AGPL-3.0. Narration only when you ask for it. It is never used for music. |

Audio rule: the editor uses **only audio you uploaded** (the video's own sound and your mp3s in `songs/`).
No stock music and no AI music; `cut_video.py` refuses a song from anywhere else.

## Claude Code infrastructure

| Name | Repo | Group | Verdict |
|---|---|---|---|
| `context7` | [upstash/context7](https://github.com/upstash/context7) | Docs | Useful: live docs for Remotion, ffmpeg, the Graph API |
| `playwright-mcp` | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | Tools | Useful for checking a posted Reel or a preview page in a browser |
| `firecrawl` | [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | Tools | Optional, needs your own key. Reading pages only: never for downloading other creators' videos |
| `agentmemory` | [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | Memory | Optional: remembers your preferences between sessions |
| `codebase-memory` | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | Memory | Optional: remembers this repo. Its installer is a download-and-run script, so the helper only prints the command for you to run yourself |
| `claude-hud` | [jarrodwatts/claude-hud](https://github.com/jarrodwatts/claude-hud) | Token-saver | Optional: shows context and usage in the status line |
| `caveman` | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Token-saver | Optional: terse replies to save tokens. Leave it off while agents write captions or prompts |
| `mattpocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills) | Skills | Optional: coding workflow skills, helps when changing this project's code |
| `anthropic-skills` | [anthropics/skills](https://github.com/anthropics/skills) | Skills | Optional: document and example skills |
| `youtube-skills` | [ZeroPointRepo/youtube-skills](https://github.com/ZeroPointRepo/youtube-skills) | Skills | Optional: transcripts, video search, channels. Research only: never to download or re-upload someone else's video |
| `composio-skills` | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | Skills | Optional: connect other apps |
| `learn-claude-code` | [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | Harness | Reading material on how agent harnesses work; nothing to wire in |
| `awesome-mcp` | [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | Tools | A list to browse; nothing to wire in |

"youtube-skills" and "codebase-memory-mcp" were named without an owner; the repos above are the ones that
match those names. Tell the Director if you meant different ones.

## Free coding option (only when you ask for a free run)

`opencode`: OpenCode + DeepSeek V4 Flash through OpenCode Zen. It does not replace Claude Code and no
agent switches to it on its own. Say "free run" and the Director will point you to
`bash scripts/install_extras.sh opencode`, which prints the install command for you to run.

## Generator notes

- Seedance 2.5 is called through fal.ai (`bytedance/seedance-2.5/reference-to-video`, task `editing`),
  with your own `FAL_KEY` in `.env`. At 720p it costs roughly half a dollar per generated second, so the
  generator stops and asks before sending more than `generator.max_generated_seconds` (see `config.yaml`).
  Limits: 4-30s output, reference clips 1.8-30.2s.
- "Kling Multi-Cam": no public Kling endpoint with that name could be confirmed. `config.yaml` has the
  slot (`kling-multicam`, 3-10s reference, 5-10s out, 9:16) with an empty model id; fill in the Kling
  video-reference model your account has before using it.
- No key, empty model id, or a clip returned at the wrong length: the generator stops and says exactly
  why. Nothing is faked.
