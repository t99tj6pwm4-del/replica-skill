# Moving the gym video editor to a NEW Claude account

## The easy way (Claude sets itself up)
1. **Plan:** the new Claude account needs a paid plan (Pro or Max) to use Claude Code on the web.
2. **GitHub:** go to https://claude.ai/connect-github while signed in to the NEW Claude account and connect GitHub.
   - Same GitHub account as now: allow the repo `replica-skill`. Done.
   - Different GitHub account: first fork https://github.com/t99tj6pwm4-del/replica-skill (untick
     "Copy the main branch only"), then allow the fork.
3. **Open** https://claude.ai/code, pick the `replica-skill` repository, keep the Default environment, and start.
4. **Paste** the "first message" prompt at the bottom of this page. Claude makes the environment (you approve
   a card), saves the setup script, and opens a secure form for your Hugging Face token.
5. When it says the new environment is ready, **start one more new session** on that environment, then send
   `/fonzi-edit <link>` like always.

The manual way (if you prefer to click it yourself) is below.

# Manual way

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
This is my fonzi-gym-video-editor project, moved from my other account. If this session is not on an
environment called fonzi-gym-video-editor yet, create one for me first: personal, unrestricted network,
for the replica-skill repo, with the setup script from fonzi-gym-video-editor/MOVE_TO_NEW_ACCOUNT.md
(run it here once first to check it works), and ask me for my Hugging Face token with the secure form
for huggingface.co and zerogpu-aoti-wan2-2-fp8da-aoti-faster.hf.space. Then tell me to start a new
session on it. Check out the branch
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
