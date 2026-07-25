# tphduy-studio

Personal Claude Code plugin marketplace.

## Plugins

- `plugins/dev-toolkit/` — skills: `grill-me` (a twist on [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)'s `grilling` skill), `prove-it` (personal), `prompt-master` (vendored via `git subtree` from [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master), MIT — see its own `LICENSE`/`README.md`). To pull upstream updates: `git subtree pull --prefix=plugins/dev-toolkit/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash`.
- `plugins/notify/` — a macOS notification hook (desktop/audio/speech) for Claude Code's `Notification` event. Requires `terminal-notifier` and `jq` — see [plugins/notify/README.md](plugins/notify/README.md).

## Setup on a new machine

1. Clone this repo:

```bash
git clone https://github.com/tphduy/tphduy-studio
cd tphduy-studio
```

2. Inside a Claude Code session, add the marketplace and install both plugins:

```bash
/plugin marketplace add tphduy/tphduy-studio
/plugin install dev-toolkit@tphduy-studio
/plugin install notify@tphduy-studio
```

For local iteration before pushing, add the marketplace by absolute path instead: `/plugin marketplace add /path/to/tphduy-studio`.

3. Copy `rules/*.md` into `~/.claude/rules` — Claude Code's plugin manifest has no `rules` component, so plugin install alone won't pick those up. This only touches the files named here, so any machine-local rule files already in `~/.claude/rules` stay put. Re-run after `git pull` to pick up rule changes (this overwrites same-named files in `~/.claude/rules`):

```bash
mkdir -p ~/.claude/rules
cp rules/*.md ~/.claude/rules/
```

4. Copy `statusline/statusline-command.sh` into `~/.claude/`, then merge this block into `~/.claude/settings.json` (don't overwrite your existing keys). Requires `jq` — `brew install jq`:

```bash
cp statusline/statusline-command.sh ~/.claude/statusline-command.sh
```

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh"
}
```

## License

MIT — see [LICENSE](LICENSE).
