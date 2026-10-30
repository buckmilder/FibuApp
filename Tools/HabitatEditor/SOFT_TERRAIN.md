# Soft connected terrain — fibu-soft-turf-v2

This updates the existing terrain kit and builder, rather than importing external generated models. Forest, Lime and Meadow receive quieter large-scale leaf textures, three broad earth bands and a shallow soft grass cap. Golden, Sand, Limestone, Cobble, Timber and Volcanic keep their existing material artwork. All nine stable terrain IDs remain available. Props, character assets, skins, animations, Swift code, Watch resources and the three prebuilt reference habitats are unchanged.

The existing welded boundary rounding already gives the core its narrow sloped/rounded exposed edges. The added cap follows that contour, bulges around exposed edges, and tucks under at the rim. It is intentionally low-detail geometry; leaf detail is primarily texture. There are no leaf meshes or per-block bushes.

## Geometry and collision

The original `fibu-rounded-boundary-v1` solid-boundary algorithm remains the basis and the collision mesh: exposed faces only, four-by-four face quads, global quarter-meter vertex keys, two simultaneous Laplacian passes at weight 0.35. This rounds the connected outline rather than rounding each tile independently. Logical cubes remain 1×1×1 meters, with first tile bottom-center pivot and Y-up, row=-Z coordinates.

The visual generator is now `fibu-soft-turf-v2` for the terrain catalog. Nongrass themes render exactly as v1. For Forest/Lime/Meadow:

1. Identify grassy +Y faces without a solid cell above. Buried grass cells produce no cap and no painted green fringe on their soil side texture.
2. Retain the complete v1 mesh as `collision_mesh`. Omit grass top quads only from the visual core; preserve exposed core sides and bottoms.
3. Build cap vertices on those top faces using the SAME global lattice keys across all grassy materials. Start from the rounded core positions. Shift by the sum-normalized directions of exposed horizontal edges times 0.065 m. Raise by 0.055 m plus `0.012*sin(x*2.1+z*1.7)*sin(z*1.3-x*.8)`. The world-space variation never restarts as a separate dome on each tile.
4. Emit a rim only where the same-layer face-adjacent solid cell is absent. Adjacent grass caps share exact positions and normals, without a hidden rim between them. Any adjacent non-cap solid suppresses the overhang and marks that seam's cap keys flush: no extra lift/undulation there. This tapers grass into paving/walls instead of intersecting them with a decorative lip.
5. At each exposed rim key, let `p` be its cap position and `n` its normalized outward sum. Depth is `s=0.13+0.035*cos(TAU*(p.x*1.7+p.z*1.7))+0.012*sin(TAU*(p.x*.47-p.z*.91))`. A middle ring is `p+n*.012-(0,s*.5,0)`; a lower ring is `p-n*.025-(0,s,0)`. Shared keys weld rings at corners and along boundaries. Two quad rows form a soft bulging/tucked edge. This is a decorative open shell over the soil, not a watertight standalone collision volume.
6. Recompute area-weighted shared normals across visual quads, group surfaces by material/top-side, then emit the same Godot clockwise triangle order. Terrain UVs stay world-aligned exactly as in v1. Rim faces use the matching grass top material with side-projected UVs. USD/Blender exports reverse winding and flip texture V for their conventions.

`terrain.gd` is authoritative, including face frames, boundary key directions and seam behavior. Source occupancy is independent of material. Water remains excluded from solid terrain and is unchanged by this algorithm.

The visible cap can partially hide the bottom of a character's feet while its movement surface remains the solid soil top (Y=layer+1 in flat interiors). **Do not create collision from the raised visual mesh.** Godot picking/Preview now use the retained solid mesh. Near rounded ledges, query the solid mesh for support; logical occupancy alone is not a navigation/grounding solution. Decorative grass can slightly overhang the logical footprint. It does not make the walkable habitat larger.

The shell is not a grass simulation: no bending under footsteps, wind or displacement is included. Props still use their authored bottom pivots and logical footprint rules. A prop may intentionally nestle into the shallow cap; do not add grass lift to every prop's Y automatically.

## Budgets and review

| Study | Triangles | Grass rim edges |
| --- | ---: | ---: |
| Grass single | 256 | 4 |
| Nongrass single | 192 | 0 |
| Connected 3×3 grass patch | 1,152 | 12 |
| Connected 9×9 flat grass floor | 6,912 | 36 |

Counts cover the rendered mesh, including underside and exposed walls; the collider is a separate retained mesh. Shared internal solid faces and decorative rims do not exist. Materials are batched by theme/top-side, not one draw call per block. These are geometry counts, not a device performance benchmark.

Open `Assets/Habitats/soft-terrain-study.json` to inspect all three grass colors, an exposed terrace and a paving transition without props. Preview images and asset checks are in `Assets/Handoff/SoftTerrain/`. Palette thumbnails for the three changed materials are updated.

`Assets/Models/SoftTerrain/` contains nine standalone singles plus a connected 3×3 patch and terrace as paired GLB/USDZ files. These are reference/baked modules, NOT self-connecting instances. Cloning singles does not suppress their rims or fuse their geometry. For editable layouts, port/bake the connected generator. Earlier module exports and prebuilt habitats are preserved.

The Blender source `Assets/Blender/SoftTerrain/Fibu.SoftTerrain.blend` contains the exact exported builder meshes with packed textures. Shapes and pivots match Godot's generator; the nine modules are arranged in a review grid in the Blender source, while the exported individual files retain their original bottom-center pivots. No modifiers, subdivision or model-generation service is required.

Three 1024×1024 painted top/side map sets are stored with source and copied into the editor texture library. Leaves use 32 broad overlapping strokes per square meter instead of the earlier 330 small marks. Soil keeps three broad gently wavy bands. Palette/source colors differ per grass theme. Quiet periodic normal maps and matte roughness accompany them in Godot; paired static GLB/USDZ references use the same base-color artwork and geometry normals with constant matte roughness. Existing texture originals in other authoring folders remain available. This is an original procedural art pass, ready for later artist textures/UV work.

## Regenerate

From repository root (Python needs numpy, Pillow and usd-core; Blender 4.3.2 / Godot 4.6.3 used):

```sh
python3 Assets/Blender/SoftTerrain/textures.py
./scripts/habitat-editor.sh check
godot4 --headless --path Tools/HabitatEditor --script tests/export_soft_terrain.gd
TMPDIR=/tmp python3 Assets/Blender/SoftTerrain/export_usdz.py
blender -t 4 --background --factory-startup --python Assets/Blender/SoftTerrain/build.py
TMPDIR=/tmp python3 Assets/Blender/SoftTerrain/validate.py
```

Use `FIBU_GODOT_BIN`/the installed Godot app path on Mac and `PYTHONPATH` if usd-core is separately installed. The USD packager uses a writable temp folder. Generated mesh JSON includes BOTH visual and collision arrays; only the visual surfaces are in static reference assets. Blender/GLB and USDZ are built from those same arrays, not from an approximation of the shape.

`tests/soft_terrain_checks.gd` covers shared rims, mixed grass seams, paving transitions, buried cells, holes, signed layers, 3×3 and 9×9 budgets, finite normals and unchanged nongrass materials. The normal editor suite also checks collision hits and existing painting/undo/props/water behavior. Python validation reopens packages, compares vertices/UV coverage/triangle counts and winding, checks embedded texture bytes and dependencies, validates GLB triangle parity and image embedding, and measures texture seam differences.

## Local Codex handoff

Fetch `origin/codex/soft-terrain`, preserving local work. Run `./scripts/habitat-editor.sh check`, then open the editor and the terrain study. These changes update the Godot editor as soon as the branch is integrated; nothing automatically changes the native app.

For native layout rendering, use the `fibu-soft-turf-v2` catalog profile. Reproduce `terrain.gd` or bake its visual AND solid-collision arrays. Keep grass visual only and ground Fibu against soil; disable auto-trimesh collision on the combined visual mesh. Preserve world UV phase, topology at material joins, colors, winding and Y-up/row=-Z conventions. Validate a single, 3×3 patch, hole, terrace and mixed paving boundary. The static GLB/USDZ examples can help compare appearance but do not replace neighbor-aware generation.

Preserve local character/skins/animations and Watch resources; the rejected walk stays on hold. Do not replace the three existing prebuilt habitats unless separately requested. After native renderer changes, run relevant movement/camera/skin checks and build BOTH schemes. Native appearance, foot occlusion, pathfinding and device performance still need Mac validation; cloud checks do not claim those results.
