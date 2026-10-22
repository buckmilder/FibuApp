# Fibu modular block kit — first prototype

21 original building pieces inspired by cozy miniature worlds: meadow, stone, and timber palettes, each with cube, half block, slab, ramp, steps, wall, and post.

## Files

- `FibuBlockKit.blend`: editable source with all pieces and a sample 5×5 layout.
- `preview.png`: rendered overview.
- `models/*.usdz`: self-contained iOS / RealityKit assets, using USD Preview Surface materials.
- `models/*.glb`: alternate assets for other 3D tools; RealityKit does not directly load GLB.
- `models/*.usdc` and `*.json`: intermediate USD and mesh data.
- `build.py`: regenerate source, GLB exports, and preview using Blender 4.3+.
- `package_usdz.py`: generate USDZ using Python with `usd-core` installed.

## Grid and orientation

Each tile is 1 meter wide and deep before app scaling. Origins are centered horizontally at the base. USDZ files use Y-up; Blender source uses Z-up. The cube is 1m high, half block 0.5m, slab 0.25m; wall is 1m wide × 0.25m deep × 1m high; post is 0.25m square × 1m high. Ramp and four-step staircase span a full tile and rise 1m. Place centers at integer grid coordinates; stack pieces at their actual heights. Ramps rise toward Blender +Y / USD -Z.

Apply the same scale to all pieces. At 0.1 scale a tile becomes 10cm. These are solid-color prototype materials, with small bevels on rectangular pieces. Ramps have sharp edges. Individual pieces are deliberately distinct; grass caps do not merge or remove hidden neighbor faces automatically. There are no textures, plants, UV atlases, LODs, collision bodies, or character animations yet. Geometry includes hidden surfaces; optimize once the visual direction is approved.

## Swift / RealityKit

Add the desired USDZ files to your iOS target and enable target membership / Copy Bundle Resources. This example expects a regular bundle resource, not a Reality Composer Pro package:

```swift
import RealityKit

@MainActor
func loadMeadowTile() async throws -> Entity {
    let tile = try await Entity(named: "meadow_cube.usdz")
    tile.scale = SIMD3<Float>(repeating: 0.1)
    return tile
}
```

For repeated tiles, load once and clone recursively. An app must add the entity to its RealityKit scene and configure the camera and lighting. The download does not change your app automatically. RealityKit rendering targets iPhone / iPad; watchOS needs a separate image or supported rendering approach.

## Regenerate

From this folder, with Blender on PATH and Python `usd-core` available:

```sh
blender --background --factory-startup --python build.py
python package_usdz.py
```

Verified in Linux Blender and OpenUSD: source generation, rendering, 21 USDZ packages reopening, nonempty geometry, base-height orientation, and absence of unresolved dependencies. Apple rendering, Xcode compilation, and on-device performance have not been tested here.
