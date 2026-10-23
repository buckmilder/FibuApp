# Painted terrain and three 9×9 habitats

Original procedural paint-style textures informed by the supplied soft, mottled grass references. All nine styles receive 1024px top/side color maps plus 256px normal/roughness maps (54 PNGs). The grass adds muted leaf strokes and sparse seed/flower flecks; earth/sand add mineral grains; limestone adds pores/cracks; cobble retains mortar and varied stones; timber adds grain/knots; volcanic stone adds dark pores. These are this project's textures, not extracted game textures. Prior sources and their textures remain in TerrainV2/ and HabitatExpansion/; previous runtime versions remain in Git history.

All 45 detailed `terrain_{style}_{layout}.usdz` files are refreshed in place, retaining their one-meter grid, pivots, geometry, normals, and `/Terrain/Mesh` path. UVs are regenerated from the editable meshes: 29 exports differ from the earlier files following a stale UV-handle fix; some prior files contained corrupted coordinates. See geometry-compatibility.json for exact differences. Layouts remain single/pair/5×5-platform/L-corner/terrace. They are building modules, separate from the **three new 9×9 assembled habitats**. Individual blocks still do not auto-connect when cloned; fused meshes or local neighbor-aware generation remain necessary.

## Preconstructed scenes

- **Garden nook:** meadow base, trees, pergola, bench, stepping stones, shrubs, flowers, grass, picnic mat and fruit bowl.
- **Pond retreat:** recessed 5×4 basin, turquoise surface, stone coping, fountain, deck/bench, umbrella, trees, flowers and lantern.
- **Ember camp:** volcanic base, timber deck, cobblestone fire hearth/path, logs/stools, crates, lanterns, tree and sparse grass/rocks.

Scene files: `Assets/Models/habitat_{garden,pond,camp}.usdz`. Each includes separately named meshes and embedded material textures. Base footprint: 9×9 meters, X from -0.5 to 8.5 and Z from -8.5 to 0.5, Y-up; ground top Y=1 before prop heights. Vegetation/umbrella can overhang the core footprint. The pond's basin removes ground cells rather than hiding an intact grass surface under water. The water/stream/ripples and fire shapes are **static**; no simulation, flicker, particles or audio. Emissive materials do not guarantee lighting in SceneKit; configure app lighting.

These are asset scenes, not an implemented habitat editor or navigation system. Fibu is not embedded. Place the character with a common scene scale, then configure walkable areas and obstacle handling. `layout-notes.json` supplies grid conventions, suggested spawn, and pond exclusion cells, not a baked navigation mesh. Avoid letting the current rectangular movement clamp route Fibu through furniture or water. Check all furniture interactions separately; authored sitting/lying clips are not automatically matched to seat anchors.

## Rebuild

Requires the tracked TerrainV2/build.py generator, HabitatExpansion/ foliage source, both older texture folders, Blender 4.3.2, and Python with Pillow/NumPy/usd-core 26.11. From this folder:

```sh
python textures.py
blender -t 4 --background --factory-startup --python build.py
blender -t 4 --background FibuHabitats9x9.blend --python capture_modules.py
TMPDIR=/tmp python export.py
python validate.py
blender -t 4 --background FibuHabitats9x9.blend --python preview_materials.py
```

`FibuHabitats9x9.blend` packs all textures and includes the three scenes plus hidden module meshes. Garden is visible by default; scene mesh names and generation code identify the other sets. Source props remain separately editable. `capture_modules.py` retrieves fresh post-modifier UV data. The shared TerrainV2 generator was corrected to refresh its UV handle after the normal modifier. Export removes zero-area triangles and supplies geometric normal fallbacks for the pond boundary where needed.

Copy generated runtime USDZs into Assets/Models/, and validated manifest/previews into Assets/Handoff/HabitatWorlds/. `generated/` is ignored. The USD materials carry base color, normal and roughness; final SceneKit importer support and lighting must be checked on Mac. Base color remains usable if a renderer omits the extra maps. The Blender previews include studio lights and shadows that are not exported as gameplay lighting.

Validation reopens all 48 packages and verifies finite indexed meshes, unit normals, UV/material coverage, texture dependency resolution, stored/aligned USDZ archives, hashes, and 9×9 habitat base bounds. It also compares existing module geometry and UVs against the previous committed versions. Habitat triangle counts: garden 46,816; pond 30,862 after degenerate cleanup; camp 16,540. Refer to the final manifest for exact counts. No Xcode builds, iPhone performance, collision/navigation, or Watch rendering were validated here. Add resource references on Mac, measure the chosen scene, and run both simulator builds and existing tests after integration.
