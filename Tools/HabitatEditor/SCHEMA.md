# Habitat layout contract v1

Files are UTF-8 JSON with `format: "fibu-habitat"` and `version: 1`. Engine-specific resources are resolved through the catalog, never serialized into habitat objects. JSON numbers may reload as floats; integer-valued cell coordinates retain their integer semantics. Unknown JSON fields are preserved. Unsupported versions are rejected without changing the current document or original file.

## Coordinates

All transforms are **meters, right-handed, Y-up**. A terrain cell `[x, layer, row]` maps to a unit cube with bottom-center `[x, layer, -row]`. It spans X `[x-.5,x+.5]`, Y `[layer,layer+1]`, Z `[-row-.5,-row+.5]`. X/row indices are nonnegative within width/depth; layers are signed integers with no fixed editor range. A 9×9 grid spans X `[-.5,8.5]` and Z `[-8.5,.5]`.

Blender conversion is `(x,y,z) -> (x,z,-y)`. The same conversion is used by existing USDZ habitat exports. GLB assets use their standard Y-up transforms. Object position is its horizontal-centered, bottom-grounded asset pivot. Object rotations are **degrees**, Euler **YXZ order**, matching Godot Node3D defaults. In Swift compose `Ry * Rx * Rz` for column-vector transforms. Positive yaw follows the right-hand rule; do not negate it again. Scale is a positive local XYZ vector.

## Fields

```json
{
  "format": "fibu-habitat",
  "version": 1,
  "id": "stable-habitat-id",
  "name": "My Garden",
  "grid": {"width": 9, "depth": 9, "cell_size": 1},
  "coordinates": "Y-up meters; cell [x,layer,row] maps to [x,layer,-row]",
  "terrain": [{"cell": [0, 0, 0], "asset": "terrain_meadow"}],
  "objects": [{
    "id": "stable-instance-id",
    "asset": "foliage_round_tree",
    "position": [0, 1, 0],
    "rotation": [0, 90, 0],
    "scale": [1, 1, 1],
    "solid": false,
    "dimensions": [1.8, 2.7, 1.8],
    "properties": {}
  }],
  "spawn": [0, 1.03, 0],
  "environment": {}
}
```

Example dimensions above are illustrative; the catalog is authoritative. `solid` and `dimensions` in instance records support editor occupancy checks and should agree with the registered asset. Gameplay should apply its own approved collision rules. Environment settings are documented in [ATMOSPHERE.md](ATMOSPHERE.md). They are a versioned primitive JSON dictionary, not a Godot resource. Empty legacy environment objects resolve to Sunny Highlands; the starter now stores explicit settings. Names and properties are optional. New IDs use random 96-bit hexadecimal strings; other stable strings are accepted.

`spawn` is the suggested character **foot** position, before native character grounding adjustments. Width and depth are configurable in data; cell size is currently required to be 1 because the catalog has one-meter geometry. The editor rejects other cell sizes explicitly rather than silently mis-scaling assets.

## Terrain algorithm: fibu-rounded-boundary-v1

The registry selects a material theme per terrain ID. Terrain is logical occupancy, not an array of rounded model instances.

1. Convert cell indices to integer world lattice `(x,layer,-row)`.
2. Emit each cube face only when its face-adjacent neighbor is unoccupied, regardless of material. Cube origin is lattice + `(-.5,0,-.5)`.
3. Subdivide each exposed face into 4×4 quads. Weld vertices globally by exact quarter-meter integer lattice coordinates; no epsilon welding. Connect each quad's four perimeter edges into a deduplicated vertex-neighbor graph.
4. Run **two simultaneous Laplacian passes**, each `p_next = lerp(p, average(unique_edge_neighbors), 0.35)`. Use the full surface across materials. This rounds exposed contours while preserving coplanar regions. Do not smooth each cube separately.
5. Accumulate outward quad normals from `cross(p1-p0,p2-p0)` onto welded vertices, then normalize. Emit clockwise triangles `(0,2,1)` and `(0,3,2)` for Godot. **SceneKit uses counterclockwise front faces**, so native geometry should reverse those indices or use outward `(0,1,2),(0,2,3)` winding.
6. Choose top material on original +Y faces; side material on all others. Top/bottom UV = `(x+.5,-z+.5)`; X-facing UV = `(-z+.5,y)`; Z-facing UV = `(x+.5,y)`. UVs repeat. Read `scripts/terrain.gd` for the authoritative face frames and implementation.

This runtime algorithm intentionally differs from the older Blender-dissolve/bevel export pipeline. A Swift loader must reproduce this algorithm or consume geometry baked from it to match the editor. Rounded values can slightly alter support at edges; gameplay grounding should query the resulting mesh.

Signed layers permit holes, caves and floating islands. Terrain occupancy alone does not imply reachability, support rules, water safety or a navigation mesh. More complex diagonal contacts should be visually validated before production use.


## Water extension

`terrain` is the logical cell collection and can now also contain `asset: "water_teal"`, registered as `kind: "water"`, `solid: false`, `occupies_grid: true`. Native consumers must partition these cells before generating solid terrain or walkability. A cell's optional `water_style` references the optional top-level `water_styles` dictionary. See [WATER.md](WATER.md) for exact connectivity, appearance, default and merge rules. Water is generated from cells and style settings, not serialized mesh data. Legacy layouts without water fields remain valid.
