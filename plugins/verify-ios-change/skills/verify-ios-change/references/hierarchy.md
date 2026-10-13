# Hierarchy inspection

Drivers see only the accessibility tree. The inspector reads the app's own view hierarchy: class names, window frames, visibility, UIKit text, gesture actions and, through `SWIFTUI_PRINT_TREE`, SwiftUI text and shapes. Use it for elements with poor or no accessibility, to find coordinates for a coordinate-based action, and to diagnose.

An inspector the app already embeds (Lookin, FLEX and similar) comes from project context. Never inject LookinServer into an app that already embeds it: both servers would compete for the same ports.

## Launch with the inspector

One `simctl launch` injects LookinServer and turns on SwiftUI's print tree:

```sh
SIMCTL_CHILD_DYLD_INSERT_LIBRARIES="${CLAUDE_SKILL_DIR}/vendor/LookinServer.framework/LookinServer" \
SIMCTL_CHILD_SWIFTUI_PRINT_TREE=1 \
  xcrun simctl launch --console --terminate-running-process <udid> <bundle-id> [launch args…] \
  > "<run-dir>/console.txt" 2>&1
```

- Run it in the background (for example `( … > console.txt 2>&1 & )`). `--console` must stay attached: ending that process ends the app. `--stdout=`/`--stderr=` instead of `--console` wrote nothing on iOS 27.0.
- `console.txt` holds stdout/stderr.
- Drop `SWIFTUI_PRINT_TREE` when the screen is pure UIKit; it is noisy (one SwiftUI screen transition printed 1,600 lines, 300 KB).
- **Attach the driver to this process, do not relaunch from the driver.** A driver relaunch kills the injected process. With agent-device, `open <bundle-id>` without `--relaunch` attaches to the running app, and `close` leaves it running (bake-off: same PID before and after; confirm it in this run).
- If a test case's plan needs a relaunch (a last-resort reset), run this launch again and attach the driver without relaunching, so the inspector stays available.

## Find the PID

Without `--console`, `simctl launch` prints `<bundle-id>: <pid>`; with `--console` it does not. Either of these gives the PID of the running app:

```sh
xcrun simctl spawn <udid> launchctl list | grep <bundle-id>   # first column
python3 -I "${CLAUDE_SKILL_DIR}/scripts/lookin.py" scan                     # injected apps only
```

Several simulators share the host's port range 47164–47169, so identify the server by PID, never by port. `lookin.py scan` lists every server with its PID, app and bundle ID.

## Dump

```sh
python3 -I "${CLAUDE_SKILL_DIR}/scripts/lookin.py" dump --pid <pid> [--print-tree "<run-dir>/console.txt"] [--raw <out.json>]
```

- One line per view: class, window frame in points, hidden and alpha, UIKit text (`UILabel`, `UITextField` value and placeholder), gesture recognizers with their target actions. About 1k–6k tokens per screen; save it to the bundle rather than reading it twice.
- `--print-tree` joins SwiftUI display lists to their hosting views and appends each one's text, images and shapes in window points. Only each hosting view's latest display list is used; views no longer on screen are dropped. An unlabeled SF Symbol shows up as a `shape`.
- Exit codes: 0 ok, 2 no server found (not injected, app not running, or not yet listening: it listens within about 3 s of launch), 3 server error.
- `lookin.py --help` has the rest.

**Frames are window points.** Use a frame's centre for a coordinate-based action only after checking the view is not hidden, has non-zero alpha and is not covered. Flag the action as coordinate-based in the evidence.

`SWIFTUI_PRINT_TREE` is an undocumented debug switch and may change with any iOS release. When it gives nothing, read SwiftUI from the accessibility tree and a screenshot.
