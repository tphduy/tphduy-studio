---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
  - "**/rules/**/*.md"
  - "**/agents/**/*.md"
---

# Instruction Voice

Apply to skills, rules, and custom subagent definitions.

- Command, don't describe.
  ✗ "This skill helps you format output."
  ✓ "Format the output as a table."
- Use imperative, second-person verbs.
  ✗ "The function should be renamed."
  ✓ "Rename the function."
- Keep sentences short — declarative, under 12 words.
  ✗ "When an error occurs, it is generally advisable to check the logs first."
  ✓ "On error, check the logs first."
- Make each bullet one claim.
  ✗ "Validate the input and cache the result."
  ✓ "Validate the input." / "Cache the result."
- Cut hedging — no "perhaps", "may", "might", "could", "consider".
  ✗ "You may want to consider caching the result."
  ✓ "Cache the result."
- Prefer lists to prose.
  ✗ "First lint, then run the tests, then build."
  ✓ "1. Lint. 2. Test. 3. Build."
- Give every item the same grammatical shape.
  ✗ "Validate input. / Logging errors. / You should retry."
  ✓ "Validate input. / Log errors. / Retry failures."
- Use concrete nouns, not abstractions.
  ✗ "Handle the data appropriately."
  ✓ "Parse the CSV into rows."
- Write header fragments, not titles.
  ✗ "## How to Set Up the Environment"
  ✓ "## Environment setup"
