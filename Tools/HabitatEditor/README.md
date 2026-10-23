# Fibu Habitat Creator

A separate Godot 4.6 desktop authoring project. Fibu remains a native Swift/SceneKit app. No Grimoire files, Swift code, Xcode settings, character, skins, animations, or existing habitat exports are changed. Tested with Godot **4.6.3**, Blender 4.3.2, and usd-core 26.11.

## Launch on Mac

From the FibuApp repository:

```sh
./scripts/habitat-editor.sh run
./scripts/habitat-editor.sh run --blank
./scripts/habitat-editor.sh edit
./scripts/habitat-editor.sh check
```

The launcher finds `/Applications/Godot.app`, `~/Applications/Godot.app`, or `godot4`/`godot` on PATH. For another installation:

```sh
FIBU_GODOT_BIN="/path/to/Godot.app/Contents/MacOS/Godot" ./scripts/habitat-editor.sh run
```

It explicitly selects this project, imports its assets, and opens the standalone desktop window. Opening `Tools/HabitatEditor/project.godot` in Godot and pressing F6 on `HabitatEditor.tscn` also works. The first import/start can take longer while textures and shaders compile. There is no Xcode or simulator dependency. No macOS application bundle has been exported yet; source-project launch is the supported workflow.

The starter garden opens initially; New creates an empty habitat. Save As before modifying the starter if you want to keep it intact. Open defaults to `Assets/Habitats/`. The editor never commits or pulls automatically. Push authored JSON and any newly registered assets through the normal Git workflow; local Codex fetches cloud changes. Godot reimports saved asset/script changes, but a running standalone session may need restarting to use code changes. No background Git automation is installed.

## Building

- Choose a terrain material using the search/category palette. **B** activates Place; click repeatedly or drag to paint. A stroke keeps its initial face plane, preventing accidental towers. Hover outlines are green/red for valid/invalid placement.
- Blocks snap to one-meter cells, with no fixed positive/negative vertical layer limit. **R** rotates props in 90-degree increments. Solid footprints must fit inside the 9×9 boundary; decorative anchors must fit, but foliage can overhang.
- Hover a top/side/bottom face to extend terrain. Hold **Alt** to force placement on the current build plane. **[ / ]** changes that layer; the layer field accepts values beyond its initial range.
- **X** erases terrain; Ctrl-click in Erase deletes a picked prop. **V / Esc** selects; Shift-click toggles multiselection. Drag empty space to box-select visible instance centers.
- **G** preserves the selection and enters Move: click the destination surface/plane to translate the group. Terrain movement uses whole-cell offsets; props can be positioned precisely in Inspector. Alt targets the build plane.
- **R** rotates selected props around their own pivots. Terrain cubes have no directional orientation. **Cmd/Ctrl-D** duplicates one cell to the right, subject to collision rules. **Delete** removes selection.
- **Cmd/Ctrl-Z**, **Shift-Cmd/Ctrl-Z** (or Ctrl-Y) undo/redo; a stroke/group operation is one history entry. History is capped at 100 snapshots.
- Trees, grass and furniture ground on terrain surfaces, with optional 0.25m X/Z snapping. Props can overlap intentionally. The initial solid prop is a stair; furniture/foliage are decorative, not gameplay obstacles.
- Use the selection dropdown to select props obscured by other objects. Inspector edits position, rotation, scale and name. Solid stairs are scale-locked and restricted to yaw rotation.
- Cutaway hides terrain above the chosen layer and props above that layer + 1. Hidden terrain is excluded from picking. This is an editing view; saved cells are retained. Grid and layer plane are optional.
- The spawn button sets spawn above the **last viewport placement cursor**, not the toolbar click location. A pale blue outline marks it. Preview to check grounding.

## Camera and preview

Right-drag orbits; middle-drag or Shift-right-drag pans; wheel zooms. Focus/**F**, Frame, Top, Isometric and Reset provide view presets. Fly enables WASD/QE translation in the camera basis. Navigation is not restricted to ground level.

**Tab / Preview** runs a small capsule navigation proxy: WASD/arrows, Space jumps, Esc returns. Quarter-height stairs auto-step; solid terrain/steps collide. Decorative furniture, water and gameplay hazards are **not** a navigation validation system. Preview events never edit authored data. Camera and selection restore on return. This is not the native Swift player controller and does not test Fibu animations or SceneKit rendering.

**H / Help** shows shortcuts. Keyboard editing shortcuts yield to text fields/dialogs.

## Assets and adding more

`assets/catalog.json` registers nine terrain materials and fourteen individual props. GLBs embed their maps; terrain maps are in `assets/textures/`. Thumbnails are actual rendered asset previews. IDs are stable and must not be renamed after layouts refer to them.

To add a prop:

1. Export a meter-scale Y-up GLB to `assets/models/`, horizontal center at the origin, bottom at Y=0. Export a matching USDZ into `Assets/Models/EditorKit/`.
2. Add a catalog entry with a unique `id`, `name`, `category`, `kind: "prop"`, `godot`/`ios` references, dimensions `[X,Y,Z]`, footprint, allowed rotations, scale range and `solid` classification. Add `assets/thumbnails/<id>.png`.
3. Reimport/relaunch. Browser categories populate from the catalog. Check matching transforms and collision dimensions before authoring layouts.

Current solid construction uses grid/face alignment and yaw rotations. Arbitrary connector/socket snapping, sloped collision-aware decorative placement, and scripted asset property editors are not implemented. Asset `properties` and unknown fields survive JSON round trips for future tools.

Reproduce the included conversions (not needed to run the editor):

```sh
blender -t 4 --background --factory-startup --python Tools/HabitatEditor/prepare_assets.py
blender -t 4 --background --factory-startup --python Tools/HabitatEditor/render_thumbnails.py
TMPDIR=/tmp python Tools/HabitatEditor/export_ios_assets.py
python Tools/HabitatEditor/validate_assets.py
```

The Blender converter needs the existing ignored HabitatWorlds generated JSON memberships. If absent, first run `FIBU_SKIP_RENDER=1 blender -t 4 --background --factory-startup --python Assets/Blender/HabitatWorlds/build.py`. Conversion scratch is ignored. USD tools need `usd-core`; Blender supplies its own Python. Original sources and runtime exports remain untouched.

## Sky & Atmosphere

Open **Sky & Atmosphere** from the toolbar. Six one-click thumbnail presets provide original procedural skies, clouds, layered distant landscapes and matching sun/ambient/fog settings: Sunny Highlands, Golden Sunset, Starry Night, Misty Forest, Desert Haze and Frozen Twilight.

Edit sky/horizon/lower colors, sun heading/elevation/color/energy, ambient color/energy, clouds, fog, landscape type/tint/visibility, background rotation and horizon offset. Settings preview immediately and are stored in the habitat's `environment`; no second copy of habitat geometry is needed for a different mood. Color-picker edits form one undo entry; numeric changes are undoable. **Revert session changes** restores the environment present when the panel opened.

Save or duplicate named custom presets under `Assets/Habitats/SkyPresets/`. Saving over an existing filename requests confirmation. Preset definitions are copied into habitats, so editing a saved preset does not unexpectedly alter other layouts. Commit custom presets if you want to share them.

**Import panorama** copies your equirectangular PNG/JPEG/HDR/EXR into `Assets/Habitats/SkyArt/` with a content-derived filename. Commit the art with its habitat. Panorama mode replaces procedural clouds/landscapes while retaining coordinated lighting/fog; **Use procedural sky** restores procedural mode. Missing art falls back to procedural rendering and retains the original reference.

Optional slow cloud movement is off by default. No automatic clock or day/night cycle is implemented. These are editable mood starting points; a future native cycle can interpolate environment values while keeping geometry unchanged. See [ATMOSPHERE.md](ATMOSPHERE.md) for the data contract and Swift integration limits.

## Data and architecture

See [SCHEMA.md](SCHEMA.md) and [IOS_HANDOFF.md](IOS_HANDOFF.md). Authored content lives in `Assets/Habitats/`, separate from `user://` editor preferences and test files. Open/Save As use normal file dialogs, retain unknown fields/missing IDs, reject malformed and unsupported-version files, and write with a same-directory temporary file then atomic rename. Unsaved changes are guarded on New/Open/Close.

- `scripts/document.gd`: portable data, validation, placement checks and serialization.
- `scripts/registry.gd`: asset loading/material cache.
- `scripts/atmosphere.gd` and `assets/skies/stylized.gdshader`: environment presets, background rendering and coordinated lighting.
- `scripts/terrain.gd`: occupancy-driven exposed boundary, shared smoothing, normals and UVs.
- `scripts/editor.gd`: desktop UI, commands/history, placement, camera and preview.
- `tests/run.gd`: model/mesh checks and actual editor command/physics tests.

Terrain rebuilds occur after edits, not idle mouse movement. This initial implementation rebuilds the visible habitat per edit, with shared texture/material caches. Incremental chunk rebuilds are a future optimization; unlimited vertical placement is not a promise of unlimited memory/performance. Diagonally touching voxels and complex cavity intersections need more visual coverage before production terrain parity is guaranteed.

## Existing habitats

Garden, pond and camp remain unchanged references in `Assets/Models/` and `Assets/Handoff/HabitatWorlds/`. The editable Terrace Garden is a new starter, not a replacement. The three older scenes contain fused terrain and many individually generated flowers, lantern parts, decks, water, fire and architectural pieces. They are not automatically decomposed editable templates. Exact template conversion needs their generator to emit logical cell/instance placements, plus registration of remaining composite props. Representative benches, pergola, picnic setting, fountain, umbrella, hearth and supplies are already reusable here.

## Verification and limits

Run `./scripts/habitat-editor.sh check`. Linux headless tests and desktop rendering/input checks are recorded in the handoff. Native Mac launch, trackpad ergonomics, and native iOS loader/rendering verification remain for local Codex. No iOS application changes were made, so no Xcode build is claimed. This tool does not yet ship an iOS loader, in-app editor, foliage brush, arbitrary connector snapping, automatic material transitions, enemies, events, or visual scripting.
