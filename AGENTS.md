# AGENTS.md

Personal Claude Code + Codex plugin marketplace. Structure: `plugins/prompt-master` (vendored `prompt-master` skill), `plugins/notify` (macOS notification hook), `rules/` (global rules copied into `~/.claude/rules`), `status-line/`, `.claude-plugin/marketplace.json` (Claude Code marketplace), `.agents/plugins/marketplace.json` (Codex marketplace).

## Conventions

- No build or test tooling — pure Markdown/JSON/shell. Nothing to compile or run.
- Commit messages: short imperative summary, no body, no prefix (see `git log`).
- Each plugin has its own `plugin.json` version, independent of the others and of the marketplace manifests.
- A plugin that supports both platforms carries two manifests side by side: `.claude-plugin/plugin.json` for Claude Code and a root `plugin.json` for Codex, both pointing at the same shared `skills/` directory — don't duplicate skill content per platform.
- Vendored code (e.g. `plugins/prompt-master/skills/prompt-master`) keeps its own `LICENSE`/`README.md` under the original author — never merge into the repo-root `LICENSE`.
- `prompt-master` is vendored via `git subtree`, not a manual copy — pull upstream updates with `git subtree pull --prefix=plugins/prompt-master/skills/prompt-master https://github.com/nidhinjs/prompt-master.git main --squash` rather than copying files over it.
- Reserve `git subtree` vendoring for sources that don't already ship as a Claude Code/Codex marketplace plugin, or where the content gets hand-edited to personal taste — everything else (currently `i-have-adhd`, `mattpocock/skills`, `SimpleEnglish`, `ecc`) is installed from its own upstream marketplace instead (see `README.md`'s "Third-party skills" section), never vendored into this repo.
- `rules/*.md` is Claude Code-only — Codex has no per-path rule injection, only a repo-wide `AGENTS.md`, so don't try to port rules content there. Style rules for editing `SKILL.md` or `rules/*.md` content live in `rules/instruction-voice.md` and `rules/skill-authoring.md` — read those before touching skill or rule files rather than restating them here.
- `rules/*.md` filenames are referenced by glob (`cp rules/*.md`) in `README.md`'s setup steps — keep filenames stable.
