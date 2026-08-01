# tphduy-studio

Personal Claude Code plugin marketplace.

## Plugins

- `plugins/prompt-master/` — `prompt-master` skill (vendored via `git subtree` from [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master), MIT — see its own `LICENSE`/`README.md`). To pull upstream updates: `git subtree pull --prefix=plugins/prompt-master/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash`.
- `plugins/prove-it/` — `prove-it` skill (personal).
- `plugins/notify/` — a macOS notification hook (desktop/audio/speech) for Claude Code's `Notification` event. Requires `terminal-notifier` and `jq` — see [plugins/notify/README.md](plugins/notify/README.md).

## Third-party skills

`i-have-adhd`, `grilling`, and `writing-great-skills` used to be vendored into `dev-toolkit` — now install them directly from their own upstream marketplaces instead:

```bash
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock-skills
```

The `mattpocock/skills` marketplace ships one bundled plugin (`mattpocock-skills`) covering all of Matt Pocock's skills, including `grilling` and `writing-great-skills` — there's no way to install just one of those two separately through the marketplace.

## Setup on a new machine

1. Clone this repo:

```bash
git clone https://github.com/tphduy/tphduy-studio
cd tphduy-studio
```

2. Inside a Claude Code session, add the marketplace and install the plugins:

```bash
/plugin marketplace add tphduy/tphduy-studio
/plugin install prompt-master@tphduy-studio
/plugin install prove-it@tphduy-studio
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
