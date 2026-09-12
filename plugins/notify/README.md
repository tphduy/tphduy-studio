# notify

macOS notification hook for Claude Code's `Notification` event — desktop notification (`terminal-notifier`), audio chime (`afplay`), and spoken announcement (`say`).

## Requirements

- macOS (`afplay`, `say`, `ps` are built in)
- [`terminal-notifier`](https://github.com/julienxx/terminal-notifier) — `brew install terminal-notifier`
- `jq` — `brew install jq`

## Behavior

Distinguishes permission-prompt, idle/finished, auth-success, and elicitation notifications with different sounds and spoken phrasing. Notifications from the same session replace each other instead of stacking.

## License

MIT — see the repo root [LICENSE](../../LICENSE).
