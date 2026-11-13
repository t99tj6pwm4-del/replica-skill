#!/usr/bin/env bash
# Optional add-ons Alfonso picked. Nothing here is needed to edit a video, and nothing is installed
# unless you name it. Each one is someone else's software: read docs/TOOLS.md first.
#
#   bash scripts/install_extras.sh            # list what is available
#   bash scripts/install_extras.sh context7   # install one
set -euo pipefail
cd "$(dirname "$0")/.."
VENDOR="$PWD/vendor"   # git-ignored

clone() { mkdir -p "$VENDOR"; [ -d "$VENDOR/$2" ] || git clone --depth 1 "https://github.com/$1" "$VENDOR/$2"; echo "cloned to vendor/$2"; }

case "${1:-list}" in
  # --- video ---
  openmontage)        clone OpenMontageInc/OpenMontage OpenMontage
                      echo "Next: cd vendor/OpenMontage && make install   (AGPL-3.0: keep it in vendor/, do not copy its code into this project)";;
  open-generative-ai) clone Anil-matcha/Open-Generative-AI Open-Generative-AI
                      echo "Next: follow vendor/Open-Generative-AI/README.md. Cloud models need your own API key.";;
  voicestudio)        clone debpalash/VoiceStudio VoiceStudio
                      echo "Next: follow vendor/VoiceStudio/README.md to install the app on your own machine (local voice cloning, AGPL-3.0).";;
  # --- Claude Code infrastructure ---
  context7)           claude mcp add context7 -- npx -y @upstash/context7-mcp;;
  playwright-mcp)     claude mcp add playwright npx @playwright/mcp@latest;;
  firecrawl)          : "${FIRECRAWL_API_KEY:?Set FIRECRAWL_API_KEY in your shell first (your own key)}"
                      claude mcp add firecrawl -e FIRECRAWL_API_KEY="$FIRECRAWL_API_KEY" -- npx -y firecrawl-mcp;;
  agentmemory)        npx skills add rohitg00/agentmemory -y;;
  codebase-memory)    echo "Run its installer yourself after reading it:"
                      echo "  curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash";;
  claude-hud)         claude plugin marketplace add jarrodwatts/claude-hud && claude plugin install claude-hud@claude-hud;;
  caveman)            claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman;;
  mattpocock-skills)  npx skills@latest add mattpocock/skills;;
  anthropic-skills)   claude plugin marketplace add anthropics/skills
                      echo "Then inside Claude Code: /plugin install example-skills@anthropic-agent-skills";;
  youtube-skills)     npx skills add ZeroPointRepo/youtube-skills;;
  composio-skills)    clone ComposioHQ/awesome-claude-skills awesome-claude-skills
                      echo "Next: claude --plugin-dir vendor/awesome-claude-skills/connect-apps-plugin";;
  # --- reference reading only ---
  learn-claude-code)  clone shareAI-lab/learn-claude-code learn-claude-code;;
  awesome-mcp)        clone punkpeye/awesome-mcp-servers awesome-mcp-servers;;
  # --- free coding option, only when Alfonso asks for a free run ---
  opencode)           echo "Only for a free run. Install it yourself after reading the script:"
                      echo "  curl -fsSL https://opencode.ai/install | bash"
                      echo "Then pick DeepSeek V4 Flash through OpenCode Zen inside opencode. It does not replace Claude Code.";;
  list|*)             grep -E '^  [a-z0-9-]+\)' "$0" | sed 's/).*//' | sed 's/^/ /'
                      echo; echo "Usage: bash scripts/install_extras.sh <name>   (details: docs/TOOLS.md)";;
esac
