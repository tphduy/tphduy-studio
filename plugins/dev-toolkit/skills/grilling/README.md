Vendored from [mattpocock/skills](https://github.com/mattpocock/skills), `skills/productivity/grilling/` subdirectory, via `git subtree`.

Upstream is MIT-licensed by Matt Pocock — see `LICENSE` in this directory.

This is the full `grilling` skill, not upstream's separate `grill-me` (a thin, user-invoked wrapper that just runs `/grilling`) — that wrapper was intentionally not vendored.

Since this skill lives in a subdirectory of its upstream repo rather than at the repo root, a straight `subtree pull` would pull the whole upstream monorepo (other skills, `CLAUDE.md`, `package.json`, etc.) into this directory alongside `SKILL.md`. Re-run the split-and-pull steps below instead to keep only this skill's content in sync:

```sh
# in a scratch clone of the upstream repo
git subtree split --prefix=skills/productivity/grilling -b grilling-split

# back in this repo
git subtree pull --prefix=plugins/dev-toolkit/skills/grilling <path-to-scratch-clone> grilling-split --squash
```
