# Evidence bundle

`manifest.json` is the source of truth for one run. [`assets/manifest.schema.json`](../assets/manifest.schema.json) defines every field with its type, allowed values and meaning; read it before the first edit, and update the manifest in place as work progresses. [`scripts/validate-manifest`](../scripts/validate-manifest) checks what the schema cannot: IDs, references, evidence files and completion. Validation checks the record, not the truth of an observation. Schema 6 replaces schema 5; current tooling rejects older bundles without rewriting them. Their generated reports remain standalone.

## Initialize and record

`create-run-dir` creates a fresh run directory outside the project and main checkouts and initializes `manifest.json` from [the starter template](../assets/manifest.json), with run identity set and every collection empty. It then generates `index.html` from the initialized manifest.

If scaffolding fails, recover with a fresh writable temporary run directory outside the checkout and copy the starter manifest into it. Set its run ID, absolute project directory and UTC start time, then run `generate-report` on the run directory. If evidence storage remains unavailable, stop and explain the blocker directly.

Keep the manifest valid JSON between updates. A recovered capability no longer appears as a blocker.

- **Environment:** record the build/source identity and readiness evidence in the app/build check; identify a continued session when applicable.
- **Resources:** readiness-check details identify process IDs, session names, capture paths and whether each resource was started or reused. After a build replacement, relaunch or other resource change, update the affected build/resource details and recheck affected capabilities needed by the remaining cases. Mark capabilities no longer needed `not_applicable`; apply the blocker/limitation rules to unavailable capabilities still needed. Preserve earlier evidence with its build/process identity so historical readiness remains distinguishable from current readiness.
- **Evidence:** give capture tools absolute paths inside the run directory, then register paths relative to it. Revision records distinguish `ordinary` divergences from `advanced` attempts; both use SKILL.md's evidence-driven recovery rules; only the current plan is stored.
- **Effort:** copy the resolved active effort from SKILL.md into `run.effort`. Null does not enable advanced recovery; do not infer effort from task difficulty.

## Temporary modifications

Use `temporary_modifications` for both source edits and runtime-only changes. Set `purpose` to `diagnostic` for ordinary behaviour-neutral observation, or `intervention` for advanced recovery. Before applying an intervention, record its mechanism, affected cases, and `scope`: the target behaviour preserved and claims left unproven. Link those cases to an advanced revision explaining why ordinary recovery was exhausted.

Register patches, fixtures or debugger transcripts as artifacts; record the tested build/process identity in `runtime_state`. `test_cases` retains all affected cases; `result_cases` identifies the subset whose current verification depends on the modification. If an optional independent run replaces that evidence, remove the case from `result_cases` while preserving its historical association and artifacts. Restoration alone does not remove a dependency. `assisted_pass` requires intervention artifacts, the normal passing evidence, and a case `detail` explaining its qualified scope. Restore source at Finish and update `state`; `runtime_only` means no source edit was made. Case status never depends on restoration or a recheck.

At Finish, fill `runtime_state` with the retained app/build/process, active overrides and supporting resources, and `restoration` with concrete steps to return them to normal. Distinguish persistent state from process-local state that expires on relaunch. Explain any cleanup failure in the cleanup check; retain evidence and case results. Ordinary diagnostics also record their final runtime state and any remaining restoration work.

## Blockers and limitations

An unbuilt app, an unbooted simulator or missing tooling needs preparation, not a blocker; bootstrap tooling using project guidance. The schema defines blocker and limitation on `checks[].impact`. Continue cases that remain verifiable and explain affected cases as inconclusive. A run blocked before planning has an empty `test_cases` array and an explanatory blocker check. There is no overall verdict or stored finish timestamp.

Record a build failure in an app/build check with its reason, impact and build-log artifact; update the same check if recovery succeeds.

## Generate and validate

After preparation and at Finish after cleanup, generate the standalone report. It embeds the current manifest in a copy of [`assets/index.html`](../assets/index.html); regenerate after manifest changes.

```sh
"${CLAUDE_SKILL_DIR}/scripts/generate-report" "<run-dir>"
```

One command validates the structure against the schema, then references and evidence, and exits nonzero on a problem; a structural problem stops it before the reference checks:

```sh
"${CLAUDE_SKILL_DIR}/scripts/validate-manifest" "<run-dir>"
```

It needs the `jsonschema` Python package or Node.js (`npx ajv-cli@5`) and exits 3 when neither is available; install one rather than skipping the check. `--structure-only` checks the schema alone.

Use draft validation during preparation and planning. It allows planned cases and does not require an HTML report.

At Finish, including runs blocked before planning, resolve every planned case, regenerate the report and run:

```sh
"${CLAUDE_SKILL_DIR}/scripts/validate-manifest" --final "<run-dir>"
```

Final validation requires initialized run identity, a matching report, and either cases or an explanatory setup blocker. Both passing statuses need observed results for every step and a screenshot reference. Assisted passes additionally need an eligible effort, a linked intervention and its evidence, scope and advanced revision. A failing case needs an observed mismatch and evidence artifacts; a withdrawal preserves supporting evidence. Temporary modifications require final runtime state and restoration instructions, independently of their case results.
