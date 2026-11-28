#!/usr/bin/env bash
# HyperFrames (HeyGen, Apache-2.0) for intro / title / pop-up motion graphics (Alfonso, 2026-11-21).
# Installs the CLI into ~/tools/hf-cli if missing, pins the tested version, turns telemetry OFF.
# Use:  source scripts/hyperframes_setup.sh   then   hf <command>   (rules: docs/hyperframes.md)
HF_DIR="${HF_DIR:-$HOME/tools/hf-cli}"
HF_VER="0.9.78"   # tested 2026-11-21
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
if [ ! -x "$HF_DIR/node_modules/.bin/hyperframes" ]; then
  mkdir -p "$HF_DIR" && (cd "$HF_DIR" && { [ -f package.json ] || npm init -y >/dev/null; } && npm i -s "hyperframes@$HF_VER" >/dev/null)
fi
"$HF_DIR/node_modules/.bin/hyperframes" telemetry disable >/dev/null 2>&1 || true
hf() {
  case "${1:-}" in
    share|publish|cloud|lambda|cloudrun|templates|billing|reverse|capture|tts)
      echo "hyperframes $1 is not allowed (docs/hyperframes.md)." >&2; return 3 ;;
  esac
  "$HF_DIR/node_modules/.bin/hyperframes" "$@"
}
