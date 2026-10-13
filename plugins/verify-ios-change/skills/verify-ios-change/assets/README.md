# Evidence templates

`manifest.json` is the version 6 starter manifest used by `scripts/create-run-dir`. It contains no example test cases. The agent updates the copy in the run directory throughout verification.

`index.html` is the standalone report template used by `scripts/generate-report RUN_DIR` during run initialization, after preparation and at Finish. The script embeds the latest manifest safely; the agent does not edit report JSON by hand.

`manifest.schema.json` defines the data structure. See [the evidence bundle reference](../references/evidence-bundle.md) for recording instructions, statuses, evidence requirements and validation commands.
