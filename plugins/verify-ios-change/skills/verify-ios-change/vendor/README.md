# Vendored LookinServer

`LookinServer.framework` is [QMUI LookinServer](https://github.com/QMUI/LookinServer) tag `1.2.8` (commit `e553d1b`), built for the iOS Simulator by [`../scripts/build-lookinserver.sh`](../scripts/build-lookinserver.sh): `Src/Main` and `Src/Base` compiled with `-DSHOULD_COMPILE_LOOKIN_SERVER=1`, the Swift subspec left out, minimum iOS 26.0, Xcode 27.0 SDK, ad hoc signed.

- **Slices:** arm64 and x86_64 simulator. Only arm64 has run (iOS 26.5 and 27.0 on Apple silicon); x86_64 is checked with `lipo` only.
- **Use:** inject at launch, never into an app that already embeds LookinServer (both servers would take ports 47164–47169):

  ```sh
  SIMCTL_CHILD_DYLD_INSERT_LIBRARIES=<skill>/vendor/LookinServer.framework/LookinServer \
    xcrun simctl launch <udid> <bundle-id>
  ```
- **Rebuild:** `../scripts/build-lookinserver.sh` (clones the tag; set `LOOKIN_TAG` or `MIN_IOS` to change them, or pass a checkout as the second argument).
- **Licence:** the repository's `LICENSE` (copied here) is MIT; its podspecs declare `GPL-3.0`. The source is public at the tag above.
