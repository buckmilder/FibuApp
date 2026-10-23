# Habitat expansion — nine terrain styles in total

This delivery adds meadow, sand, limestone, cobblestone, timber, and volcanic rock to the existing golden, forest, and lime styles. Each new material has a single, fused pair, fused 5×5 platform, L-corner, and terrace: 30 new terrain USDZs. The previous three variants and app assets remain unchanged.

## Foliage

Six additional original props: `foliage_round_tree`, `foliage_young_tree`, `foliage_shrub`, `foliage_grass_small`, `foliage_grass_fluffy`, and `foliage_grass_tall`. Each has its own USDZ, a base-centered pivot, Y-up meters, opaque matte materials, and explicit normals. The tree has a tapered branching trunk, root flares, and a scalloped three-tier canopy. Its young version is 65% scale. Grass uses thick curved leaf solids, not transparent planes; no wind, skeletons, collision, or LODs are included. The props contain overlapping closed components rather than one union surface. They are static meshes; contact shadows shown in Blender must come from app lighting.

Tree/young-tree: 4,524 triangles each; shrub: 1,344; small grass: 696; fluffy grass: 1,276; tall grass: 928. Exact bounds and SHA-256 hashes are recorded in the delivery manifest. Scale all assets consistently with terrain and Fibu. Tree foliage may extend beyond its origin tile: account for canopy clearance. Small grass is roughly 0.35m high, fluffy roughly 0.53m, tall roughly 0.78m; use manifest bounds for exact sizes.

## Terrain connections

The boundary generator from `../TerrainV2/` removes shared faces, dissolves coplanar joins, and bevels only the exposed contour. Terrain is 1m per tile, with 0.085m edge rounding. Source layouts grow Blender +X/+Y/+Z; USDZ uses +X/-Z/+Y. All terrain pivots sit at the first tile's bottom center. The source script and texture generator are original; no textures or geometry are extracted from the reference games.

The fused examples are prebuilt. Adjacent single USDZ nodes do not auto-fuse. Local app work must use neighbor-aware mesh generation or connection variants to support editing. Cross-material fusion is not implemented. Terrain details are two 512px repeating base-color textures per style, with matte USD Preview Surface; cracks, stone divisions, wood grain, and mineral pores are painted details rather than displacement. Timber is wood-textured terrain, not a structural beam kit. Volcanic rock is solid dark porous stone, without fire/lava effects.

## Reproduce

Requires the existing `../TerrainV2/` scripts, Blender 4.3.2, and Python with NumPy, Pillow, usd-core 26.11. From this directory:

```sh
python textures.py
blender --background --factory-startup --python build.py
TMPDIR=/tmp python export_usdz.py
python validate.py
blender --background HabitatExpansion.blend --python demo.py
```

The editable `HabitatExpansion.blend` packs terrain textures and includes all terrain arrangements plus foliage. The default render displays six new terrain singles and the six props. Other terrain arrangements are hidden only for rendering and remain in the source. `demo.py` renders a separate sample garden using instances of these same meshes. `generated/` is ignored scratch space; copy `terrain_*.usdz` and `foliage_*.usdz` into `Assets/Models/` and validation/previews into `Assets/Handoff/HabitatExpansion/`.

## Checks and local integration

Validation covers closed edge-manifold components, outward signed volume per component, finite coordinates, triangle bounds, complete unit normals, material bindings, embedded texture counts, dependency resolution, USDZ archive alignment, and hashes. Blender product and habitat previews were inspected. Apple SceneKit appearance, iPhone/Watch rendering, performance, and Xcode builds remain untested here. Do not switch renderers or regenerate character assets for this delivery.

On the Mac, add desired assets to Xcode resources, stage a test habitat in existing SceneKit, match Fibu scale, verify leaves remain opaque and the tree is grounded, then build both targets and run existing checks. Watch use needs an appropriate conversion and a separate performance budget; do not automatically load every detailed prop on the watch.
