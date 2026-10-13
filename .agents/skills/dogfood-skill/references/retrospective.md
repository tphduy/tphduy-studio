# Retrospective

Runs after a trial. Its inputs are the trial's run directory and the skill under test.

## Sources

Read primary sources only:

- `stream.jsonl`: the `init` event (model, plugins, MCP servers, permission mode), every tool call with its result, and the final `result` event (turns, duration, cost). When the stream is truncated, `~/.claude/projects/*/<uuid>.jsonl` holds the full transcript.
- `stderr.log`, `exit-code`, and `timed-out`, whose presence marks an incomplete run.
- `before.txt` against `after.txt`.
- Files the trial run wrote outside the target, found through the stream's tool calls or by the session UUID in their paths.
- The skill under test: its `SKILL.md` and every file it points to.

A launch that fails (nonzero exit, empty stream) is the finding: report `stderr.log` and stop.

## Dimensions

Examine each dimension:

- **Instruction hygiene**: duplicated, conflicting or redundant instructions across the skill's files, including a rule stated twice where the agent followed only one.
- **Improvable steps**: steps the agent followed but wastefully: repeated observations, avoidable detours, reorderable work, deterministic work done by hand that a script could do.
- **Deviations**: instructions the agent skipped or bent. Treat unclear wording as the cause before agent error.
- **Improvisation**: decisions the agent invented because the skill was silent.
- **Ambiguity stalls**: points where the skill asks for clarification or an input the headless run could not get, and what the agent did instead.
- **Tool friction**: errors, retries or missing dependencies from scripts and validators the skill ships or names.
- **Substitution fidelity**: every `${CLAUDE_*}` variable the skill uses resolved to what this run passed (`${CLAUDE_EFFORT}` is `effort`, `${CLAUDE_SESSION_ID}` is the UUID).
- **Cost**: turns, time and tokens by phase, and reference files read but never used.
- **Undeclared target changes**: before/after differences the skill does not declare as its own.
- **Environment interference**: loaded plugins or MCP servers that steered the run.

The retrospective is done when every dimension has findings or a "none found" naming what was checked. Each finding carries its trace evidence (a `stream.jsonl` line number or an artifact path) and the implicated skill `file:line`. Discard a finding that cannot name both, and a finding caused by the target project rather than the skill's instructions.

## Report

Write `<run-dir>/findings.md`: a header with the parameters, exit status, whether the run was incomplete, and turns and cost; then free-form bullets grouped by dimension. Print only the file's path in chat.
