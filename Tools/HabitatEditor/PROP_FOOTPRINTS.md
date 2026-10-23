# Tile footprints and Fibu movement — prop rules v1

The shared catalog now has `prop_rules_version: 1`. Props have `placement_grid`, local `[width,depth]` `footprint`, `occupies_grid`, and `blocks_movement`. Layout format remains v1; these are additive fields. Registered catalog rules are authoritative, even when an older instance still says `solid: false`. Newly placed objects also carry snapshots of the flags for native/custom-asset consumers.

| Prop | Local footprint | Blocks Fibu |
| --- | --- | --- |
| Round / young tree | 1×1 | Yes |
| Bush / grass variants | 1×1 | No |
| Bench | 2×1 (1×2 after rotation) | Yes |
| Fountain | 1×1 | Yes |
| Umbrella | 1×1 post, canopy may overhang | No |
| Pergola | 3×3 | No; interior remains traversable |
| Picnic rug | 2×2 | No |
| Hearth | 3×3 | Yes |
| Supplies | 2×2 | Yes |
| Stairs | 1×1 | Existing walkable ramp collision |

A footprint is a placement reservation, independent of whether Fibu can traverse it. Bushes can be walked through but still reserve their tile against placing another prop there. Tree canopies may extend outside a one-tile ground footprint. The original GLB/USDZ geometry, textures and pivots remain unchanged; bench geometry already fits within two tiles.

## Placement

Catalog props always snap to whole tiles, use unit scale and quarter-turn yaw. Odd-width axes center on integer coordinates. Even-width axes center on half-integer coordinates, so a two-wide bench covers two complete tiles rather than halves of three tiles. Rotation swaps width/depth and re-snaps the center to the matching parity. New placement, moving, duplication, inspector edits and rotation all follow this rule. The ghost and selection outline display the footprint; the inspector shows tile dimensions and movement behavior. **Loose snap** still controls fine snapping for unregistered/free assets.

Old layouts load without moving their props. Select an older prop and choose **Align props** to normalize its position/rotation/scale explicitly; move/rotation/edit also normalize a catalog prop when touched. Alignment is undoable and cancels the entire operation if it creates a reservation conflict or leaves the habitat. Original reference habitats remain available. Dense older layouts may need manual rearrangement before all props fit the new reservations.

Props check boundaries and terrain intersection using their footprint instead of canopy width. Their vertical collision/occupancy height retains the actual asset height. A separate support/reachability constraint is not introduced; the editor continues to allow deliberate floating or underground construction.

Open `Assets/Habitats/tile-footprints-study.json` for trees, a bush, both bench orientations, grass and a fountain on a 9×9 floor.

## Navigation / collision

Editor picking stays on layer 2. It is separate from movement collision on layer 1. Trees/benches/blocking props get a box with the local tile footprint and asset height, rotated/scaled with their instance. Bushes/grass get no movement collider. Stairs retain their triangle ramp collision. Canopies never become wide movement obstacles merely because their visual bounds are wider.

`HabitatDocument.blocked_cells()` derives blocked horizontal navigation tiles for the current objects. Entries `[x,surfaceLayer,row]` refer to the CHARACTER FOOT surface layer, not the terrain block below it. A tree planted at Y=1 blocks its ground tile on the terrain's Y=1 top. Legacy yaw/scale are conservatively projected into touched tiles; canonical new props use unit scale/quarter turns. Legacy tilted props should be explicitly aligned before production navigation. The helper does not calculate reachable terrain, ramps, swimming or actor-radius clearance; native pathfinding must combine those rules.

## Local Codex prompt

Fetch `origin/codex/prop-footprints` and integrate its editor/catalog changes without overwriting local work. Read this document and `IOS_HANDOFF.md`. Launch with `./scripts/habitat-editor.sh run`; verify the study layout and run `./scripts/habitat-editor.sh check`.

Update the native habitat loader and Fibu navigation to read the SAME catalog footprints and `blocks_movement` flags. New per-instance snapshots are available for custom/missing catalog assets. Do not use the old `solid: false` snapshots to make registered trees passable. Reserve one tile for each tree and two for each bench, including rotated benches. Trees/benches block walking; bushes/grass do not. Use footprint/trunk collision instead of the full tree canopy mesh. Preserve terrain/stair traversal and apply Fibu's movement-radius clearance to paths. Preserve all existing character, skin, animation and Watch resources.

Verify native collision/pathfinding and GLB/USDZ parity in the simulator, then build both schemes and run relevant app checks. Godot preview collision has been tested here; the current cloud change does not implement or claim native Swift navigation changes.
