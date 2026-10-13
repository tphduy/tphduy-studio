# Appium + WebDriverAgent

Appium with the XCUITest driver, which runs WebDriverAgent on the simulator. Bake-off: Appium 3.8.0 with XCUITest driver 12.15.0, Xcode 27.0, iOS 27.0. Reach it over the W3C WebDriver REST API with `curl`; no client library is needed. Record the Appium and driver versions in `tools`.

**Prefer it** when the project already has Appium tests or capabilities.

**Appium goes last.** After Appium had run on the host, AXe's default taps (and XcodeBuildMCP's, through its bundled AXe) reported success and did nothing on every simulator until the Mac was restarted. Run no AXe-based driver after Appium in the same host session. The session also started Xcode's `DeviceHub.app`, set `ConnectHardwareKeyboard = false` for the simulator and left the WebDriverAgent runner installed.

## Setup

- `npx appium driver install xcuitest` (with `APPIUM_HOME` set if you keep it local). Start `npx appium` in the background.
- Launch the installed app with the preparation's capture and injection setup first. Create a session (`POST /session`) with `platformName: iOS`, `appium:automationName: XCUITest`, the selected `appium:udid`, `appium:bundleId`, `appium:autoLaunch: false`, `appium:noReset: true` and `appium:forceAppLaunch: false`. Omit `appium:app` to avoid reinstalling. Verify the app PID is unchanged after session creation. The first session builds WebDriverAgent: 74 s; a warm one takes about 5 s.
- Set `appium:shouldTerminateApp: false` so ending the session (`DELETE /session`) preserves a reused app. Cleanup terminates an app started by this run separately. These [capabilities](https://appium.github.io/appium-xcuitest-driver/latest/reference/capabilities/) control launch, reset and session-end behaviour.

## Observe

| Need | Call | Cost |
|---|---|---|
| Tree (type, frame, identifier, label, value) | `POST /execute/sync` with `mobile: source` and `format: description` | about 2.2k tokens |
| Tree as XML | `GET /source` | about 6k tokens |
| One element | `POST /element`, then `GET /element/{id}/text`, `/attribute/value`, `/displayed`, `/attribute/hittable` | |
| Screenshot | `GET /screenshot` (base64 PNG at device pixels) | |

## Act

- `POST /element/{id}/click`; `POST /element/{id}/value` types (1.3 s).
- Point: W3C `POST /actions` (pointer move, down, up), or `mobile: tap {x, y}`.
- `mobile: scroll` (6–7 s each); `GET /alert/text`, `POST /alert/accept`.

## Wait for the expected effect

Appium has no wait for a value or for absence; the implicit wait covers presence only, and its expiry is the same `no such element` as an immediate miss. Waiting for the expected effect is yours to do; `find` is cheap (about 30 ms).

## Locators

| Strategy | Appium |
|---|---|
| `accessibility id` | `using: accessibility id` (the identifier) |
| `name` | the identifier if the element has one, **else** the label: `name=Increment` is not found when the button has identifier `form.increment` |
| label | `using: -ios predicate string`, `value: label == "Favorite"` |
| `class name` | `XCUIElementTypeButton` and so on |
| point | `POST /actions` or `mobile: tap` |

## Errors (W3C WebDriver vocabulary)

| WebDriver error | Appium |
|---|---|
| `no such element` | HTTP 404 `no such element` with a stack trace (about 450 tokens) and nothing about the current screen; check a landmark |
| `timeout` | None for element waits: the implicit wait ends in `no such element` |
| ambiguous match | Not raised: `/element` returns the first match; `/elements` gives the count |
| `element not interactable` | Not raised for a covered element (the click succeeds); `displayed` and `hittable` return `false`, so check them first. Off-screen elements in a lazy list are `no such element` |
| no effect | Not detected; only the expected-effect check catches it |
| (alerts) | `no such alert` when no alert is open |

## Capture

Video needs `ffmpeg` for `start_recording_screen`; without it use `xcrun simctl io <udid> recordVideo <path.mp4>`, stopped with SIGINT.
