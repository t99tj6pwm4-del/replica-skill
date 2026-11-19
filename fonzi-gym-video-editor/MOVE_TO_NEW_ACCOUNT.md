# Moving the gym video editor to another Claude account

Everything the team needs (agents, `/fonzi-edit` skill, scripts, rules, reference sheets, sound effects,
HANDOVER.md) is in the GitHub repo `t99tj6pwm4-del/replica-skill`, branch `claude/blissful-hamilton-k7clws`.
The repo is public, so the new account can copy it. Four steps, about 15 minutes.

## 1. Copy the repo to the new account's GitHub
1. Sign in to GitHub with the account the new Claude account will use.
2. Open https://github.com/t99tj6pwm4-del/replica-skill and press **Fork**.
3. **Untick "Copy the main branch only"**, so the branch `claude/blissful-hamilton-k7clws` comes too. Create the fork.
   (If the new account uses the same GitHub account as now, skip this step: the repo is already there.)

## 2. Connect GitHub in the new Claude account
In the new Claude account: claude.ai, Settings, Connectors (or claude.ai/code), connect GitHub and allow the
forked repo. Install the Claude GitHub App on it if asked.

## 3. Make the cloud environment (claude.ai/code, Environments, New)
- **Name:** `fonzi-gym-video-editor`
- **Repository:** the forked `replica-skill`
- **Network access:** Unrestricted (it downloads from iCloud, Google Drive, Hugging Face, GitHub, Google Fonts)
- **Setup script** (paste exactly):

```bash
if [ -d replica-skill/fonzi-gym-video-editor ]; then
  cd replica-skill/fonzi-gym-video-editor
  python3 -m pip install -q -r requirements.txt
  (cd remotion && npm install --no-audit --no-fund --loglevel=error)
  mkdir -p "$HOME/.claude/skills"
  for s in kinetic-multicam cine-multicam-capcut; do
    [ -d "$HOME/.claude/skills/$s" ] || git clone -q "https://github.com/aipauloshimas/$s" "$HOME/.claude/skills/$s"
  done
  python3 -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"
  (uv tool install -q graphifyy || pipx install graphifyy) && "$HOME/.local/bin/graphify" install >/dev/null && "$HOME/.local/bin/graphify" update . || true
fi
```

- **Network secrets** (needed for the free Wan camera angles; add in the environment's secrets, never in chat):
  - host `huggingface.co`, header `Authorization`, value `Bearer <your Hugging Face token>`
  - host `zerogpu-aoti-wan2-2-fp8da-aoti-faster.hf.space`, header `Authorization`, same `Bearer <token>`
  - Get the token at huggingface.co, Settings, Access Tokens (a "read" token is enough). Without it the
    angles fall back to free crops of your footage; everything else still works.
  - Optional only: `FAL_KEY` (paid Seedance) and the `META_*` keys (auto-posting). You post yourself, so skip them.

## 4. Start a session and paste this as the first message
Start a new Claude Code session on that environment and repo, then paste:

```
This is my fonzi-gym-video-editor project, moved from my other account. Check out the branch
claude/blissful-hamilton-k7clws and keep working on it (push only to that branch, no pull requests).
Read fonzi-gym-video-editor/HANDOVER.md first, then .claude/agents/fonzi-director.md, and follow every
standing rule in them exactly as before. Then check the setup: python requirements, remotion npm install,
Whisper model, rembg, graphify, the Hugging Face secret for wan-free (test it once, do not print it).
Tell me in plain words what works and what is missing. Don't edit any video until I send one with /fonzi-edit.
```

## What does NOT move (send again when needed)
- **Your songs** (`songs/*.mp3`) and **raw footage** (`input/`) are not in GitHub. Send the iCloud/Drive link with
  `/fonzi-edit` as usual; the song too, the first time it is used.
- **Finished exports** (`exports/`) stay in the old session; you already have the files you posted.
- `posted/ledger.json` (what was already handed to you) DOES move, so the duplicate check still works.
- The old session's history doesn't move, but HANDOVER.md and the agent files hold every rule and decision.
