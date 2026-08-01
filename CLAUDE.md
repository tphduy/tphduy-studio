# CLAUDE.md

Personal Claude Code plugin marketplace. Structure: `plugins/prompt-master` (vendored `prompt-master` skill), `plugins/prove-it` (`prove-it` skill), `plugins/notify` (macOS notification hook), `rules/` (global rules copied into `~/.claude/rules`), `statusline/`, `.claude-plugin/marketplace.json`.

## Conventions

- No build or test tooling — pure Markdown/JSON/shell. Nothing to compile or run.
- Commit messages: short imperative summary, no body, no prefix (see `git log`).
- Each plugin has its own `plugin.json` version, independent of the others and of `.claude-plugin/marketplace.json`.
- Vendored code (e.g. `plugins/prompt-master/skills/prompt-master`) keeps its own `LICENSE`/`README.md` under the original author — never merge into the repo-root `LICENSE`.
- `prompt-master` is vendored via `git subtree`, not a manual copy — pull upstream updates with `git subtree pull --prefix=plugins/prompt-master/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash` rather than copying files over it.
- `i-have-adhd`, `grilling`, and `writing-great-skills` are NOT vendored in this repo — install them from their own upstream marketplaces instead (see `README.md`'s "Third-party skills" section).
- Style rules for editing `SKILL.md` or `rules/*.md` content live in `rules/instruction-voice.md` and `rules/skill-authoring.md` — read those before touching skill or rule files rather than restating them here.
- `rules/*.md` filenames are referenced by glob (`cp rules/*.md`) in `README.md`'s setup steps — keep filenames stable.
