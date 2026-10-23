# Local Codex handoff — desktop habitat editor

Integrate `codex/habitat-editor`, preserving local Swift changes. This branch builds on the habitat-only delivery and adds a separate Godot project plus new standalone prop assets/layouts. It does not change Fibu, skins, animations, native app behavior, Xcode resources, or the current habitat catalog. Do not merge the older mixed experimental asset branch.

## Run the tool first

1. Use Godot 4.6.3 (4.6.x launcher requirement). Run `./scripts/habitat-editor.sh check`, then `./scripts/habitat-editor.sh run` on the Mac. No simulator is required.
2. Check mouse/trackpad navigation, resize the window, paint/erase, stack, use Alt + negative build layers, place a tree, move/rotate/duplicate/delete selections, undo/redo, Save As, reload and preview stairs. Check unsaved-change prompts. Source launch is supported; a signed standalone Mac bundle is not yet produced.
3. Author files into `Assets/Habitats/`, commit and push through the normal workflow. Do not enable background Git syncing. The shipped starter may be saved as a new habitat; the original three complete habitats remain references.

## Next native task (not implemented in this cloud delivery)

Implement a Swift decoder/loader for the format documented in `SCHEMA.md`. First prove `Assets/Habitats/terrace-starter.json` renders the same terrain, stairs and prop placements. Preserve existing app behavior until this loader is ready; do not silently replace current habitats with an unverified authoring layout.

- Bundle authored layout JSON and the shared `Tools/HabitatEditor/assets/catalog.json` (or a generated runtime subset retaining identical IDs), required `Assets/Models/EditorKit/*.usdz`, and terrain maps. Asset paths in catalog are repository-relative references, not paths to open on an installed device; map them to bundled resource URLs.
- There are nine terrain themes and fourteen paired GLB/USDZ props. `Assets/Models/EditorKit/manifest.json` records matching export hashes. Existing complete habitat USDZs and Fibu.Soft.usdz are untouched.
- Reconstruct connected terrain using `fibu-rounded-boundary-v1`. See the complete algorithm and **Godot/SceneKit winding difference** in SCHEMA.md. Do not substitute the old pre-beveled single cubes. If preferred, add a baking step from the canonical algorithm to an iOS mesh rather than duplicating the runtime generator.
- Coordinates match prior habitat exports: Y-up meters, row = -Z. Apply a common scene scale at the habitat root. Compose Euler rotations in YXZ order; keep asset bottom pivots and the character's own grounding distinct.
- Keep grid bounds, surface height, collision and reachability separate. Terrain/stairs collide in desktop proxy preview; other current props are decorative. The editor does not define safe water/fire behavior or native pathfinding.
- Validate versions, finite transforms, duplicate cells/IDs and missing assets. Keep unsupported fields when implementing a future native editor. Avoid clearing unrelated user preferences or skin choices.
- Run both existing simulator scheme builds and movement/camera/skin checks after native implementation. Visually verify all elevations, props, lighting, character scale and stair contact. Swift loading and simulator behavior have not been tested in Linux.

Desktop Preview is a capsule navigation proxy, not the Swift controller or an animation test. No automatic day/night cycle is included. Sky & Atmosphere is now authored environment data: preserve it when loading layouts and read `ATMOSPHERE.md`. It is not baked into terrain colors. Godot sky shaders do not run directly in SceneKit; native rendering requires a port or panoramic baking step plus matching light/fog settings.

## Scope remaining

Arbitrary connector/socket snapping, transform gizmos, advanced foliage brushes, material transitions, exact decomposition of the three reference habitats, and an exported Mac app bundle remain future work. Basic grid/face snapping, inspector transforms and click-destination group movement are implemented. Review the README before extending the asset schema.


## Sky update included before handoff

The same branch now includes six procedural environments and a Sky & Atmosphere panel. Check preset thumbnails, switching, color/numeric edits, custom preset save/duplicate/revert, panorama imports and habitat save/reload. The starter includes explicit Sunny Highlands settings. `assets/skies/presets.json` supplies portable reference defaults; `ATMOSPHERE.md` describes keys, coordinate conventions, background placement and SceneKit integration. Preview shares the same environment renderer. This does not implement the native app's sky or its automatic day/night clock.


## Updated camera controls

WASD now translates the authoring camera without enabling Fly, Z/X rotates left/right, C/V zooms in/out, and Shift-left-drag or right-drag orbits above and below the habitat. Middle-drag pans; Q/E adjusts height. Tool shortcuts formerly using V/X are now 1/Esc Select and 3 Erase. Verify these on the Mac, including text-field focus and Cmd-Z/Cmd-S. Preview retains WASD proxy movement.


## Water Block update

The editor now registers one Water Block and includes `water-garden.json` and `water-study.json` as optional authoring examples. Verify Water-category placement/drag painting, stacks, foam joins, selection, connected-body appearance edits, undo/redo and save/reload. Use Show/Hide water to edit the submerged floor. Preview should show the volume while keeping the existing proxy's solid collision mask unchanged.

Read `WATER.md` before native layout work: water is classified by the asset registry and is **not ordinary solid terrain**, even though it lives in the shared logical grid list. Preserve `water_styles` and cell style references. There is no static water USDZ to add; native code needs the documented boundary generator and matching transparent shader/foam treatment. Godot GLSL and SceneKit material shaders are separate implementations. No automatic food, health, swimming or waterfall behavior is included. Existing native habitat exports and Fibu remain untouched.

## Tile prop rules

The catalog now carries `prop_rules_version: 1`, `placement_grid`, `footprint`, `occupies_grid`, and `blocks_movement`. Implement the placement/collision/navigation semantics in [PROP_FOOTPRINTS.md](PROP_FOOTPRINTS.md). These supersede the prior assumption that all foliage/decor props are nonblocking. Bushes remain traversable; trees and benches now block their logical ground footprints. Godot's preview behavior does not automatically update the native app.
