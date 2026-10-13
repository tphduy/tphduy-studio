# Advanced verification

Use this reference only after ordinary recovery is exhausted and `run.effort`, resolved in SKILL.md, is `high`, `xhigh` or `max`. Assess available project-supported ways to establish conditions, exercise behaviour and observe results, such as supported routes, fixtures and debug controls. Treat ordinary recovery as exhausted when evidence shows that available approaches cannot establish the required conditions or observations; repeated attempts are unnecessary.

## Choose an intervention

Start from the blocked claim: identify whether the obstacle concerns setup, execution or observation, the target implementation that must execute, and evidence that would establish its expected effect. Choose the narrowest setup, dependency or observation boundary that preserves the behaviour under test and its relevant lifecycle. Record which claims the intervention enables and which it bypasses or leaves unverified.

Choose from these techniques or derive another from the app's architecture; this is a menu, not a required sequence.

| Obstacle | Candidate intervention |
| --- | --- |
| Wrong hints or inaccessible route | Invoke an existing router/coordinator, or add a temporary launch/home entry into the target screen with its dependencies and normal lifecycle. |
| Missing account type, flag or data | Supply synthetic state through the app’s existing account/configuration interfaces, seed simulator-local persistence, or supply a source-grounded fixture. Record which values were constructed and which came from existing fixtures. |
| Unavailable or rare service response | Substitute a dependency or intercept a specific request with a response matching the app's contract; exercise the unchanged downstream parsing, state transitions and rendering. |
| Expiry, timing, retry or failure branch | Control an injected clock, scheduler or dependency response to establish the required condition. Preserve timing behaviour when timing itself is the claim. |
| Live-process access offers a credible path | Use LLDB expressions to invoke a known route or set prerequisite state on a live object; verify the resulting state before exercising the case. |
| Invisible transition or side effect | Add focused logs, counters or probes; use breakpoints/watchpoints to observe the relevant execution and state. |

Use known interfaces and source-derived state shapes. Keep interventions within the verification environment and existing authorization; missing prerequisites do not grant authority to modify external accounts or systems. Assess whether the intervention alters properties relevant to the claim, including timing, lifecycle, concurrency or persistence, and qualify affected claims. Replacing the expected result, forcing the target handler's return value, skipping its validation or repairing its logic cannot establish `assisted_pass` for that behaviour.

For LLDB work, read [state diagnostics](state-diagnostics.md) before attachment or expressions. It owns debugger coordination, expression reliability and cleanup. Use LLDB for inspection or prerequisite setup; the selected driver still exercises changed interactions.

## Exercise and judge

1. Record an `advanced` revision explaining the exhausted ordinary approach, the new hypothesis and affected cases. Before applying it, register the intervention as described in [the evidence bundle reference](evidence-bundle.md), preserve the original source/state needed for restoration, and run draft validation.
2. Apply the intervention, confirm the intended setup or observation capability and exercise the existing case with the selected driver. Recheck affected preparation capabilities after a build/process change. Capture evidence appropriate to the intervention mechanism and tie it to the exact build/process and case observations.
3. Use `assisted_pass` only when all expected effects have the normal passing evidence and the target behaviour remained intact. Use `fail` when the mismatch establishes a defect in that behaviour; if the intervention itself could explain it, investigate or use `inconclusive`. Additional effort alone earns no successful result.

Continue while a materially different, evidence-backed intervention offers a credible next step. Record what each attempt learned in its revision. Reject approaches that replace the behaviour under test while considering other viable approaches. Stop when no evidence-backed next approach remains and explain the remaining uncertainty.

Follow SKILL.md's Finish rules: restore temporary source, retain the intervened app for inspection, and report runtime state and restoration instructions separately from case results. Keep historical evidence attached to the build/process that produced it.
