#!/bin/sh
# Status line script based on Oh My Zsh robbyrussell theme
# Receives Claude Code session JSON via stdin

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
window_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')

# Worktree info (only shown when present)
worktree_name=$(echo "$input" | jq -r '.worktree.name // empty')
worktree_branch=$(echo "$input" | jq -r '.worktree.branch // empty')

# Rate limits
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
now=$(date +%s)

# ANSI colors
bold_green='\033[1;32m'
bold_yellow='\033[1;33m'
bold_red='\033[1;31m'
magenta='\033[0;35m'
dim='\033[2m'
reset='\033[0m'
# Model tier colors
color_haiku='\033[0;36m'       # cyan  — fast / lightweight
color_sonnet='\033[1;34m'      # bold blue — balanced
color_opus='\033[1;35m'        # bold magenta — premium
color_default='\033[38;5;161m' # crimson — unrecognized model

# Helper: pick color for model tier based on display name
model_color_for() {
  _lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$_lower" in
    *haiku*)  printf '%s' "$color_haiku" ;;
    *sonnet*) printf '%s' "$color_sonnet" ;;
    *opus*)   printf '%s' "$color_opus" ;;
    *)        printf '%s' "$color_default" ;;
  esac
}

# Helper: format context window size (e.g. 200000 → 200K, 1000000 → 1M)
format_window() {
  _n="$1"
  if [ "$_n" -ge 1000000 ]; then
    printf '%dM' "$(( _n / 1000000 ))"
  elif [ "$_n" -ge 1000 ]; then
    printf '%dK' "$(( _n / 1000 ))"
  else
    printf '%d' "$_n"
  fi
}

# Helper: format remaining seconds as compact largest-two-units countdown (e.g. 2h15m, 45m, 3d5h)
# Usage: format_countdown <remaining_seconds> — prints nothing if remaining <= 0
format_countdown() {
  _remaining="$1"
  [ "$_remaining" -le 0 ] && return 1
  _days=$(( _remaining / 86400 ))
  _hours=$(( (_remaining % 86400) / 3600 ))
  _mins=$(( (_remaining % 3600) / 60 ))
  if [ "$_days" -gt 0 ]; then
    printf '%dd%dh' "$_days" "$_hours"
  elif [ "$_hours" -gt 0 ]; then
    printf '%dh%dm' "$_hours" "$_mins"
  else
    printf '%dm' "$_mins"
  fi
}

# Helper: pick bold color based on percentage value
# Usage: color_for_pct <integer_pct>
color_for_pct() {
  _pct="$1"
  if [ "$_pct" -lt 50 ]; then
    printf '%s' "$bold_green"
  elif [ "$_pct" -le 80 ]; then
    printf '%s' "$bold_yellow"
  else
    printf '%s' "$bold_red"
  fi
}

# Dim separator
sep="${dim} · ${reset}"

# Arrow (always bold green)
arrow="${bold_green}➜ ${reset}"

# --- Segments ---

# Model segment
model_part=""
if [ -n "$model" ]; then
  mcolor=$(model_color_for "$model")
  win_label=""
  [ -n "$window_size" ] && win_label=" [$(format_window "$window_size")]"
  model_part="🤖 ${mcolor}${model}${reset}${win_label}"
fi

# Context segment
ctx_part=""
if [ -n "$used_pct" ]; then
  used_int=$(printf '%.0f' "$used_pct")
  ctx_color=$(color_for_pct "$used_int")
  ctx_part="🧠 ${ctx_color}${used_int}%%${reset}"
fi

# 5-hour rate limit segment
five_part=""
if [ -n "$five_pct" ]; then
  five_int=$(printf '%.0f' "$five_pct")
  five_color=$(color_for_pct "$five_int")
  five_part="⏳ ${five_color}${five_int}%%${reset}"
  if [ -n "$five_reset" ]; then
    five_reset_int=$(printf '%.0f' "$five_reset")
    five_countdown=$(format_countdown "$(( five_reset_int - now ))")
    [ -n "$five_countdown" ] && five_part="${five_part} ${dim}(${five_countdown})${reset}"
  fi
fi

# 7-day rate limit segment
week_part=""
if [ -n "$week_pct" ]; then
  week_int=$(printf '%.0f' "$week_pct")
  week_color=$(color_for_pct "$week_int")
  week_part="📅 ${week_color}${week_int}%%${reset}"
  if [ -n "$week_reset" ]; then
    week_reset_int=$(printf '%.0f' "$week_reset")
    week_countdown=$(format_countdown "$(( week_reset_int - now ))")
    [ -n "$week_countdown" ] && week_part="${week_part} ${dim}(${week_countdown})${reset}"
  fi
fi

# Worktree segment (only shown when active)
worktree_part=""
if [ -n "$worktree_name" ]; then
  wt_label="$worktree_name"
  [ -n "$worktree_branch" ] && wt_label="${worktree_name}:${worktree_branch}"
  worktree_part="🌿 ${magenta}${wt_label}${reset}"
fi

# --- Assemble line ---
line="$arrow"
first=1

append_seg() {
  _seg="$1"
  if [ -n "$_seg" ]; then
    if [ "$first" -eq 1 ]; then
      line="${line}${_seg}"
      first=0
    else
      line="${line}${sep}${_seg}"
    fi
  fi
}

append_seg "$model_part"
append_seg "$worktree_part"
append_seg "$ctx_part"
append_seg "$five_part"
append_seg "$week_part"

printf "${line}\n"
