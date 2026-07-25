# No Manual Line Wrapping

- Never hard-wrap prose at a column limit. One sentence or bullet = one unbroken line.
- In YAML and frontmatter, never use folded (`>`) or literal (`|`) scalars. Use a plain quoted single-line string.

```yaml
# Bad — folded scalar wraps one idea across lines
description: >
  Breaks when
  indentation is lost.
# Good
description: "Survives copy-paste as one line."
```

**Why:** One line = one idea. A mid-sentence newline splits it and breaks on copy-paste.