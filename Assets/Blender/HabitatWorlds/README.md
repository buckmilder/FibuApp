# Terraced habitats — habitat-only delivery

This branch delivers exactly three replacement scene assets: garden, pond, and camp. Each has a 9×9 core footprint, fused rounded terrain at heights 1, 2 and 3 meters, and two four-tread stairways connecting levels. Props on raised ground are elevated with their supporting terrace. Pond stairs run along the right bank; camp stairs sit beside the hearth. Fire, water and ripples remain static.

Sources: `FibuHabitats9x9.blend` packs textures and includes all three scenes (garden visible by default). The generator depends on the included `../TerrainV2/` boundary generator and `../HabitatExpansion/` foliage library and previous texture sources. These folders contain habitat geometry only. The generator also produces the earlier 45 module arrangements as scratch outputs; this isolated delivery ships only the three complete runtime habitat USDZs.

Rebuild with Blender 4.3.2 and Python with NumPy, Pillow, usd-core 26.11:

```sh
python textures.py
blender -t 4 --background --factory-startup --python build.py
blender -t 4 --background FibuHabitats9x9.blend --python capture_modules.py
TMPDIR=/tmp python export.py
python validate.py
```

Generated data remains in ignored `generated/`. Export includes painted base color, normal and roughness maps in each USDZ. The default build renders all three scenes; `FIBU_SKIP_RENDER=1` skips rendering during generation. Scene coordinates are Y-up meters in USD, with row mapped to -Z. First tile is centered at X/Z zero; the footprint spans X [-0.5,8.5], Z [-8.5,0.5]. Vegetation may overhang.

See `Assets/Handoff/HabitatWorlds/README.md` and `terrace-layout.json` for replacement instructions and terrain heights. Grid heights describe terrain, not furniture collision or stair interpolation. Local movement must follow actual surface height and avoid water, cliffs and props. This is not a baked navigation mesh. One-meter main rises have four 0.25m treads.

All packages were reopened and checked for indexed finite geometry, normals, UV/material coverage, dependencies and archive alignment. All 243 grid-column terrain heights were ray-probed against exported geometry, including the 20 pond openings. Previews were visually inspected. SceneKit import, navigation, iPhone performance and both Xcode builds still require local validation.

No character, rig, skin or animation changes are part of this branch. Day/night is a future SceneKit runtime task: scene lights are not baked into these textures. App lighting, sky/environment, shadows and lantern emission can change at runtime; preview lighting is not exported gameplay lighting.
