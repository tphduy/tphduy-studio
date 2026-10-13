# XcodeBuildMCP

[getsentry/XcodeBuildMCP](https://github.com/getsentry/XcodeBuildMCP): an MCP server (and CLI) for building, running and driving simulator apps. It bundles AXe and the FBSimulatorControl frameworks. Bake-off: 2.7.0 on Xcode 27.0, iOS 27.0, through its MCP tools over stdio. Record its version in `tools`.

**Prefer it** when the app's logs matter (it captures them per launch without being asked) or when the run already uses it to build. It has no coordinate tap over MCP; use its bundled `axe` for that.

## Setup

- Run it with `npx xcodebuildmcp`; the server starts in under a second (`npx xcodebuildmcp mcp`). The CLI exposes the same tools, but the stateful UI tools need its daemon.
- **UI tools are off by default.** Set `XCODEBUILDMCP_ENABLED_WORKFLOWS=simulator,ui-automation` (add `debugging` for LLDB tools). Set `XCODEBUILDMCP_SENTRY_DISABLED=true` to turn off its error reporting.
- `session_set_defaults` (simulator UDID and bundle ID), then `install_app_sim` and `launch_app_sim`.
- Tool definitions cost about 5k tokens of input schemas; much more if the client loads output schemas into context.

## Observe

| Need | Tool | Cost |
|---|---|---|
| Actionable targets (role, label, value, identifier, ref, allowed actions) | `snapshot_ui` | 750–830 tokens. Static text and frames are not listed |
| Find an element by selector | `wait_for_ui` with `identifier`, `label`, `role` or `value` | 330–880 tokens |
| Screenshot | `screenshot` (inline image) | |
| Logs | `launch_app_sim` writes stdout, stderr and `os_log` to `~/Library/Developer/XcodeBuildMCP/workspaces/<key>/logs/` | |

## Act

`tap`, `type_text`, `touch` and `long_press` take only an `elementRef`. To act by identifier: `wait_for_ui exists identifier=<id>` returns the ref, then `tap <ref>`. `swipe` takes a scroll ref; `gesture` has presets only. For a point, run the bundled `axe tap -x <x> -y <y> --udid <udid>` and note that AXe's caveats apply (see `axe.md`).

## Wait for the expected effect

`wait_for_ui` with `exists`, `gone`, `enabled`, `focused`, `textContains` or `settled`, and a timeout.

## Locators

| Strategy | XcodeBuildMCP |
|---|---|
| `accessibility id` | `wait_for_ui identifier=…`, then the ref |
| label | `wait_for_ui label=…` |
| `class name` | `wait_for_ui role=…` |
| point | not over MCP; bundled `axe` |
| ref | `e50` from `snapshot_ui` or `wait_for_ui`; stale after the screen changes |

## Errors (W3C WebDriver vocabulary)

Failures come back with `isError: true`, a `Code:` and a `Recovery` block.

| WebDriver error | XcodeBuildMCP |
|---|---|
| `no such element` | `ELEMENT_REF_NOT_FOUND` for a stale or unknown ref. A selector that matches nothing surfaces only as `WAIT_TIMEOUT` |
| `timeout` | `WAIT_TIMEOUT`: `Timed out after 3000ms waiting for UI predicate 'exists'.` It names the predicate, not the screen; read a landmark yourself |
| ambiguous match | Not applicable: actions take one ref. `wait_for_ui` returns every match |
| `element not interactable` | `TARGET_NOT_ACTIONABLE` when the ref does not list the action. A classification, not a hit test: covered elements are tapped anyway, and a tappable image with action `none` is refused (use `touch`) |
| no effect | Not detected (`tap` reports success); `wait_for_ui` catches it |

## Capture

`screenshot`; `record_sim_video` start and stop (MP4).

## Quirks

- Covered elements are tapped and success is reported; the expected-effect check catches it.
- Every action is a round trip with 250–900 tokens of status, next steps and tips; `tap` takes 2.5–4 s.
- Its bundled AXe drops default-style taps after Appium has run, like standalone AXe.
