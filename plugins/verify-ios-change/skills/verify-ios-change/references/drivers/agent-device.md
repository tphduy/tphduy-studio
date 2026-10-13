# agent-device

[callstack/agent-device](https://github.com/callstack/agent-device): a CLI (also MCP and Node API) with a daemon and an XCUITest runner. Bake-off: 0.21.22 on Xcode 27.0, iOS 26.5 and 27.0. Versions are not pinned; record `agent-device --version` in `tools`.

**Prefer it** by default: the cheapest observation, typed failures, a UI diff after every action and the current screen named on a wait timeout.

`agent-device help`, `help <command>` and `help workflow` are the authority for exact flags; this file records what the bake-off learned.

## Setup

- Run it with `npx agent-device <command>` (no install step), or use the copy you were told to use. It need not be on `PATH`.
- The first `open` builds the XCUITest runner into `~/.agent-device/apple-runner` (about 4 s when Xcode caches are warm; longer cold).
- Run `session list` first. A session already holding the simulator refuses `open` with `DEVICE_IN_USE` (`--wait` only delays that). Reuse it: pass its name as `--session` on every command and confirm with `snapshot` that it shows the app under test. Otherwise target the selected simulator: pass `--platform ios --udid <udid>` on `open`, and use a named `--session` for the run.
- `install <bundle-id> <path.app>` installs; `open <bundle-id> --relaunch` starts fresh. `open` without `--relaunch` attaches to the app already running, which keeps an injected inspector alive (see [hierarchy inspection](../hierarchy.md)); compare the app's PID before and after to confirm it.
- Use `close` to end a run-owned session when the skill's Finish requires cleanup; leave reused sessions open.

## Observe and exercise

Use CLI help for snapshots, screenshots, locators, actions and waits. Prefer `snapshot -i` for actionable elements; request the full tree or JSON only when needed. Refs from a snapshot become stale after the screen changes.

`--settle` waits for quiet and prints a diff. A diff of `+0 -0` can mean a dropped action: check the expected effect. `wait absent` takes one selector argument (`wait absent 'text="Saved"'`). On timeout, `Current surface: …` identifies the observed screen and helps diagnose wrong navigation hints.

## Errors (W3C WebDriver vocabulary)

Add `--json` for `error.code` and `error.details.reason`.

| WebDriver error | agent-device |
|---|---|
| `no such element` | `COMMAND_FAILED`, `reason: selector_not_found`; text `Selector did not match: …`, exit 1. The same error is returned when you are on the wrong screen; tell them apart with a landmark |
| `timeout` | `COMMAND_FAILED`, `reason: wait_deadline_exceeded`; text `wait timed out for …. Current surface: …`, exit 1 |
| ambiguous match | `AMBIGUOUS_MATCH` with up to 5 candidate refs. `find` never raises it: it silently takes the first match |
| `element not interactable` | `reason: target_covered`, or `is behind the visible keyboard` (`tap_keyboard_occludes_target`) |
| no effect | Not reported by the action (exit 0); the `--settle` diff is `+0 -0`, and `wait`/`is` catch it |

Off-screen elements in a lazy list are `selector_not_found`: snapshots hold visible elements only. Scroll with `--until`.

## Capture

- Video: `record start <path.mp4>` and `record stop` (MP4; `record stop` can take 20 s or more to export). Use `--hide-touches` for a faster export.
- `record contact-sheet <video.mp4> --out <sheet.png>` turns a recording into one PNG of the frames where the screen changed.
- Logs: `open … --launch-console <path>` captures the launch console; `logs start`, `logs mark`, `logs path` stream the app's logs.

## Quirks

- **False "covered" on iOS 27 sheets.** Every element in a presented sheet is flagged `[covered]` and `press` by id, label or ref is refused with `target_covered`, although the screenshot shows it. Press its coordinates instead (or `back` to dismiss); do not switch drivers for this.
- **Keyboard.** After `fill`, the keyboard can cover the next control (`behind the visible keyboard`). `keyboard dismiss` fails when the keyboard has no dismiss key; `keyboard enter` closes it.
- **First-run keyboard tip.** A fresh simulator shows "Speed up your typing by sliding your finger…" with Continue inside the keyboard area. `keyboard enter` or a coordinate press on Continue clears it.
- **First tap after a fresh boot dropped** once on iOS 26.5 (exit 0, diff `+0 -0`). The expected-effect check catches it; repeat the action.
- **Navigation bar label can lag.** Right after a push, the `[navigation-bar]` node once still read the previous title ("Long List") while the title text read "Detail 5". Use the title text or an identifier as the landmark.
- **Alerts.** `is visible text="Saved"` missed an alert title that `snapshot` listed as `[text] "Saved"`. Read alerts with `alert` (or `wait text "Saved"`) and close them with `alert accept`.
- The CLI takes one argument per flag. In zsh, a variable holding several flags is not word-split; spell flags out or use an array.
- On iOS 26.5 snapshots print `Simulator AX snapshot unavailable (…)` and fall back to XCTest: slower (0.5–0.7 s) but valid.
- Follow [state diagnostics](../state-diagnostics.md) when a driver call hangs during LLDB work.
- After a blocked call, the next snapshot may print `circuit-disabled`; later commands work.
