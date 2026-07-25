---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
---

# Skill Authoring

## Content

- Every loaded line costs tokens.
- Add only what Claude lacks: org specifics, edge cases, non-obvious constraints. Skip defaults and library basics.
- Match freedom to fragility:
  - many paths work → plain instruction ("summarize the test failures")
  - one preferred pattern → pseudocode (retry: try; on 5xx back off; cap 3)
  - fragile, hard-to-undo → exact script (the signed release-publish command)

## Triggering

- Make `description:` the trigger — one third-person line, leading with the use case in the user's words.
- Put detailed conditions in `when_to_use:`. Front-load both — the listing truncates them.

## Structure

- Keep `SKILL.md` under 500 lines; extract anything not needed on every invocation.
- Put runnable code in `scripts/`; put everything else — templates, boilerplate, long detail — in `references/`. Name each file from `SKILL.md`; unreferenced files are invisible.
- Keep references one level deep. Add a contents list to any reference over ~100 lines.

## Portability

- A skill is self-contained: everything it needs lives under its own directory; never reference paths outside `${CLAUDE_SKILL_DIR}`.
- Run scripts from `${CLAUDE_SKILL_DIR}` so paths survive a cwd change.

## Workflows

- Number the steps of a multi-step task.
- Track a long, stateful task with a live checklist.
- Where output must pass a check, loop validate → fix → repeat; proceed only when it passes.

## Invocation

- Leave skills model-invocable by default.
- Set `disable-model-invocation: true` only when an unprompted run would be hard to undo — publish, deploy, send, delete.
- Set `user-invocable: false` for pure background knowledge.

## Arguments

- Declare args in `arguments:`; reference as `$name`. Prefer `$name` over `$0`/`$1`. Use `$ARGUMENTS` for the whole raw string.
- Quote multi-word values at the call site. Show the call shape in `argument-hint:`, e.g. `argument-hint: '<file> "<search query>"'`.
- Guard required args once at the top: blank → stop and state the call shape. Add no section explaining an argument, its default, or an empty-value fallback.
- Write `$name` inline where the value belongs; assume it is present.
- Never pass `$ARGUMENTS` to a shell command. Pass quoted positional values: `"$0"`, `"$env"`.

## Shell in the body

- `` !`cmd` `` runs `cmd` at preprocessing and pastes its output into the body before Claude reads it. Use it to inject read-only context: `` !`git status -s` ``, `` !`date +%F` ``.
- A command shown as plain text or in a code block is not executed; Claude chooses whether to run it as a tool call. Use that for side effects; pair with `disable-model-invocation: true`.
