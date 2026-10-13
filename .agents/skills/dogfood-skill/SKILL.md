---
name: dogfood-skill
description: Run a plugin's skill headless against a target project, then review the trial run for improvements to the skill.
argument-hint: "plugin=<dir> target=<dir> [skill=<name>] [model=sonnet] [effort=medium] [context=<text>] [timeout=60m]"
disable-model-invocation: true
---

# Dogfood skill

Run the **skill under test** headless against a **target project**, then read the **trial run**'s record for what its instructions got wrong, made redundant or left implicit. Requires the `claude` CLI. The retrospective reports; the skill under test stays untouched.

## Parameters

`key=value` pairs in the arguments; quote values that contain spaces.

| Parameter | Meaning | Default |
| --- | --- | --- |
| `plugin` | Directory holding `.claude-plugin/plugin.json` | required |
| `target` | Git repository the trial run executes in | required |
| `skill` | Skill name inside the plugin; required only when the plugin ships several | its only skill |
| `model` | Model for the trial run | `sonnet` |
| `effort` | Effort level for the trial run | `medium` |
| `context` | Text appended after the slash command, for example a PRD path | empty |
| `timeout` | Wall-clock limit before the trial run is killed, for example `90m` | `60m` |

## Run the trial

1. **Resolve** absolute paths for `plugin` and `target`. The plugin has a manifest, the target is a git repository, and exactly one skill name is settled from `<plugin>/skills/*/SKILL.md`. Stop with the reason when any of these fails.
2. **Pick** the run directory `reports/dogfood-skill/<UTC timestamp>/` under this repository's root, and a lowercase UUID for the trial run's session.
3. **Start** the script in the background and wait for its completion notice without polling:

   ```sh
   "${CLAUDE_SKILL_DIR}/scripts/run-trial" "<run-dir>" "<plugin>" "<target>" "<skill>" "<model>" "<effort>" "<timeout-in-seconds>" "<uuid>" "<context>"
   ```

   It snapshots the target to `before.txt`, runs `claude -p "/<skill> <context>"` with `--plugin-dir`, `--permission-mode auto` and `--session-id`, kills the process at the timeout, and snapshots again to `after.txt`.

The trial is done when `exit-code` and `after.txt` exist in the run directory.

## Run the retrospective

Once the trial is done, including a `timed-out` run, read [the retrospective reference](references/retrospective.md) and follow it.

The retrospective is done when `<run-dir>/findings.md` exists; print only its path in chat.
