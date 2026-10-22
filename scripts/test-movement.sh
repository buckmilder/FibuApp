#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
check_file=$(mktemp /tmp/fibu-movement-checks.XXXXXX.swift)
trap 'rm -f "$check_file"' EXIT
cat FibuApp/IslandMovement.swift Tests/MovementChecks.swift > "$check_file"
xcrun swift "$check_file"
