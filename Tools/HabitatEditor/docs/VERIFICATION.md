# Verification — 2026-10-23

Environment: Linux cloud workspace, Godot 4.6.3 stable, Compatibility renderer. Desktop window rendered through Xorg dummy display with Mesa llvmpipe. This is not a native Mac run.

- `./scripts/habitat-editor.sh check`: clean asset import and **67 checks, 0 failures**. Covers catalog loading, valid/invalid layouts, signed layers, rotated multicell bounds, rotation restrictions, overlap, missing assets and unknown-field round trips, atomic save/reload, malformed load isolation, exposed-face counts, normals/winding, actual editor commands/history, window pointer routing, fixed-plane brush strokes, preview state/focus restoration, terrain raycasts, and proxy climbing four stair treads.
- `python Tools/HabitatEditor/validate_assets.py` with usd-core: all 23 thumbnails and 14 paired GLB/USDZ props passed hash, grounding, dimensions, finite indexed geometry, packaged dependency and USDZ alignment checks.
- Rendered desktop checks: starter scene, terrain palette/thumbnails/favorites, mouse placement, single selection and outline, keyboard undo, entering preview and seeing the navigation proxy. An actual pointer-routing issue found during this check was fixed and given regression coverage.
- `bash -n scripts/habitat-editor.sh`: passed.

Not verified here: native Mac/trackpad behavior, macOS exported app bundle, SceneKit layout loader, Swift gameplay parity, Xcode builds or iOS performance. No existing app, character, skin or animation files changed. The new native loader is documented as a separate local task, not claimed as delivered.
