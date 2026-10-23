# Fibu terrain — three original variants

- **Golden:** pale sandy top, warm ochre earth, subtle mineral flecks.
- **Forest:** dark green turf with an irregular grass edge over layered warm soil.
- **Lime:** bright grassy top and alternating scalloped green bands.

Original geometry and six original 512×512 seamless color textures. No game assets are copied. `FibuTerrainV2.blend` includes the three variants in five arrangements and packs its textures for portability.

## Fused geometry

`build.py` starts from occupied grid cells, omits shared faces, dissolves coplanar grid boundaries, then bevels the resulting boundary mesh (radius 0.085m, five segments). This rounds exposed convex and concave contours without creating seams at internal tile joins. Top and side UVs use a common world grid, so texture phase does not restart at each block. Blender Z-up becomes Y-up in USDZ; `(x,y,z)` maps to `(x,z,-y)`.

The included single, pair, 5×5 platform, L-corner, and terrace are **pre-fused meshes**, not self-connecting individual USDZ nodes. Cloning singles in SceneKit will not fuse them. For editable habitats, local app work must rebuild exposed geometry from occupied cells or select a complete neighbor-aware variant system. This delivery establishes the art and tests the fused result; it does not implement an in-app terrain editor. Mixed-material boundaries, holes, diagonal-only contacts, arbitrary imported layouts, and mesh rebuilding performance have not been validated. Existing app and character assets are unchanged.

Texture detail repeats once per meter and remains visible on large platforms. Grass fringes and strata are painted color detail, not separate foliage geometry. Materials use matte USD Preview Surface base-color textures, with no normal/displacement maps. Soft shading is exported as explicit face-varying normals. This is a first detailed art pass, pending iPhone visual approval.

## Rebuild

Dependencies: Blender 4.3.2, Python with NumPy, Pillow, and usd-core 26.11.

From this directory:

```sh
python textures.py
blender --background --factory-startup --python build.py
TMPDIR=/tmp python export_usdz.py
python validate.py
blender --background FibuTerrainV2.blend --python closeup.py
```

`generated/` is ignored scratch output. Copy `generated/terrain_*.usdz` to `Assets/Models/`, and copy previews plus validation-report.json to `Assets/Handoff/TerrainV2/`. No script changes app code or Xcode references. Validate after copying by comparing SHA-256 hashes.

Runtime dimensions use 1m tiles and a pivot at the first cell's bottom center, so the first tile spans x/z ±0.5m. Layout extensions grow +X and Blender +Y (USD -Z); upper levels grow USD +Y. Apply one common habitat scale to match the app and character. The pair is 2×1×1 tiles, platform 5×5×1, corner occupies three cells in a 2×2×1 box, terrace occupies nine cells in a 3×2×2 box. The manifest records exact occupied cells in Blender grid coordinates.

Validation checks closed two-manifold triangulation, signed volume, UV/normal coverage, unit normals, USD material bindings, packaged textures, dependency resolution, and USDZ archive alignment. Apple SceneKit/RealityKit appearance, Xcode builds, Watch conversion, and device performance must be checked on macOS.
