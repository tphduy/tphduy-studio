---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
---

# Skill Authoring

## Portability

- A skill is self-contained: everything it needs lives under its own directory; never reference paths outside `${CLAUDE_SKILL_DIR}`.
- Run scripts from `${CLAUDE_SKILL_DIR}` so paths survive a cwd change.

## Workflows

- Number the steps of a multi-step task.
- Track a long, stateful task with a live checklist.
- Where output must pass a check, loop validate → fix → repeat; proceed only when it passes.

## Arguments

- Declare args in `arguments:`; reference as `$name`. Prefer `$name` over `$0`/`$1`. Use `$ARGUMENTS` for the whole raw string.
- Quote multi-word values at the call site. Show the call shape in `argument-hint:`, e.g. `argument-hint: '<file> "<search query>"'`.
- Guard required args once at the top: blank → stop and state the call shape. Add no section explaining an argument, its default, or an empty-value fallback.
- Write `$name` inline where the value belongs; assume it is present.

## Shell in the body

- `` !`cmd` `` runs `cmd` at preprocessing and pastes its output into the body before Claude reads it. Use it to inject read-only context: `` !`git status -s` ``, `` !`date +%F` ``.
- A command shown as plain text or in a code block is not executed; Claude chooses whether to run it as a tool call.
