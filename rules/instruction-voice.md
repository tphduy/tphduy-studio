---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
  - "**/rules/**/*.md"
  - "**/agents/**/*.md"
---

# Instruction Voice

Apply to skills, rules, and custom subagent definitions.

- Use imperative, second-person verbs.
  ✗ "The function should be renamed."
  ✓ "Rename the function."
- Keep sentences short — declarative.
  ✗ "When an error occurs, it is generally advisable to check the logs first."
  ✓ "On error, check the logs first."
- Give every item the same grammatical shape.
  ✗ "Validate input. / Logging errors. / You should retry."
  ✓ "Validate input. / Log errors. / Retry failures."
- Use concrete nouns, not abstractions.
  ✗ "Handle the data appropriately."
  ✓ "Parse the CSV into rows."
- Write header fragments, not titles.
  ✗ "## How to Set Up the Environment"
  ✓ "## Environment setup"
