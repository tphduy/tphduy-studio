# Repository maintenance

This is Duy Tran's personal plugin marketplace for Codex and Claude Code.

## Authoring

- Create plugins under `plugins/<name>/`. Share compatible content and add entries only to supported platforms' catalogs.
- Use root `plugin.json` for portable Codex packages and `.claude-plugin/plugin.json` for Claude Code. Keep name, description, author, and version consistent; versions belong in manifests, not catalog entries.
- For each Codex skill, include `agents/openai.yaml` with `interface.display_name`, `interface.short_description`, and `interface.default_prompt`, aligned with the skill's `SKILL.md`.
- Increment the semantic version when releasing changed content or behavior. Remove retired plugins from applicable catalogs and delete their files; installed copies require explicit uninstall.

## Verification

Run `.venv/bin/python scripts/verify.py` and `.venv/bin/python -m unittest discover -s tests` after structural changes. For installation, updates, removal, or changed plugin behavior, follow [runtime verification](docs/verification.md).

Report each check as `pass`, `failed`, or `inconclusive`, with evidence. Structural validation alone does not prove runtime behavior.
