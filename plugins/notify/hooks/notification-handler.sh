#!/usr/bin/env bash
# Claude Code — Notification hook
#
# Triggered by Claude Code's "Notification" event. Receives a JSON payload on
# stdin and fires a macOS desktop notification via terminal-notifier, an audio
# chime via afplay, and a spoken announcement via say.
#
# JSON input schema (from Claude Code):
#   session_id      — unique identifier for the Claude session
#   transcript_path — absolute path to the session transcript file
#   message         — notification body text
#   title           — optional notification title (defaults to "Claude Code")

# ---------------------------------------------------------------------------
# 1. Read and parse the JSON payload from stdin
# ---------------------------------------------------------------------------
payload=$(cat)

# Extract all fields in a single jq call; read line-by-line into indexed array
# (bash 3.2-compatible — readarray requires bash 4+).
_i=0; _fields=()
while IFS= read -r _line; do
  _fields[$_i]="$_line"
  _i=$(( _i + 1 ))
done < <(
  printf '%s' "$payload" | jq -r '
    (.message // "Needs attention"),
    (.title // ""),
    (.session_id // ""),
    (.transcript_path // ""),
    (.payload.notification_type // "")
  ' 2>/dev/null
)
msg="${_fields[0]:-Needs attention}"
hook_title="${_fields[1]:-}"
session_id="${_fields[2]:-}"
transcript="${_fields[3]:-}"
ntype="${_fields[4]:-}"
unset _i _line _fields

# ---------------------------------------------------------------------------
# 2. Derive a human-readable project name from the transcript path
#
# Claude Code stores transcripts at ~/.claude/projects/<encoded-path>/<id>.md
# The encoded path uses hyphens as separators, so the last segment is the
# project directory name.
# ---------------------------------------------------------------------------
project=$(basename "$(dirname "$transcript")" | sed 's/.*-//')

# Build the notification title: "Claude Code" or "Claude Code · <project>"
title="Claude Code${project:+ · $project}"
subtitle="$hook_title"

# Sanitise values for terminal-notifier: replace double-quotes with single
# quotes to avoid breaking the argument string.
safe_msg="${msg//\"/\'}"
safe_title="${title//\"/\'}"
safe_subtitle="${subtitle//\"/\'}"

# ---------------------------------------------------------------------------
# 3. Detect the parent editor so terminal-notifier can focus the right window
#
# Hooks run as child processes several layers below the editor. Walking up the
# process tree up to 20 levels finds the nearest Zed or VS Code ancestor and
# captures its bundle ID for the -activate flag.
# ---------------------------------------------------------------------------
sender_bundle=""
pid=$PPID
for _ in $(seq 1 10); do
  [ -z "$pid" ] || [ "$pid" = "1" ] && break
  pname=$(ps -o comm= -p "$pid" 2>/dev/null)
  case "$pname" in
    *iTerm2*) sender_bundle="com.googlecode.iterm2"; break ;;
    *zed*)    sender_bundle="dev.zed.Zed";           break ;;
    *Code*)   sender_bundle="com.microsoft.VSCode";  break ;;
  esac
  pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
done

# ---------------------------------------------------------------------------
# 3b. Map the notification type to a spoken phrase and a chime so the audio
# cue distinguishes "needs your input" from "finished". The Notification hook
# fires for several situations; payload.notification_type tells them apart.
# Unknown/future types fall back to the original Glass + generic phrasing.
# ---------------------------------------------------------------------------
case "$ntype" in
  permission_prompt) speech="needs approval"; sound="/System/Library/Sounds/Funk.aiff" ;;
  idle_prompt)       speech="finished";       sound="/System/Library/Sounds/Glass.aiff" ;;
  auth_success)      speech="authenticated";  sound="/System/Library/Sounds/Glass.aiff" ;;
  elicitation_dialog|elicitation_complete|elicitation_response)
                     speech="needs attention"; sound="/System/Library/Sounds/Submarine.aiff" ;;
  *)                 speech="needs attention"; sound="/System/Library/Sounds/Glass.aiff" ;;
esac

# ---------------------------------------------------------------------------
# 4. Fire the notification, sound, and voice announcement in parallel
#
# terminal-notifier flags used:
#   -group $session_id  — replaces any prior notification from this session
#                         instead of stacking, so only the latest is shown
#   -ignoreDnD          — bypasses macOS Do Not Disturb / Focus modes
#   -timeout 30         — auto-dismiss after 30 seconds
#   -activate           — bring the originating editor to the foreground on click
# ---------------------------------------------------------------------------
terminal-notifier \
  -message "$safe_msg" \
  -title "$safe_title" \
  ${safe_subtitle:+-subtitle "$safe_subtitle"} \
  -timeout 30 \
  -ignoreDnD \
  ${sender_bundle:+-activate "$sender_bundle"} \
  ${session_id:+-group "$session_id"}

# Play audio chime and speak the announcement concurrently; both run in the
# background so this script exits immediately without blocking Claude Code.
say "${project:+$project, }Claude Code $speech" &
afplay "$sound" &
