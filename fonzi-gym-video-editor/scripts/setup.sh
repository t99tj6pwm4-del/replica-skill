#!/usr/bin/env bash
# One-time install for fonzi-gym-video-editor. Needs: ffmpeg, python3, node 18+, git.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (brew install ffmpeg / apt install ffmpeg)"; exit 1; }
python3 -m pip install -q -r requirements.txt
(cd remotion && npm install --no-audit --no-fund)
mkdir -p input output songs posted

# Multicam prompt-template skills used by the Multicam/B-Roll Agent
mkdir -p "$HOME/.claude/skills"
for skill in kinetic-multicam cine-multicam-capcut; do
  if [ ! -d "$HOME/.claude/skills/$skill" ]; then
    git clone -q "https://github.com/aipauloshimas/$skill" "$HOME/.claude/skills/$skill"
  fi
done
echo "Setup done. Optional add-ons: bash scripts/install_extras.sh"
