#!/usr/bin/env bash
# Handover hook: after an auto-compact, have Claude write HANDOVER.md;
# on a fresh session, load HANDOVER.md before anything else.
mode="$1"
input="$(cat)"
dir="${CLAUDE_PROJECT_DIR:-$PWD}"
marker="${TMPDIR:-/tmp}/claude-handover-pending-$(printf '%s' "$dir" | cksum | cut -d' ' -f1)"

case "$mode" in
  precompact)   # registered for auto-compact only
    touch "$marker"
    ;;
  sessionstart)
    source="$(printf '%s' "$input" | jq -r '.source // ""' 2>/dev/null)"
    if [ "$source" = "compact" ]; then
      [ -f "$marker" ] || exit 0
      rm -f "$marker"
      cat <<'MSG'
The conversation was just auto-compacted. Before doing anything else, write (overwrite) HANDOVER.md in the project root with exactly these sections:
## Done
## Left to do
## Next step
## Key files
## Key decisions
Then stop and tell the user: "HANDOVER.md written - run /clear (or start a new session) to continue from it with a clean context." Do not continue the task in this session.
MSG
    elif [ "$source" = "startup" ] || [ "$source" = "clear" ]; then
      [ -f "$dir/HANDOVER.md" ] || exit 0
      echo "HANDOVER.md from the previous session follows. Treat it as your starting context and read it before doing anything else:"
      echo
      cat "$dir/HANDOVER.md"
    fi
    ;;
esac
exit 0
