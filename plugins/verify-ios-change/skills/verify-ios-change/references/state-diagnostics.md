# State diagnostics

Use LLDB to inspect app state and code behaviour: persistence, launch arguments, variables and breakpoints. It can also dump UIKit hierarchy without relaunching. LookinServer's launch and dump recipes live in [hierarchy inspection](hierarchy.md).

## Attach and resume

Launch with `simctl` or the driver without an attached debugger. Only one debugger can own the process; an existing Xcode debugger blocks standalone LLDB attachment. Record that conflict through the bundle reference's capability rules.

Attachment initially stops the app; an attached process can run after `continue`. For inspection or setup, complete diagnostics, detach and confirm the app resumed before driver actions. For breakpoint/watchpoint observation during an interaction, keep LLDB attached and continue before issuing the driver action. Coordinate each stop, capture and continuation. A driver call waiting on a stopped process remains pending; let it finish after continuation rather than issuing a duplicate. A hung call warrants checking `ps -o stat= -p <pid>` for `T` (stopped).

After diagnostics, remove run-owned breakpoints, commands and hooks, detach and confirm the process is running before ordinary driver work or leaving the app for inspection.

## Preparation readiness

For every preparation, attach to the running app, evaluate a basic process fact, and detach:

```sh
xcrun lldb --batch \
  -O 'settings set stop-disassembly-display never' \
  -p <pid> \
  -o 'expr -l objc -- @import Foundation' \
  -o 'expr -l objc -O -- [[NSProcessInfo processInfo] arguments]' \
  -o detach
ps -o stat= -p <pid>
```

Save output in the run directory. Pass only when attachment, expression output and detach are confirmed, and the app still exists with a non-stopped process state. Read the expression output: batch exit status alone is insufficient. Record a separate LLDB check; use the evidence bundle's blocker/limitation rules on failure. A successful check proves debugger readiness; feature-specific state checks belong in verification.

## State and code inspection

Derive expressions, symbols and object identities from the case requirements, current build and live process; addresses expire on relaunch. Capture commands and actual outputs. Before mutating prerequisite state, follow [advanced verification](advanced-verification.md) through SKILL.md's effort and exhausted-recovery gate; inspect before and after the mutation and verify that the intended implementation executes.

For UI calls, use a suitable main-thread stop with an initialized scene; avoid synchronous dispatch onto a stopped thread. If expression evaluation or object access is unreliable, preserve the error and choose a supported inspection mechanism or, when advanced recovery is eligible, a temporary source hook instead of guessing memory offsets.

Consult [LLDB's command tutorial](https://lldb.llvm.org/use/tutorial.html) and local `help` for expression and breakpoint syntax; app-specific commands belong in the run's evidence.

## UIKit hierarchy dump

One batch, then detach:

```sh
xcrun lldb --batch \
  -O 'settings set stop-disassembly-display never' \
  -p <pid> \
  -o 'expr -l objc -- @import UIKit' \
  -o 'expr -l objc -O -- [[[UIApplication sharedApplication] keyWindow] recursiveDescription]' \
  -o 'expr -l objc -O -- [[[[UIApplication sharedApplication] keyWindow] rootViewController] _printHierarchy]' \
  -o detach
```

- `keyWindow` misses other windows (alerts, sheets in their own scene). For every window, iterate `[[UIApplication sharedApplication] connectedScenes]` and each scene's `windows`.
- Frames in `recursiveDescription` are relative to the superview. For window points: `expr -l objc -- (CGRect)[(UIView *)<address> convertRect:[(UIView *)<address> bounds] toView:nil]` (needs the `@import UIKit` first).
- A dump takes 6–14 s, during which the app is frozen. Text is UIKit only, as with LookinServer.
- Apple's own apps refuse the attach. No debug build or dSYM is needed for a developer-built simulator app.
