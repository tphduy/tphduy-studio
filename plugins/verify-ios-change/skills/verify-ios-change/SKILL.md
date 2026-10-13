---
name: verify-ios-change
description: Prepare and verify changed iOS screens or interactions in a simulator with runtime evidence.
---

# Verify iOS change

Exercise the changed behaviour and report findings with runtime evidence. Prepare the environment as needed; the user owns functional source fixes and bundle retention.

## Inputs

Use the PRD as the primary requirement, supported by design references and the diff. Discover the app, bundle ID, simulator and setup hints from project context; clarify material ambiguity. Prefer project instructions, fixtures and debugging tools over this skill's references.

Active effort: `${CLAUDE_EFFORT}`. Record the resolved value in `run.effort`; use null for an unavailable, unresolved or unrecognized value.

## Prepare environment

1. Run the command below to scaffold this verification's **run directory** and `manifest.json`. Use its printed path for all evidence.

   ```sh
   "${CLAUDE_SKILL_DIR}/scripts/create-run-dir" "${CLAUDE_PROJECT_DIR}" "${CLAUDE_SESSION_ID}"
   ```

2. Read [the evidence bundle reference](references/evidence-bundle.md) before updating `manifest.json`. Record environment, tools, the selected driver and readiness checks as defined there.
3. Prepare and observe readiness for the app/build, simulator, action driver, native hierarchy, LLDB and logs, recording one readiness check per capability. Recover setup problems using project guidance and bootstrap tooling as needed; when recovery is exhausted, apply the bundle reference's blocker and limitation rules.
   - **Simulator:** select by priority: user-specified, project-designated, suitable booted, then newest available compatible. Record the choice in its readiness check and confine simulator operations to that UDID.
   - **Driver:** select one for the whole run from the table below, and read its reference before its first command.
   - **Inspection:** read [hierarchy inspection](references/hierarchy.md) before configuring native inspection, and [state diagnostics](references/state-diagnostics.md) for the mandatory LLDB readiness check.
   - **Order:** configure required capture and injection before launching, launch without an attached debugger, then attach the driver to the running process without relaunching. Follow state diagnostics for detach/resume checks and coordinated driver actions during breakpoint/watchpoint observation.
   - **Logs:** pass readiness when capture starts successfully for the intended target, its process or session remains active, and its output destination is accessible. Empty capture is acceptable; cases that depend on log content must observe that content during verification.
4. Record process IDs, session names, capture paths and resource ownership in the relevant readiness-check details as resources are started or reused.

If preparation blocks all verification, go to Finish.

### Driver selection

| Driver | Choose when |
| --- | --- |
| [agent-device](references/drivers/agent-device.md) | Default: cheap observation and typed failures. |
| [XcodeBuildMCP](references/drivers/xcodebuildmcp.md) | App logs matter or the run already uses it to build. |
| [Appium](references/drivers/appium.md) | The project has Appium tests or capabilities. |
| [AXe](references/drivers/axe.md) | Coordinate or single-element actions without a runner. |

## Verification loop

Repeat Explore & plan and Exercise until every case is judged or withdrawn, then go to Finish.

### Explore & plan

1. **Explore the codebase and consolidate available context** to understand the change and its intended behaviour.
2. **Derive high-ROI test cases** for the change, prioritizing user impact and regression risk relative to verification effort. Record the plan in `manifest.json` before navigating and run draft validation.
3. **Refine the current plan** as understanding develops. On returning from Exercise, update it in place while preserving existing results and evidence.

### Exercise

1. **Navigate to the next planned case** in the current session. Use project hints, screen captures, accessibility and runtime diagnostics. Check each hint's landmark at its own step and record the observed landmark and supporting evidence in the relevant case step. Use separate checks for preparation facts or route blockers. If the changed screen cannot be reached, follow the divergence step below.
2. **Confirm preconditions** by observation, applying the case's reset if needed. Capture video when available and take a before screenshot.
3. **Exercise and observe** each action, stating its expected effect before running it. Wait for that effect using driver waits or repeated observation, then take an after screenshot. Exercise changed interactions directly; verify static rendering through runtime inspection. For elements available only in the native hierarchy, use the hierarchy reference's coordinate guidance.
4. **Record evidence** for each step: the action or runtime observation, expected effect, observed result with its locator and method, and supporting artifacts.
5. **On a divergence, return to Explore & plan** to investigate the cause and revise the current manifest plan. Record what triggered the revision, what changed, the affected cases and supporting evidence, then run draft validation before resuming Exercise.
   - A plan revision may change route, locators, order, waits, resets and preconditions.
   - A case wrongly derived from the PRD or the diff is withdrawn, with the reason and evidence that showed it; it stays in the bundle. A correct case that cannot be shown stays and ends `inconclusive`.
   - Continue ordinary recovery while evidence supports a useful next approach. When remaining approaches lack a credible path to establishing the required conditions or observations, use Advanced recovery below or end the case `inconclusive` with the remaining blocker.
   - Two exits skip the loop: an action whose located target does not behave as the PRD says is `fail`; a demonstrated driver fault is `inconclusive`, with the driver error and supporting evidence. Either way, move on to the next case.
6. **Resolve uncertainty** with [state diagnostics](references/state-diagnostics.md), [hierarchy inspection](references/hierarchy.md), constraint inspection or behaviour-neutral diagnostic edits. Record temporary edits and affected cases in `temporary_modifications`, preserving the build/process identity of their evidence. Source restoration and runtime retention follow Finish; another case run is optional.

### Advanced recovery

Only after ordinary recovery is exhausted and the resolved `${CLAUDE_EFFORT}` is `high`, `xhigh` or `max`, read [advanced verification](references/advanced-verification.md). It permits temporary source and runtime interventions, including LLDB, while preserving the behaviour being verified. Record advanced revisions separately; continue while a materially different, evidence-backed approach offers a credible path to verification. Otherwise end the affected case `inconclusive`.

## Results

Judge each test case from its expected effects and runtime evidence:

- `pass`: every expected effect matches a machine check (driver wait, accessibility value, log line or native dump), and the case or its steps reference a screenshot. Video and GIF capture are optional.
- `assisted_pass`: the same evidence requirements as `pass`, obtained through advanced recovery. Link the intervention in `temporary_modifications` and explain the verified scope and unproven conditions in `detail`. Evidence that depends on an intervention earns this status instead of `pass`.
- `fail`: an exercised action's expected effect is absent or different. Explain the mismatch and attach evidence.
- `inconclusive`: the case is unexercised, blocked, under-evidenced or affected by a demonstrated driver fault. Explain what remains unverified.
- `withdrawn`: the case was wrongly derived; preserve its explanation and evidence.

Resolve every `planned` case before Finish. Record findings outside the change in `side_observations`.

## Finish

1. **Clean up**, including blocked runs: restore only the run's temporary source edits, preserving pre-existing work. Release run-owned capture/driver/debugger resources and preserve reused resources and the simulator. Leave an intervened app available for inspection without rebuilding or resetting it; retain only run-owned support it needs. Verify source restoration and record cleanup failures, retained resources, final runtime state and concrete restoration steps. Cleanup is independent of case results and requires no case re-run.
2. **Reconcile `manifest.json`** with the final source, build and runtime state, distinguishing restored source from the retained app and the build/process used for each observation.
3. **Generate and validate the report** as [the evidence bundle reference](references/evidence-bundle.md) describes.
4. **Return per-case results and cleanup results**, including blockers or limitations, retained resources and the report path, without an overall verdict.
