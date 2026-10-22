#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
check_file=$(mktemp /tmp/fibu-skin-checks.XXXXXX.swift)
result_file=$(mktemp /tmp/fibu-skin-results.XXXXXX.json)
trap 'rm -f "$check_file" "$result_file"' EXIT
cat FibuApp/FibuSkin.swift Tests/SkinChecks.swift > "$check_file"
xcrun swift "$check_file" > "$result_file"
python3 Tests/SkinAssets.py "$result_file"
