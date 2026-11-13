#!/usr/bin/env bash
# One-time install for fonzi-gym-video-editor. Needs: ffmpeg, python3, node 18+.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (brew install ffmpeg / apt install ffmpeg)"; exit 1; }
python3 -m pip install -q -r requirements.txt
(cd remotion && npm install --no-audit --no-fund)
mkdir -p input output songs posted
echo "Setup done."
