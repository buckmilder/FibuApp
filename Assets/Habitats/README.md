# Authored habitats

Editable habitat JSON belongs here and should be committed with matching registry/assets. `terrace-starter.json` is an editable example for the Godot desktop creator; it does not replace the app's three existing habitat exports.

Run `./scripts/habitat-editor.sh run` from the repository root. Use Save As to create your own layout. See `Tools/HabitatEditor/SCHEMA.md` and `IOS_HANDOFF.md`. Native Swift layout loading is a separate local integration task and is not yet implemented.

Layouts now include `environment` sky/lighting settings. Custom named sky presets belong in `SkyPresets/`; imported panoramic artwork belongs in `SkyArt/`. Commit referenced art along with layouts. These directories are created when used. No automatic day/night clock is included.

`water-garden.json` is a composed Water Block example; `water-study.json` exercises multiple modular water arrangements. These are editable examples for the desktop tool, not native app replacements. See `Tools/HabitatEditor/WATER.md` before implementing water in the Swift loader.
