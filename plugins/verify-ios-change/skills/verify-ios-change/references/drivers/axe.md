# AXe

[cameroncooke/AXe](https://github.com/cameroncooke/AXe): a single CLI that talks to the simulator directly, with no runner or daemon. Bake-off: 1.8.0 on Xcode 27.0, iOS 26.5 and 27.0. Record `axe --version` in `tools`.

**Prefer it** for quick coordinate or single-element actions without a runner. Its observation is the most expensive of the four drivers, and it reports success for taps that did nothing, so verify every tap.

**Never run AXe after Appium has run in the same host session.** After Appium, every default-style AXe tap printed success and changed nothing, on every simulator, surviving a simulator reboot, until the Mac was restarted.

`axe <command> --help` gives exact flags.

## Setup

Homebrew (`brew install cameroncooke/axe/axe`). Nothing to build. AXe neither installs nor launches apps: use `xcrun simctl install` and `simctl launch`. Every command takes `--udid <udid>`.

## Observe

| Need | Command | Cost |
|---|---|---|
| Whole accessibility tree | `describe-ui` (JSON: role, `AXLabel`, `AXUniqueId`, `AXValue`, frame) | about 32k tokens (130 KB), mostly empty `Group` wrappers |
| One element | `describe-ui --point x,y` | small |
| Screenshot | `screenshot --output <path>` (device pixels, 1206×2622 on iPhone 18 Pro) | |

Filter `describe-ui` output down before reading it.

## Act

- `tap --id <identifier>`, `tap --label <label>`, `tap --value <value>`; narrow with `--element-type`. `tap --id` reads the tree and then taps (1.1–1.5 s).
- `tap -x <x> -y <y>` taps a point (0.65 s).
- `type <text>` types into the focused field.
- `swipe --start-x … --start-y … --end-x … --end-y …` scrolls. There is no scroll-until.
- `touch`, `button`, `key`, `gesture` and `batch` cover the rest.
- `--tap-style physical` (touch down and up) still landed when default-style taps were being dropped.

## Wait for the expected effect

AXe has no wait of its own. `tap --wait-timeout` only waits for the target to appear before tapping, and its expiry prints the same message as an immediate miss. Waiting for the expected effect is yours to do.

## Locators

| Strategy | AXe |
|---|---|
| `accessibility id` | `--id` (matches `AXUniqueId`) |
| label | `--label` |
| value | `--value` |
| `class name` | `--element-type`, as a narrowing filter |
| point | `-x -y` |

Back buttons usually have no identifier: `tap --label <previous title>`.

## Errors (W3C WebDriver vocabulary)

| WebDriver error | AXe |
|---|---|
| `no such element` | `No accessibility element matched --id '…'`, `No tap performed.`, exit 1. Also what a wrong screen looks like; check a landmark |
| `timeout` | None of its own: `--wait-timeout` expiry prints the `no such element` message |
| ambiguous match | `Multiple (N) accessibility elements matched …`, `No tap performed.`, exit 1 |
| `element not interactable` | Not detected: a covered element is tapped at its point (landing on whatever covers it) and success is reported. Off-screen elements are `no such element` |
| no effect | Not detected (exit 0). Only the expected-effect check catches it |

## Capture

- Video: `record-video --udid <udid> --output <path.mp4>` (H.264, 10 fps by default). Stop it with SIGINT, not SIGKILL, or the MP4 is not finalised.
- `xcrun simctl io <udid> screenshot` and `recordVideo` also work.

## Quirks

- Default-style taps can be dropped silently (the Appium interaction above). Every tap needs its expected-effect check; retry a dropped tap with `--tap-style physical`.
- #71 (dropped first tap on Xcode 27) did not reproduce in 8 trials, but keep the check.
- For debugger-related hangs, follow [state diagnostics](../state-diagnostics.md).
