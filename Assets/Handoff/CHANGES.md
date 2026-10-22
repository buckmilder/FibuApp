# Terrain V2 — three detailed variants

New delivery: golden earth, forest turf over layered soil, and lime layered grass. Source: `Assets/Blender/TerrainV2/FibuTerrainV2.blend`; original packed and standalone color textures plus reproducible generation/export/validation scripts live beside it. Previews and per-asset validation manifest: `Assets/Handoff/TerrainV2/`.

Runtime assets: `Assets/Models/terrain_{golden,forest,lime}_{single,pair,platform,corner,terrace}.usdz` (15 files). Each is self-contained with two 512px color textures, explicit normals, and matte USD Preview Surface materials. Single/pair/platform have 428 triangles each; corner/terrace have 644 each. Names are unique and existing models are preserved.

The fused samples omit shared faces and coplanar tile boundaries before beveling exposed contours with a 0.085m radius. They demonstrate seamless joins on a pair, a 5×5 platform, an L-corner, and a stacked terrace. THESE ARE PRE-FUSED SAMPLES: placing independent single-cube assets next to each other will not connect them automatically. A future editable habitat requires local neighbor-aware mesh rebuilding or a complete set of connection variants. See source README for the boundary-mesh algorithm, placement dimensions, and limitations. Cross-material connections are not yet implemented.

USDZ uses Y-up and meters, with the first cell bottom center as origin; occupancy and exact bounds are recorded in the manifest. Blocks extend toward +X / -Z; terraces rise +Y. Use a common scale to fit the existing island/Fibu. This is an art and asset handoff, not a gameplay change.

Validation: all 15 closed meshes passed edge-manifold, signed-volume, triangle index/UV coverage, unit-normal, material binding, packaged-texture dependency, hash, and USDZ alignment checks. Blender overview and close-up renders were inspected. Xcode, SceneKit appearance, iPhone performance, and Watch conversion remain for local testing. No Swift, Xcode references, character files, or Watch assets changed.

Suggested local pass: review the close-up first, add resource references for a representative single and fused platform, display them using the current SceneKit renderer, match scale to Fibu, check textures and smooth contours, then run both builds and existing tests. Keep habitat building/editor behavior separate until requested. Character Watch regeneration is unnecessary for this delivery.

---

# Habitat block kit — first delivery

21 prototype modules: three palettes (meadow, stone, timber), each with cube, half, slab, ramp, steps, wall, and post. See HabitatKit-manifest.json for exact filenames and SHA-256 hashes; HabitatKit-preview.png shows the shapes and a sample 5×5 layout.

## Placement

USDZ uses Y-up and meters. Pivots are centered horizontally at the bottom. Tile width/depth is 1m. Cubes, ramps, and four-step stairs rise 1m; half blocks rise 0.5m; slabs rise 0.25m. Walls measure 1m wide × 0.25m deep × 1m high; posts measure 0.25m square × 1m high. Ramps and stairs rise toward -Z. Adjacent full tiles use 1m center spacing; stack at the support surface height. Apply one common scale to the entire habitat and match Fibu to it during local integration.

## Sources and regeneration

Editable source and scripts: Assets/Blender/HabitatKit/. Run `blender --background --factory-startup --python build.py` from that directory, then `python package_usdz.py` with usd-core installed. Outputs are generated in its models/ subdirectory; copy only the resulting USDZ modules into Assets/Models/ for delivery. Do not overwrite the character assets. Blender 4.3.2 and OpenUSD 26.11 were used for this delivery.

## Validation and limitations

All 21 USDZ packages reopen with nonempty geometry, valid face indices, fully bound face-material subsets, base-centered grounding, and no unresolved dependencies. Blender source was saved and its overview rendered. Materials are solid-color USD Preview Surface prototypes; no external textures. Rectangular pieces have small bevels; ramps are sharp. Hidden interior faces remain, and touching grass caps do not automatically merge. These are initial building blocks, not finished decorated habitats.

The existing app uses SceneKit: import the USDZ modules using the established SceneKit workflow; do not migrate it to RealityKit just for this kit. Check material appearance, scale against Fibu, pivots, and adjacency in the iPhone simulator. Add Xcode resource references during local integration, then build both schemes and run the existing checks per AGENTS.md. Watch rendering requires a separate validated conversion or preview strategy.

Xcode, SceneKit rendering, simulator builds, and device performance were not tested in Linux. App code, Xcode project references, character USDZ, character Blender sources, and Watch scene are unchanged. No character re-export or Watch regeneration is needed for this asset-only delivery.
