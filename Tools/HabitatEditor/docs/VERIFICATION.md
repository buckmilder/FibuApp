# Verification — 2026-10-23

Environment: Linux cloud workspace, Godot 4.6.3 stable, Compatibility renderer. Desktop window rendered through Xorg dummy display with Mesa llvmpipe. This is not a native Mac run.

- `./scripts/habitat-editor.sh check`: clean asset import and **67 checks, 0 failures**. Covers catalog loading, valid/invalid layouts, signed layers, rotated multicell bounds, rotation restrictions, overlap, missing assets and unknown-field round trips, atomic save/reload, malformed load isolation, exposed-face counts, normals/winding, actual editor commands/history, window pointer routing, fixed-plane brush strokes, preview state/focus restoration, terrain raycasts, and proxy climbing four stair treads.
- `python Tools/HabitatEditor/validate_assets.py` with usd-core: all 23 thumbnails and 14 paired GLB/USDZ props passed hash, grounding, dimensions, finite indexed geometry, packaged dependency and USDZ alignment checks.
- Rendered desktop checks: starter scene, terrain palette/thumbnails/favorites, mouse placement, single selection and outline, keyboard undo, entering preview and seeing the navigation proxy. An actual pointer-routing issue found during this check was fixed and given regression coverage.
- `bash -n scripts/habitat-editor.sh`: passed.

Not verified here: native Mac/trackpad behavior, macOS exported app bundle, SceneKit layout loader, Swift gameplay parity, Xcode builds or iOS performance. No existing app, character, skin or animation files changed. The new native loader is documented as a separate local task, not claimed as delivered.


## Sky & Atmosphere follow-up

- Headless import and **118 checks, 0 failures** after adding the environment module. Added coverage includes all six presets and exported definitions/thumbnails, live light values, environment save/reload, undo/redo, optional cloud motion, Preview continuity, preset save/duplicate/revert, malformed sky settings, panorama copying/application and missing-image fallback.
- All six actual backgrounds were rendered and visually inspected in the Compatibility renderer. Original procedural silhouettes, cloud gradients, night stars/moon, desert layers and icy peaks are visible from the default angled camera. Reference renders are `sky_*.png` in this folder.
- The rendered editor's Sky & Atmosphere window and one-click Starry Night selection were exercised through mouse input; the scene background and lighting changed while construction remained in place. `atmosphere-panel.png` captures that panel.
- No Forward+ volumetric features or distant collision geometry are used. This does not establish an iOS frame-rate/battery measurement, native Mac verification, SceneKit visual parity, or an automatic day/night clock.


## Camera bindings follow-up

130 automated checks pass after the camera update. Added coverage checks horizontal forward/strafe movement, Z/X yaw, C/V distance changes, Shift-drag underside/birdseye orientations, finite camera basis near the pole, gesture release without painting, unchanged authored data, and suppression of camera input during typing/command shortcuts. Both camera views were also rendered and visually inspected (`camera_birdseye.png`, `camera_underside.png`). Native Mac keyboard/trackpad verification remains local.


## Water Block follow-up

165 automated checks pass. New coverage includes single/2×2/stacked/L-shaped/disconnected volumes, no internal faces or perimeter grids, shoreline/wall detection, winding and depth interpolation, depth independent of global Y, unchanged-body cache reuse, actual editor placement/move/duplicate/delete/history, body style isolation, water persistence, visibility/picking under water, preview collision separation and sky-linked foam lighting. Nearby picking was made more precise while retaining long-distance queries for tall construction.

Actual Compatibility renders were inspected in daylight and night: the shallow shelf/deep floor remain visible, outer volume walls are translucent, and broken pale foam follows water/terrain boundaries. Reference images are water-garden.png, water-night.png, water-study.png and water-editor.png. The asset integrity helper validates 24 thumbnails and the unchanged 14 paired props. Native Mac and SceneKit/iPhone rendering/performance remain local verification tasks.
