# Local verification

Run the structural verifier and its tests using the README setup commands. Runtime checks are separate and use normal account usage. Save local evidence under ignored `reports/`, with CLI versions, source root, plugin version, commands, outcomes, and output excerpts.

Use `pass`, `failed`, or `inconclusive`. Missing authentication, unavailable tooling, or an uncompleted run is inconclusive. An observed wrong result is failed. A structurally valid package is not a runtime pass.

## Instructions and authoring tools

Start each CLI from this repository. Ask it to name the maintenance instruction file, the manifest convention, and the required verifier. Expect `AGENTS.md`, portable Codex plus Claude manifests, and `scripts/verify.py`.

In Claude, inspect `/memory` and `/plugin`: shared instructions should be imported and `plugin-dev@claude-plugins-official` enabled for this project. In Codex, confirm Plugin Creator's `create-plugin` and `update-plugin` appear in the skill picker. Record unavailable skills as inconclusive; the repository can still be maintained directly using its instructions.

## Isolated marketplace lifecycle

Use an isolated source copy and state directories to avoid replacing another checkout registered as `tphduy-studio`. These commands do not copy account credentials and do not require model calls. Run them in a subshell so exported variables do not affect later sessions:

```sh
(
  studio_root="$PWD"
  studio_test_root="$(mktemp -d "${TMPDIR:-/tmp}/tphduy-studio-check.XXXXXX")"
  mkdir -p "$studio_test_root/source" "$studio_test_root/codex" "$studio_test_root/claude"
  cp -R .agents .claude-plugin plugins AGENTS.md CLAUDE.md "$studio_test_root/source/"
  export CODEX_HOME="$studio_test_root/codex"
  export CLAUDE_CONFIG_DIR="$studio_test_root/claude"
  cd "$studio_test_root/source"
  git init --initial-branch=main

  codex plugin marketplace add "$PWD"
  codex plugin list --marketplace tphduy-studio --available --json
  codex plugin add writing-for-human@tphduy-studio --json
  codex plugin list --marketplace tphduy-studio --json

  claude plugin marketplace add "$PWD" --scope user
  claude plugin install writing-for-human@tphduy-studio --scope user
  claude plugin list --json
  claude plugin details writing-for-human@tphduy-studio

  # Change only the disposable source to exercise an update.
  "$studio_root/.venv/bin/python" - <<'PY'
import json
from pathlib import Path
for path in (Path('plugins/writing-for-human/plugin.json'),
             Path('plugins/writing-for-human/.claude-plugin/plugin.json')):
    data = json.loads(path.read_text())
    data['version'] = '0.1.1'
    path.write_text(json.dumps(data, indent=2) + '\n')
PY
  codex plugin remove writing-for-human@tphduy-studio --json
  codex plugin add writing-for-human@tphduy-studio --json
  codex plugin list --marketplace tphduy-studio --json
  claude plugin update writing-for-human@tphduy-studio --scope user --json
  claude plugin list --json

  codex plugin remove writing-for-human@tphduy-studio --json
  claude plugin uninstall writing-for-human@tphduy-studio --scope user --json
  codex plugin list --marketplace tphduy-studio --json
  claude plugin list --json
  printf 'Disposable evidence directory: %s\n' "$studio_test_root"
)
```

Inspect every result before continuing. Confirm initial version `0.1.0`, updated version `0.1.1`, and disappearance from installed inventories after uninstall. Available catalog entries can remain after uninstall. Stop and record a failed or inconclusive step rather than treating the last command's success as success for the whole sequence. The disposable copy leaves repository versions unchanged.

## Writing behavior

For Codex, install the source plugin using README commands after confirming the marketplace name is free, then use the documented session override to enable it in this authoring repository. For Claude, test without changing an existing marketplace registration:

```sh
claude --plugin-dir ./plugins/writing-for-human
```

Start fresh sessions. Explicitly invoke the packaged skill: `/writing-for-human:writing-for-human` in Claude or `$writing-for-human:writing-for-human` in Codex. Confirm the surfaced identifier if the host changes its naming convention. Use the packaged skill rather than a same-named standalone skill.

Use this scenario on both platforms:

> Use the packaged writing-for-human skill to rewrite this update for engineers in two sentences. Facts: our team reduced CI time from 12 minutes to 8 minutes; I designed the cache-key change; two teammates implemented the rollout. Keep the ownership boundaries and invent no facts. Return one finished draft.

Accept two sentences preserving 12 → 8 minutes, the user's design work, and teammates' rollout work. Reject invented measurements, sole personal credit, or multiple alternative drafts.

Then request a version with light self-aware wit, asking the agent to consult the bundled joke guidance first. Confirm the reference was read from the packaged skill, facts remain intact, and the output is one finished draft. Judge observable behavior rather than matching exact prose.

## Standalone-skill migration

After successful package verification, move `~/.codex/skills/writing-for-human` into a timestamped backup below `~/Documents/skill-backups/`, outside skill discovery roots. Preserve both files. Use the repository for future edits and install packaged copies for consumption.

Confirm Codex still discovers and invokes the packaged skill after the move. If that fails, restore the standalone directory from the backup and mark migration failed or inconclusive. Do not migrate when runtime verification remains inconclusive.

## Future components

For MCP additions, verify startup, discovery, authentication as applicable, and a harmless tool call on every supported platform. For hooks, verify supported events, required trust, execution, and observable outcomes. For Claude agents or other platform-specific components, verify native discovery and invocation. Add these scenarios with the component rather than assuming cross-platform portability.
