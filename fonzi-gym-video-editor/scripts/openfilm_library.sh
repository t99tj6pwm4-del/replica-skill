#!/usr/bin/env bash
# OpenFilm media library ONLY (Alfonso, 2026-11-21): free CC0 sound effects + stickers from OpenFilm's library.
# No other OpenFilm feature is used: no paid/AI generation (`get sfx`, `get music`, voice, image, video), no
# stock footage search, no Studio, no keys. Library music is BLOCKED until Alfonso says yes to it (standing rule:
# only his own songs, no stock or AI music); set openfilm.allow_music: true in config.yaml only on his yes.
#
#   scripts/openfilm_library.sh sfx     "heavy plate drop"      # search sound effects
#   scripts/openfilm_library.sh sticker "fire"                  # search stickers
#   scripts/openfilm_library.sh music   "gym beat"              # search music (only if allowed)
#   scripts/openfilm_library.sh take    <id>                    # download one into sfx/library/ or brand/stickers/
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OF_DIR="${OPENFILM_DIR:-$HOME/tools/openfilm}"
OF_REV="a1b8d75"   # the version we tested (2026-11-21)
PROJ="$HERE/output/openfilm_project"

install() {
  if [ ! -f "$OF_DIR/packages/openfilm/bin/openfilm.mjs" ]; then
    mkdir -p "$(dirname "$OF_DIR")"
    git clone -q https://github.com/openfilm/openfilm "$OF_DIR"
    git -C "$OF_DIR" checkout -q "$OF_REV"
  fi
  if [ ! -d "$OF_DIR/node_modules" ]; then
    (cd "$OF_DIR" && corepack pnpm@9.15.9 install --frozen-lockfile >/dev/null)
  fi
  mkdir -p "$PROJ"
  [ -f "$PROJ/film.html" ] || echo '<!doctype html><film></film>' > "$PROJ/film.html"
}
of() { (cd "$PROJ" && node "$OF_DIR/packages/openfilm/bin/openfilm.mjs" "$@"); }
music_allowed() { grep -A3 '^openfilm:' "$HERE/config.yaml" | grep -q 'allow_music: true'; }

cmd="${1:-}"; shift || true
install
case "$cmd" in
  sfx)     of get sfx-search --prompt "$*" --limit 10 ;;
  sticker) of get sticker --prompt "$*" --limit 10 ;;
  music)   music_allowed || { echo "Library music is blocked: only Alfonso's own songs until he says yes." >&2; exit 3; }
           of get music-search --prompt "$*" --limit 10 ;;
  take)
    id="${1:?id}"
    case "$id" in openfilm/audio/music/*) music_allowed || { echo "Library music is blocked (his songs only)." >&2; exit 3; } ;; esac
    verb=sfx-search; case "$id" in openfilm/audio/music/*) verb=music-search;; openfilm/audio/*|openfilm/sounds/*|openfilm/community/*/sound/*) ;; *) verb=sticker;; esac
    of get "$verb" --take "$id"
    if [ "$verb" = sticker ]; then dest="$HERE/brand/stickers"; else dest="$HERE/sfx/library"; fi
    mkdir -p "$dest"
    find "$PROJ/assets" -maxdepth 2 -newer "$PROJ/film.html" -type f -exec cp -n {} "$dest/" \; 2>/dev/null || true
    touch "$PROJ/film.html"
    echo "Saved into $dest (CC0 / MIT, free to use, no credit needed)."
    ;;
  *) sed -n 2,11p "$0"; exit 2 ;;
esac
