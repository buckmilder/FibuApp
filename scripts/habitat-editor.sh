#!/bin/bash
# Uses the same installed Godot app as other projects, with this project explicitly selected.
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
project_path="$repo_root/Tools/HabitatEditor"
godot_bin="${FIBU_GODOT_BIN:-}"
if [[ -z "$godot_bin" ]]; then
  for candidate in /Applications/Godot.app/Contents/MacOS/Godot "$HOME/Applications/Godot.app/Contents/MacOS/Godot"; do
    if [[ -x "$candidate" ]]; then godot_bin="$candidate"; break; fi
  done
fi
if [[ -z "$godot_bin" ]]; then
  godot_bin="$(command -v godot4 || command -v godot || true)"
fi
if [[ -z "$godot_bin" || ! -x "$godot_bin" ]]; then
  echo 'Godot not found. Install Godot 4.6.3 or set FIBU_GODOT_BIN to its executable.' >&2
  exit 1
fi
version="$("$godot_bin" --version)"
if [[ "$version" != 4.6.* ]]; then
  echo "Expected Godot 4.6.x (tested: 4.6.3); found $version. Set FIBU_GODOT_BIN explicitly." >&2
  exit 1
fi
case "${1:-run}" in
  run)
    "$godot_bin" --headless --path "$project_path" --editor --import
    exec "$godot_bin" --path "$project_path" -- "${@:2}"
    ;;
  edit) exec "$godot_bin" --path "$project_path" --editor ;;
  check)
    "$godot_bin" --headless --path "$project_path" --editor --import
    exec "$godot_bin" --headless --path "$project_path" --script tests/run.gd
    ;;
  *) echo 'Usage: scripts/habitat-editor.sh [run [--blank]|edit|check]' >&2; exit 2 ;;
esac
