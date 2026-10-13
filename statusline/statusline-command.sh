#!/bin/sh
# Claude Code status line, styled after the Oh My Zsh robbyrussell theme.
# Reads the session JSON on stdin and prints a single ANSI-colored line.
#
# Sections (one concern each):
#   1. Constants
#   2. Input       - JSON field access
#   3. Theme       - theme detection and color palette
#   4. Formatting  - pure value -> text / color helpers
#   5. Git         - repository data, no styling
#   6. Segments    - one renderer per status line segment
#   7. Assembly    - joining segments into the final line
#   8. Main

# --- 1. Constants -----------------------------------------------------------

ESC=$(printf '\033')
SETTINGS_FILE="$HOME/.claude/settings.json"

PCT_WARN=50 # at or above: yellow
PCT_CRIT=80 # above: red

# --- 2. Input ---------------------------------------------------------------

INPUT=""

# Usage: json_get <jq-expression> [default]
# Prints the value selected from the session JSON, or [default] when absent.
json_get() {
    _value=$(printf '%s' "$INPUT" | jq -r "$1 // empty")
    printf '%s' "${_value:-$2}"
}

# --- 3. Theme ---------------------------------------------------------------

# Each theme_from_* prints "light" or "dark", or nothing when it cannot decide.

theme_from_env() {
    case "$STATUSLINE_THEME" in
        light|dark) printf '%s' "$STATUSLINE_THEME" ;;
    esac
}

theme_from_claude_settings() {
    [ -r "$SETTINGS_FILE" ] || return 0
    case "$(jq -r '.theme // empty' "$SETTINGS_FILE" 2>/dev/null)" in
        light*) printf 'light' ;;
        dark*)  printf 'dark' ;;
    esac
}

# macOS: /usr/bin/defaults only exists there (avoids spawning uname).
# AppleInterfaceStyle is "Dark" in dark mode and unset (read fails) in light mode.
theme_from_macos() {
    [ -x /usr/bin/defaults ] || return 0
    if [ "$(/usr/bin/defaults read -g AppleInterfaceStyle 2>/dev/null)" = "Dark" ]; then
        printf 'dark'
    else
        printf 'light'
    fi
}

# Other terminals: COLORFGBG is "fg;bg" (or "fg;default;bg"); bg 7/15 = light.
theme_from_colorfgbg() {
    case "${COLORFGBG##*;}" in
        7|15) printf 'light' ;;
    esac
}

# Order: STATUSLINE_THEME env, Claude Code "theme" setting, macOS appearance,
# COLORFGBG, then default dark.
detect_theme() {
    for _source in theme_from_env theme_from_claude_settings \
                   theme_from_macos theme_from_colorfgbg; do
        _theme=$($_source)
        if [ -n "$_theme" ]; then
            printf '%s' "$_theme"
            return 0
        fi
    done
    printf 'dark'
}

# Usage: load_palette <light|dark>
# Sets the color variables used by the formatting and segment sections.
load_palette() {
    reset="${ESC}[0m"
    if [ "$1" = "light" ]; then
        # Light terminal background: darker 256-color equivalents
        bold_green="${ESC}[1;38;5;28m"
        bold_yellow="${ESC}[1;38;5;130m" # amber
        bold_red="${ESC}[1;38;5;160m"
        magenta="${ESC}[38;5;90m"
        dim="${ESC}[38;5;240m" # dark gray, readable on white
        # Model tier colors
        color_haiku="${ESC}[38;5;30m"     # teal    - fast / lightweight
        color_sonnet="${ESC}[1;38;5;25m"  # blue    - balanced
        color_opus="${ESC}[1;38;5;90m"    # magenta - premium
        color_default="${ESC}[38;5;125m"  # crimson - unrecognized model
        color_cost="${ESC}[38;5;136m"     # gold    - session cost
    else
        # Dark terminal background
        bold_green="${ESC}[1;32m"
        bold_yellow="${ESC}[1;33m"
        bold_red="${ESC}[1;31m"
        magenta="${ESC}[0;35m"
        dim="${ESC}[2m"
        # Model tier colors
        color_haiku="${ESC}[0;36m"        # cyan    - fast / lightweight
        color_sonnet="${ESC}[1;34m"       # blue    - balanced
        color_opus="${ESC}[1;35m"         # magenta - premium
        color_default="${ESC}[38;5;161m"  # crimson - unrecognized model
        color_cost="${ESC}[38;5;220m"     # gold    - session cost
    fi
}

# --- 4. Formatting ----------------------------------------------------------

# Usage: format_window <tokens>   (200000 -> 200K, 1000000 -> 1M)
format_window() {
    if [ "$1" -ge 1000000 ]; then
        printf '%dM' "$(( $1 / 1000000 ))"
    elif [ "$1" -ge 1000 ]; then
        printf '%dK' "$(( $1 / 1000 ))"
    else
        printf '%d' "$1"
    fi
}

# Usage: model_color_for <display-name>   (color by model tier)
model_color_for() {
    _lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
    case "$_lower" in
        *haiku*)  printf '%s' "$color_haiku" ;;
        *sonnet*) printf '%s' "$color_sonnet" ;;
        *opus*)   printf '%s' "$color_opus" ;;
        *)        printf '%s' "$color_default" ;;
    esac
}

# Usage: color_for_pct <integer-percent>   (green / yellow / red)
color_for_pct() {
    if [ "$1" -lt "$PCT_WARN" ]; then
        printf '%s' "$bold_green"
    elif [ "$1" -le "$PCT_CRIT" ]; then
        printf '%s' "$bold_yellow"
    else
        printf '%s' "$bold_red"
    fi
}

# --- 5. Git -----------------------------------------------------------------

# Usage: git_in <dir> <git-args...>   (never takes optional locks)
git_in() {
    _git_dir="$1"
    shift
    git -C "$_git_dir" --no-optional-locks "$@"
}

# Usage: git_is_repo <dir>
git_is_repo() {
    git_in "$1" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Usage: git_branch <dir>   (branch name, or short SHA when detached)
git_branch() {
    _branch=$(git_in "$1" symbolic-ref --short -q HEAD 2>/dev/null)
    [ -n "$_branch" ] || _branch=$(git_in "$1" rev-parse --short HEAD 2>/dev/null)
    printf '%s' "$_branch"
}

# Usage: git_diff_base <dir>   (HEAD, or the empty tree before the first commit)
git_diff_base() {
    if git_in "$1" rev-parse -q --verify HEAD >/dev/null 2>&1; then
        printf 'HEAD'
    else
        git_in "$1" hash-object -t tree /dev/null
    fi
}

# Usage: git_change_summary <dir>
# Prints "<files> <added> <removed>" for uncommitted changes (staged and
# unstaged together, plus untracked files in the file count).
git_change_summary() {
    _base=$(git_diff_base "$1")
    _numstat=$(git_in "$1" diff --numstat "$_base" 2>/dev/null)
    _untracked=$(git_in "$1" ls-files --others --exclude-standard 2>/dev/null \
        | awk 'END {print NR+0}')
    printf '%s\n' "$_numstat" | awk -v untracked="$_untracked" '
        NF                { files++ }
        $1 ~ /^[0-9]+$/   { added += $1 }
        $2 ~ /^[0-9]+$/   { removed += $2 }
        END { printf "%d %d %d\n", files + untracked, added, removed }'
}

# --- 6. Segments ------------------------------------------------------------
# Each render_* prints one segment, or nothing when it has nothing to show.

# Usage: render_model <display-name> <window-size>
render_model() {
    [ -n "$1" ] || return 0
    printf '🤖 %s%s%s' "$(model_color_for "$1")" "$1" "$reset"
    [ -z "$2" ] || printf ' %s[%s]%s' "$dim" "$(format_window "$2")" "$reset"
}

# Usage: render_cost <usd>
render_cost() {
    printf '💰 %s$%.2f%s' "$color_cost" "$1" "$reset"
}

# Usage: render_worktree <name> <branch>   (only when a worktree is active)
render_worktree() {
    [ -n "$1" ] || return 0
    _label="$1"
    [ -z "$2" ] || _label="$1:$2"
    printf '🌿 %s%s%s' "$magenta" "$_label" "$reset"
}

# Usage: render_changes <files> <added> <removed>   (nothing when clean)
render_changes() {
    [ "$1" -gt 0 ] || return 0
    _noun=files
    [ "$1" -ne 1 ] || _noun=file
    printf ' %s%s %s%s' "$dim" "$1" "$_noun" "$reset"
    [ "$2" -le 0 ] || printf ' %s+%s%s' "$bold_green" "$2" "$reset"
    [ "$3" -le 0 ] || printf ' %s-%s%s' "$bold_red" "$3" "$reset"
}

# Usage: render_git <dir>   (nothing outside a git work tree)
render_git() {
    [ -n "$1" ] && git_is_repo "$1" || return 0
    _branch_name=$(git_branch "$1")
    set -- "$1" $(git_change_summary "$1")
    printf '🔀 %s%s%s%s' "$magenta" "$_branch_name" "$reset" \
        "$(render_changes "$2" "$3" "$4")"
}

# Usage: render_pct_segment <icon> <percent>   (context / rate-limit usage)
render_pct_segment() {
    _pct=$(printf '%.0f' "$2")
    printf '%s %s%s%%%s' "$1" "$(color_for_pct "$_pct")" "$_pct" "$reset"
}

# --- 7. Assembly ------------------------------------------------------------

# Usage: join_segments <segment...>   (skips empty segments, dim separator)
join_segments() {
    _sep="${dim} · ${reset}"
    _joined=""
    for _segment in "$@"; do
        [ -n "$_segment" ] || continue
        if [ -z "$_joined" ]; then
            _joined="$_segment"
        else
            _joined="${_joined}${_sep}${_segment}"
        fi
    done
    printf '%s' "$_joined"
}

# --- 8. Main ----------------------------------------------------------------

main() {
    INPUT=$(cat)
    load_palette "$(detect_theme)"

    cwd=$(json_get '.workspace.current_dir // .cwd')
    model=$(json_get '.model.display_name')
    window_size=$(json_get '.context_window.context_window_size')
    worktree_name=$(json_get '.worktree.name')
    worktree_branch=$(json_get '.worktree.branch')

    # Numeric values default to 0 so their segments always show.
    cost_usd=$(json_get '.cost.total_cost_usd' 0)
    used_pct=$(json_get '.context_window.used_percentage' 0)
    five_pct=$(json_get '.rate_limits.five_hour.used_percentage' 0)
    week_pct=$(json_get '.rate_limits.seven_day.used_percentage' 0)

    arrow="${bold_green}➜ ${reset}"
    segments=$(join_segments \
        "$(render_model "$model" "$window_size")" \
        "$(render_cost "$cost_usd")" \
        "$(render_worktree "$worktree_name" "$worktree_branch")" \
        "$(render_git "$cwd")" \
        "$(render_pct_segment 🧠 "$used_pct")" \
        "$(render_pct_segment ⏳ "$five_pct")" \
        "$(render_pct_segment 📅 "$week_pct")")

    printf '%s%s\n' "$arrow" "$segments"
}

main
