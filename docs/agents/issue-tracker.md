# Issue tracker: GitHub

Issues and specs live in GitHub Issues for this repository. Use the `gh` CLI from this checkout; it resolves the repository from `origin`.

## Ticket operations

- Publish a ticket: `gh issue create --title "..." --body-file <file>`.
- Fetch a ticket and discussion: `gh issue view <number> --comments`.
- Fetch its labels: `gh issue view <number> --json labels`.
- List tickets: `gh issue list --state open --json number,title,body,labels,comments`.
- Comment: `gh issue comment <number> --body-file <file>`.
- Apply or remove labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close: `gh issue close <number> --comment "..."`.

Use files containing actual newlines for multiline bodies. Read `triage-labels.md` when selecting triage labels.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Wayfinding operations

- Map: one issue labelled `wayfinder:map`, containing Notes, Decisions-so-far, and Fog.
- Child tickets: GitHub sub-issues labelled `wayfinder:<type>`, where type is research, prototype, grilling, or task. If sub-issues are unavailable, use a task list in the map and `Part of #<map>` at the top of each child.
- Blocking: use native GitHub issue dependencies with issue database IDs. If unavailable, record `Blocked by: #<n>, #<n>` in the child body. A child is unblocked when every blocker is closed.
- Frontier: choose the first open, unblocked, unassigned child in map order.
- Claim: assign the child to the driving developer before starting work.
- Resolve: comment with the answer, close the child, and append a brief finding plus its link to the map's Decisions-so-far.
