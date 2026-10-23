# Modular diorama water — v1

One placeable asset, **Water → Water Block** (`water_teal`), adds original translucent blue-green water to the desktop creator. The material, geometry and foam are procedural; no Wonderbox assets were copied. It is a grid volume, not a fluid simulation or solid platform.

## Use

Choose Water in the category palette (or search “water”). Place, drag-paint, erase, select, move and duplicate using the existing cell tools. A cell is one meter, with the same X/row bounds and signed vertical layers as terrain. Neighboring water joins automatically, including vertically. Placement prevents two cells occupying the same location, including solid terrain or solid stairs; decorative props may be submerged.

Use **Show/Hide water** above the viewport to hide water and its picking collider while retaining the data. This makes the underlying floor accessible to selection, painting and erasing. When visible, water itself is easy to pick. Hold Alt to use the build plane instead of a surface; Shift-drag and WASD camera controls also work below the habitat.

Select a water cell to edit the **Connected water** inspector. Colors, top/side opacity, depth tint, roughness, highlights, ripple speed/strength/scale, foam color/width/coverage/speed/irregularity and animation toggles apply to the whole face-connected body. Disconnected ponds keep independent settings. Color edits form one undo entry when the picker closes; numeric edits are also undoable.

Appearance defaults are fairly transparent: base top and side opacity 0.40, with a small additional depth term. Exposed edges have broken foam strips and a subdued side ribbon; shores and walls have narrower variants. Underwater shelves and floors remain visible. Settings and water cells survive habitat Save/Load. Preview renders water with the same module but does not make it walkable or implement swimming.

Open `Assets/Habitats/water-garden.json` for a composed example with shallow/deep areas and an exposed diorama edge. `water-study.json` covers a single cell, 2×2 pond, three-layer pool, L-shaped pool, submerged terrain, shores/walls and disconnected bodies. Neither file replaces any existing native habitat.

## Portable layout contract

Water remains in the shared logical grid collection, distinguished from solid terrain by the asset registry's `kind: "water"`. Native consumers **must classify cells by kind**; do not turn every `terrain` entry into solid ground. `solid` is false and `occupies_grid` true for water. The asset registry points to `fibu-water-volume-v1` generation rather than a static GLB/USDZ.

```json
{
  "terrain": [
    {"cell": [3, 0, 2], "asset": "water_teal", "water_style": "pond_a"},
    {"cell": [4, 0, 2], "asset": "water_teal", "water_style": "pond_a"}
  ],
  "water_styles": {
    "pond_a": {
      "version": 1,
      "shallow_color": "279baf",
      "deep_color": "174c70",
      "opacity": 0.4,
      "side_opacity": 0.4,
      "depth_strength": 0.32,
      "foam_enabled": true
    }
  }
}
```

All omitted style fields resolve to `HabitatWater.defaults()`. Omitted `water_styles` is valid for older layouts. Missing/default style IDs resolve to defaults; saved references and unknown fields are retained. The new validation checks water settings, finite values, cell bounds, duplicate occupancy and style ID types. The existing habitat format remains version 1 because these are additive fields.

On a merge, rendering uses the style reference of the lexicographically first canonical `x,layer,row` cell key in that connected body. Other references remain saved and can reappear if bodies split. Editing the connected body's appearance assigns one consistent style to all its cells; it does not modify unrelated ponds. This is one visual style, not a library of additional water types.

## Connected geometry

`HabitatWater.components()` performs six-neighbor flood fill over water cells. For each component:

1. Convert `[x,layer,row]` to world lattice `[x,layer,-row]`, with horizontal half-cell offsets matching the terrain contract.
2. Emit only faces without neighboring water or solid terrain. Culling applies to every direction, so vertical stacks have no internal horizontal surfaces. Retain exposed surfaces at different elevations.
3. Compute each contiguous vertical column's top/bottom. Interpolate average neighboring depths at shared corners for columns with equal tops. Mesh UV2 holds column thickness and distance below the top. This is an inexpensive **vertical-column depth approximation**, not a screen-space optical-depth or refractive effect. A submerged decorative object does not change the tint's depth estimate.
4. Render top/side/bottom faces with translucent, backface-culled material. Shared global-position ripple equations avoid per-cell animation resets; there is no vertex displacement that could split joins. A subtle highlight pattern supplies motion without mirror reflections.
5. For each exposed +Y face, find horizontal neighbors. Generate foam only at the outer surface perimeter, including shores, walls and elevation breaks, never between equal-height water neighbors. World-space procedural masks break the strips into varied white streaks and gaps. Exposed sides receive a faint folded ribbon.

The generated component caches include geometry, materials and picking shape. Unchanged bodies reuse these; edits regenerate affected components, not every cell every frame. Style changes regenerate the affected body so foam width and appearance update together. Materials are shared by style/body surfaces, not instantiated per cube. Orphaned style records are retained to avoid discarding authored data.

Pick colliders use layer 8; ordinary terrain/solid stairs use layer 1, and the preview proxy's collision mask stays 1. The water volume is therefore identifiable and editable without becoming solid ground. No health, food, swimming, buoyancy, currents, waterfalls, or triggers are added.

## Sky response and native integration

Volume shading receives the existing directional/ambient lighting and fog. Foam brightness/tint also follows Sky & Atmosphere changes, keeping daytime accents white and night accents subdued. No realtime reflection capture, screen-depth sampler, refraction or volumetric simulation is used. The renderer remains Godot Compatibility.

The Swift app is unchanged. SceneKit does **not** import Godot shaders. Local Codex must decode these water cells/styles and implement or bake the boundary mesh plus a corresponding transparent material/foam renderer. `water.gd` and the two shaders are the reference implementation. Reverse Godot's clockwise triangle winding for SceneKit's counterclockwise front faces, retain meters/Y-up/-Z rows, and preserve explicit water classification. Generated geometry should not be the authored source of truth.

## Validation and limits

Headless checks cover hidden internal faces, perimeter-only foam, vertical and L-shaped bodies, shores/walls, depth independent of global Y, cache reuse, normals/winding, bounds/overlap, actual editor commands, body appearance isolation, undo/redo, persistence, picking hidden/visible water, lighting changes and preview collision separation. Real Compatibility renders are captured in `docs/water-study.png`, `water-garden.png` and `water-night.png`. Regenerate screenshots/thumbnail with `tests/render_water.gd` on a graphical display.

Alpha transparency has practical sorting limits, particularly intersecting bodies, props that also use transparency, and cameras inside the volume. Internal water faces are removed and top/side priorities are stable, but order-independent transparency and underwater immersion rendering are not implemented. Foam is a stylized boundary treatment, not wave simulation. Beveled terrain at a shore can expose small geometric differences at close range; terrain meshes were not changed to fit the water. Daylight and night have been inspected in Linux; native Mac ergonomics, SceneKit parity and iPhone frame-rate/battery performance still need local testing.
