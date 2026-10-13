# tphduy-studio

Duy Tran's personal plugin workshop for Codex and Claude Code. Plugin content is shared where compatible; each platform has its own catalog and manifests. Plugins may support one platform or both.

| Plugin | Codex | Claude Code |
| --- | --- | --- |
| json-design | Yes | Yes |
| writing-for-human | Yes | Yes |
| prompt-master | Yes | Yes |

## Local setup

Requires Git, Python 3.10+, Codex CLI, and Claude Code CLI, with existing account authentication. Runtime verification uses normal account usage. No remote repository is configured.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/verify.py
.venv/bin/python -m unittest discover -s tests
```

The verifier checks repository conventions and runs Claude's strict native validator. It does not perform model calls or full schema validation for every future component. Exit codes: `0` pass, `1` failed, `2` inconclusive. `--json` emits a machine-readable report; `--skip-native` explicitly reports native validation as inconclusive.

## Maintenance sessions

Start `codex` or `claude` from the repository root. [AGENTS.md](AGENTS.md) owns shared maintenance instructions; Claude imports it through `CLAUDE.md`. Trust the checkout when prompted so project configuration can load. Codex's project configuration disables the personal writing plugin during maintenance; it remains available in other projects after installation.

Claude's project settings enable upstream `plugin-dev` from `claude-plugins-official`. Trust this checkout when prompted. If it is not installed for this project:

```sh
claude plugin install plugin-dev@claude-plugins-official --scope project
```

Use `/plugin-dev:create-plugin` for guided Claude authoring. Codex uses the installed Plugin Creator's `create-plugin` and `update-plugin` skills; inspect the current skill picker for their exact invocation names. Its separate submission skill is relevant only when preparing a public OpenAI directory submission.

The installed Plugin Creator is distinct from the older bundled `$plugin-creator` scaffolder. If using that scaffolder, adapt its compatibility output to portable root manifests. Authoring tools are dependencies, not entries in this marketplace. Personal plugins are loaded explicitly for testing.

## Install personal plugins

Check configured marketplace roots before registering this checkout: marketplace names identify sources. If `tphduy-studio` already points to another checkout, use the isolated verification procedure first. Registering a replacement source can affect existing installations.

Codex:

```sh
codex plugin marketplace list --json
codex plugin marketplace add "$PWD"
codex plugin list --marketplace tphduy-studio --available --json
codex plugin add writing-for-human@tphduy-studio --json
```

Claude Code:

```sh
claude plugin marketplace list --json
claude plugin marketplace add "$PWD" --scope local
claude plugin install writing-for-human@tphduy-studio --scope local
```

Start a fresh session and explicitly invoke the installed skill: `$writing-for-human:writing-for-human` in Codex or `/writing-for-human:writing-for-human` in Claude. This authoring repository disables the personal plugin in its Codex project configuration; activate it for a verification session with:

```sh
codex -c 'plugins."writing-for-human@tphduy-studio".enabled=true'
```

## Enable the status line

`statusline/statusline-command.sh` is a standalone Claude Code status line, not a plugin. It shows the model, session cost, worktree, uncommitted git changes, and context and rate-limit usage. Claude Code runs it only when `statusLine` in `settings.json` names it; installing a plugin from this marketplace does not enable it. Requires `jq`, `git`, and `awk`.

Option A: clone the repository and point `settings.json` at the script. `<repository-url>` is a placeholder because no remote is configured yet; clone from your local checkout until one exists.

```sh
git clone <repository-url> ~/src/tphduy-studio
```

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/src/tphduy-studio/statusline/statusline-command.sh"
  }
}
```

Option B: copy the script and point `settings.json` at the copy.

```sh
cp statusline/statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-command.sh"
  }
}
```

Put the `statusLine` key in user settings, `~/.claude/settings.json`, and merge it with the keys already there. Project `.claude/settings.json` also works but would commit a machine-specific path. `~` expands in `command`; `$PWD` and `$HOME` do not. If the path contains spaces, quote it inside the string.

Check the script without Claude Code, then start a new session:

```sh
echo '{"model":{"display_name":"Sonnet"},"cost":{"total_cost_usd":0.42}}' | ~/.claude/statusline-command.sh
```

The status line stays blank until the workspace trust dialog is accepted for the folder. Theme detection follows `STATUSLINE_THEME` (`light` or `dark`), then Claude's `theme` setting, macOS appearance, and `COLORFGBG`; set the variable to override it.

Option A updates with `git pull`; Option B needs a fresh copy. To remove the status line, delete the `statusLine` key and, for Option B, the copied file.

## Updates and removal

For a Git-backed Codex marketplace, refresh it with `codex plugin marketplace upgrade tphduy-studio`. For local sources, reinstall with `codex plugin remove writing-for-human@tphduy-studio` followed by `codex plugin add writing-for-human@tphduy-studio`, then start a new session. Codex caches installed files; edit source files, not caches.

For Claude, refresh a Git-backed source with `claude plugin marketplace update tphduy-studio`, then run `claude plugin update writing-for-human@tphduy-studio --scope local`. Local directory sources may load edits directly; start a new session or use `/reload-plugins`.

Uninstall with `codex plugin remove writing-for-human@tphduy-studio` or `claude plugin uninstall writing-for-human@tphduy-studio --scope local`. Use the same Claude scope used at installation. Removing catalog entries alone leaves installed copies until explicit uninstall.

Before retiring an existing skill, verify the replacement and keep backups outside discovery roots. This repository becomes the source of truth for packaged content.

## Platform references

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Claude marketplace authoring](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude project instruction imports](https://code.claude.com/docs/en/memory)
- [Upstream plugin-dev](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev)

MIT licensed. Public GitHub publication is a separate step.
