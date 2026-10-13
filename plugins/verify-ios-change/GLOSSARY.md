# Agent-driven iOS verification

An agent exercises a changed iOS screen in a simulator and returns evidence that PR reviewers can audit. The work splits into the tooling that touches the simulator and the procedure that decides what to exercise.

## Language

### Layers

**Driver**:
A tool that observes and acts on a running simulator app on the agent's behalf.
_Avoid_: Controller, automation tool, simulator MCP

**Inspector**:
A tool that reads the app's native view hierarchy from inside the app's process.
_Avoid_: View debugger, driver

**Harness**:
The verification procedure that decides what to exercise and assembles evidence, independent of any particular driver.
_Avoid_: Skill, plugin (the harness ships as one, but the words are not interchangeable), framework

**Driver contract**:
The set of capabilities the harness may rely on from drivers and inspectors, named in vendor-neutral terms.
_Avoid_: Adapter, API, interface

### Observation

**Accessibility tree**:
The element tree the app exposes to assistive technology.
_Avoid_: UI tree, hierarchy (unqualified)

**Native hierarchy**:
The app's view, layer and view-controller tree as the app itself holds it, including elements with no accessibility.
_Avoid_: View tree, debug hierarchy

**Expected effect**:
The observable change an action is declared to cause, checked after the action to decide whether it landed.
_Avoid_: Assertion, postcondition, settle

**Coordinate-based action**:
An action aimed at a point rather than at an element the accessibility tree can name.
_Avoid_: Blind tap, raw tap

### Procedure

**Explore & plan**:
The recurring work of discovering the screen and preparing or revising how to exercise its test cases.
_Avoid_: Explore pass, dry run

**Verification plan**:
The ordered preconditions, resets, actions and expected effects used to exercise test cases reproducibly.
_Avoid_: Replay plan, test suite

### Inputs and outputs

**Hint**:
A claim from an upstream source about preconditions or how to reach a screen, which may be wrong.
_Avoid_: Navigation path, instructions

**Project context**:
What the app's own repository tells the agent: its instructions, existing debugging and logging harness, and code.
_Avoid_: Consumer config, project settings

**Test case**:
A scenario with preconditions, actions and expected effects that verifies changed app behaviour, judged from runtime evidence.
_Avoid_: Claim, check, assertion

**Environment check**:
The current observation of a capability needed to prepare, exercise or inspect the app.
_Avoid_: Test case, attempt history

**Blocker**:
An unavailable capability that prevents verification after useful recovery is exhausted.
_Avoid_: Setup task, missing optional capture

**Limitation**:
An evidence or coverage gap that leaves some verification possible.
_Avoid_: Blocker, failure

**Side observation**:
Something outside the change that looks wrong, reported separately from test-case results.
_Avoid_: Regression (unless confirmed), bug

**Evidence bundle**:
The per-run collection of artifacts and the report that ties test cases to them.
_Avoid_: Artifacts folder, test results

**Fixture app**:
The Playground app used to check drivers and inspectors against known screens.
_Avoid_: Sample app, test app
