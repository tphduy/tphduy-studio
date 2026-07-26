Vendored from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd), `skills/i-have-adhd/` subdirectory, via `git subtree`.

Upstream is MIT-licensed by Ayoub Ghriss — see `LICENSE` in this directory.

Pull upstream updates with:

```sh
git subtree pull --prefix=plugins/dev-toolkit/skills/i-have-adhd https://github.com/ayghri/i-have-adhd.git main --squash
```

Note: unlike `prompt-master`, this skill lives in a subdirectory of its upstream repo rather than at the repo root, so a straight `subtree pull` will pull the whole upstream tree (README translations, `plugin.json`, `evals/`, etc.) into this directory alongside `SKILL.md`. Re-run the split-and-pull steps below instead to keep only the skill content in sync:

```sh
# in a scratch clone of the upstream repo
git subtree split --prefix=skills/i-have-adhd -b i-have-adhd-split

# back in this repo
git subtree pull --prefix=plugins/dev-toolkit/skills/i-have-adhd <path-to-scratch-clone> i-have-adhd-split --squash
```
