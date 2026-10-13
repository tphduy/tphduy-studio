#!/bin/sh
# Rebuild the bundled QMUI LookinServer as a universal (arm64 + x86_64) iOS simulator framework, injected with
#   SIMCTL_CHILD_DYLD_INSERT_LIBRARIES=<skill>/vendor/LookinServer.framework/LookinServer xcrun simctl launch <udid> <bundle-id>
# The skill ships the result in ../vendor; run this only to refresh it (new tag, new SDK) or to build elsewhere.
#
# usage: build-lookinserver.sh [OUT_DIR] [SOURCE_DIR]
#   OUT_DIR     where LookinServer.framework and LICENSE go (default: the skill's vendor directory)
#   SOURCE_DIR  an existing LookinServer checkout to build from; otherwise tag $LOOKIN_TAG is cloned
#               into a temporary directory
# Prints the framework binary path on stdout.
set -eu

LOOKIN_TAG=${LOOKIN_TAG:-1.2.8}
MIN_IOS=${MIN_IOS:-26.0}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/../vendor}
SRC=${2:-}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if [ -z "$SRC" ]; then
  SRC=$WORK/src
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$LOOKIN_TAG" https://github.com/QMUI/LookinServer.git "$SRC" >&2
fi

L=$SRC/Src
SDK=$(xcrun --sdk iphonesimulator --show-sdk-path)
# Header paths and sources as in the package's Package.swift (Src/Main and Src/Base); the Swift subspec is left out.
INC=$(find "$L/Main" "$L/Base" -type d | sed 's/^/-I/' | tr '\n' ' ')
SOURCES=$(find "$L/Main" "$L/Base" -name '*.m' | tr '\n' ' ')

for ARCH in arm64 x86_64; do
  # shellcheck disable=SC2086  # INC and SOURCES are space-separated lists; LookinServer paths contain no spaces.
  xcrun --sdk iphonesimulator clang -dynamiclib -fobjc-arc -fmodules -w \
    -target "$ARCH-apple-ios$MIN_IOS-simulator" -isysroot "$SDK" \
    -install_name @rpath/LookinServer.framework/LookinServer \
    -DSHOULD_COMPILE_LOOKIN_SERVER=1 $INC \
    -framework UIKit -framework Foundation -framework QuartzCore \
    $SOURCES -o "$WORK/LookinServer-$ARCH" >&2
done

FW=$WORK/LookinServer.framework
mkdir -p "$FW"
lipo -create "$WORK/LookinServer-arm64" "$WORK/LookinServer-x86_64" -output "$FW/LookinServer"
cat > "$FW/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleExecutable</key>
	<string>LookinServer</string>
	<key>CFBundleIdentifier</key>
	<string>com.qmui.LookinServer</string>
	<key>CFBundleName</key>
	<string>LookinServer</string>
	<key>CFBundlePackageType</key>
	<string>FMWK</string>
	<key>CFBundleShortVersionString</key>
	<string>$LOOKIN_TAG</string>
	<key>CFBundleVersion</key>
	<string>$LOOKIN_TAG</string>
	<key>CFBundleSupportedPlatforms</key>
	<array>
		<string>iPhoneSimulator</string>
	</array>
	<key>MinimumOSVersion</key>
	<string>$MIN_IOS</string>
</dict>
</plist>
EOF
codesign -f -s - "$FW" >/dev/null 2>&1

mkdir -p "$OUT"
rm -rf "$OUT/LookinServer.framework"
mv "$FW" "$OUT/LookinServer.framework"
cp "$SRC/LICENSE" "$OUT/LICENSE"
echo "$(cd "$OUT" && pwd)/LookinServer.framework/LookinServer"
