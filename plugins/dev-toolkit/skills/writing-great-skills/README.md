Vendored from [mattpocock/skills](https://github.com/mattpocock/skills), `skills/productivity/writing-great-skills/` subdirectory, via `git subtree`.

Upstream is MIT-licensed by Matt Pocock — see `LICENSE` in this directory.

Since this skill lives in a subdirectory of its upstream repo rather than at the repo root, a straight `subtree pull` would pull the whole upstream monorepo (other skills, `CLAUDE.md`, `package.json`, etc.) into this directory alongside `SKILL.md`. Re-run the split-and-pull steps below instead to keep only this skill's content in sync:

```sh
# in a scratch clone of the upstream repo
git subtree split --prefix=skills/productivity/writing-great-skills -b writing-great-skills-split

# back in this repo
git subtree pull --prefix=plugins/dev-toolkit/skills/writing-great-skills <path-to-scratch-clone> writing-great-skills-split --squash
```
