# Soft grass terrain delivery

Branch: `codex/soft-terrain`. Main instructions and local Codex handoff: `Tools/HabitatEditor/SOFT_TERRAIN.md`.

Updates Forest, Lime and Meadow in the existing Godot builder: broad painted leaves, three earth bands, a raised visual cap and puffy exposed rims over the original connected rounded boundary. Other terrain materials retain their existing artwork. Stable IDs, grid dimensions, props, character, skins, animations, native app and Watch are preserved. Original static module and complete habitat exports are untouched.

- `grass-variants.png`: three changed materials.
- `connected-3x3.png`: no interior rims or grid grooves.
- `raised-terrace.png`: exposed upper levels with no buried grass caps.
- `builder-study.png` / `editor.png`: actual Godot rendering of the 9×9 terrain study.
- `validation.json`: independent exported-asset checks.
- `Assets/Models/SoftTerrain/manifest.json`: paired GLB/USDZ sources, counts and hashes.
- `Assets/Blender/SoftTerrain/Fibu.SoftTerrain.blend`: exact builder mesh exports, organized for review with packed textures.

Use the connected generator for editable layouts. Do not tile the standalone grass singles and expect them to connect; their perimeter is deliberately exposed. Keep the collision mesh at soil height so the visible grass can overlap feet. Native import/playback/foot occlusion and both Xcode scheme builds remain local integration work.
