# tphduy-studio

Duy Tran's personal setup for Claude Code and Codex CLI: a Claude Code plugin marketplace, a Codex plugin marketplace, shared global rules, a status line, and a tracked list of external skill/plugin sources to install from other marketplaces.

## Plugins

Plugins live under `plugins/`. Each one ships a Claude Code manifest (`.claude-plugin/plugin.json`); a plugin also ships a Codex manifest (root `plugin.json`) once it's been ported to Codex's plugin system.

- `plugins/prompt-master/` — `prompt-master` skill (vendored via `git subtree` from [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master), MIT — see its own `LICENSE`/`README.md`). To pull upstream updates: `git subtree pull --prefix=plugins/prompt-master/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash`. Available on both Claude Code and Codex.
- `plugins/notify/` — a macOS notification hook (desktop/audio/speech) for Claude Code's `Notification` event. Requires `terminal-notifier` and `jq` — see [plugins/notify/README.md](plugins/notify/README.md). Claude Code only for now — Codex's lifecycle-hook shape hasn't been ported yet.

## Third-party skills

Install these directly from their own upstream marketplaces rather than vendoring them here.

`i-have-adhd`, `grilling`, and `writing-great-skills` used to be vendored into `dev-toolkit` — now install them directly:

```bash
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock-skills
```

The `mattpocock/skills` marketplace ships one bundled plugin (`mattpocock-skills`) covering all of Matt Pocock's skills, including `grilling` and `writing-great-skills` — there's no way to install just one of those two separately through the marketplace.

[SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) (ASD-STE100 Simplified Technical English enforcement) ships as a dual-native plugin for both Claude Code and Codex:

```bash
claude plugin marketplace add AminBlg/SimpleEnglish
claude plugin install simple-english@simple-english
```

```bash
codex plugin marketplace add AminBlg/SimpleEnglish
codex plugin add simple-english@simple-english
```

[ecc](https://github.com/affaan-m/ecc) is a large agent-harness toolkit (68 agents, 292 skills, 94 commands) — install the whole plugin, there's no curated subset tracked here yet:

```bash
claude plugin marketplace add affaan-m/ecc
claude plugin install ecc@ecc
```

```bash
npx ecc-universal@latest setup
```

The `ecc-universal` setup script is ecc's own cross-harness installer and covers Codex and other agent CLIs — use it instead of a `codex plugin` command for ecc.

## Setup on a new machine

1. Clone this repo:

```bash
git clone https://github.com/tphduy/tphduy-studio
cd tphduy-studio
```

2. **Claude Code** — add the marketplace and install the plugins:

```bash
/plugin marketplace add tphduy/tphduy-studio
/plugin install prompt-master@tphduy-studio
/plugin install notify@tphduy-studio
```

For local iteration before pushing, add the marketplace by absolute path instead: `/plugin marketplace add /path/to/tphduy-studio`.

3. **Codex** — add the marketplace and install the plugins that have Codex support:

```bash
codex plugin marketplace add tphduy/tphduy-studio
codex plugin add prompt-master@tphduy-studio
```

For local iteration before pushing, add the marketplace by local path instead: `codex plugin marketplace add ./path/to/tphduy-studio`. Verify the exact subcommand names against your installed Codex CLI's own `--help` — this plugin system is new and command names can move.

4. Copy `rules/*.md` into `~/.claude/rules` — Claude Code's plugin manifest has no `rules` component, so plugin install alone won't pick those up. This only touches the files named here, so any machine-local rule files already in `~/.claude/rules` stay put. Re-run after `git pull` to pick up rule changes (this overwrites same-named files in `~/.claude/rules`). Rules are Claude Code-only: Codex has no per-path rule injection, only a repo-wide `AGENTS.md`.

```bash
mkdir -p ~/.claude/rules
cp rules/*.md ~/.claude/rules/
```

5. Copy `status-line/statusline-command.sh` into `~/.claude/`, then merge this block into `~/.claude/settings.json` (don't overwrite your existing keys). Requires `jq` — `brew install jq`:

```bash
cp status-line/statusline-command.sh ~/.claude/statusline-command.sh
```

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh"
}
```

## License

MIT — see [LICENSE](LICENSE).
