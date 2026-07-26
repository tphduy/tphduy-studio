# AGENTS.md

Personal Claude Code plugin marketplace. Structure: `plugins/dev-toolkit` (skills `prove-it`, vendored `prompt-master`, `i-have-adhd`, `grilling`, `writing-great-skills`), `plugins/notify` (macOS notification hook), `rules/` (global rules copied into `~/.claude/rules`), `statusline/`, `.claude-plugin/marketplace.json`.

## Conventions

- No build or test tooling — pure Markdown/JSON/shell. Nothing to compile or run.
- Commit messages: short imperative summary, no body, no prefix (see `git log`).
- Each plugin has its own `plugin.json` version, independent of the others and of `.claude-plugin/marketplace.json`.
- Vendored code (e.g. `plugins/dev-toolkit/skills/prompt-master`, `plugins/dev-toolkit/skills/i-have-adhd`, `plugins/dev-toolkit/skills/grilling`, `plugins/dev-toolkit/skills/writing-great-skills`) keeps its own `LICENSE`/`README.md` under the original author — never merge into the repo-root `LICENSE`.
- `prompt-master` is vendored via `git subtree`, not a manual copy — pull upstream updates with `git subtree pull --prefix=plugins/dev-toolkit/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash` rather than copying files over it.
- `i-have-adhd` is vendored via `git subtree` from the `skills/i-have-adhd` subdirectory of [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (not the repo root, unlike `prompt-master`) — see its `README.md` for the split-and-pull steps needed to sync updates without pulling in the rest of that repo.
- `grilling` and `writing-great-skills` are vendored via `git subtree` from the `skills/productivity/grilling` and `skills/productivity/writing-great-skills` subdirectories of [mattpocock/skills](https://github.com/mattpocock/skills) — same split-and-pull pattern as `i-have-adhd`, documented in each skill's own `README.md`. Upstream also has a separate, thin `grill-me` skill (a user-invoked wrapper that just runs `/grilling`) — intentionally not vendored, since the full `grilling` skill is vendored directly.
- Style rules for editing `SKILL.md` or `rules/*.md` content live in `rules/instruction-voice.md` and `rules/skill-authoring.md` — read those before touching skill or rule files rather than restating them here.
- `rules/*.md` filenames are referenced by glob (`cp rules/*.md`) in `README.md`'s setup steps — keep filenames stable.
