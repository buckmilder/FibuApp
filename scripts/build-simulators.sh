#!/bin/bash
set -u
cd "$(dirname "$0")/.." || exit 1
if [ -z "${DEVELOPER_DIR:-}" ] && [ -d /Applications/Xcode.app/Contents/Developer ]; then
  export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
fi
if ! xcodebuild -version; then
  echo 'Install and open Xcode, complete first-launch setup, and install iOS and watchOS components.' >&2
  exit 1
fi
mkdir -p build/logs
result=0
for scheme in FibuWatch FibuApp; do
  destination='generic/platform=watchOS Simulator'
  if [ "$scheme" = FibuApp ]; then destination='generic/platform=iOS Simulator'; fi
  if xcodebuild -project FibuApp.xcodeproj -scheme "$scheme" -configuration Debug \
    -destination "$destination" -derivedDataPath build/DerivedData \
    CODE_SIGNING_ALLOWED=NO build > "build/logs/$scheme.log" 2>&1; then
    echo "$scheme: BUILD SUCCEEDED"
  else
    echo "$scheme: BUILD FAILED (build/logs/$scheme.log)" >&2
    tail -n 60 "build/logs/$scheme.log" >&2
    result=1
  fi
done
exit "$result"
