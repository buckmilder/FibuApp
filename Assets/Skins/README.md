# Fibu skins

`Source/` contains the 11 unchanged 2048×2048 PNG texture maps from the user’s skins.zip. The archive’s macOS metadata file is excluded. The iPhone asset catalog contains 1024×1024 runtime copies (`FibuSkinNNN`) and small rendered character previews (`FibuPreviewNNN`); filenames map to the original source numbers in FibuSkin.swift. The embedded USDZ texture remains the Original option.

All 11 textures were rendered on the softer 3,200-triangle model to check wrapping. The app swaps only the Fibu material’s diffuse texture, retaining its UV transform, rig, geometry, and animation. Skin selection is local iPhone UserDefaults (`fibu.selectedSkin`); it does not sync to Apple Watch. Existing USDZ, Blender sources, and Watch scene are unchanged.

## Supplied icons

`Icons/` preserves all 11 supplied skin SVGs and both original menu SVGs. Matching numbered SVGs are used for skins 000–007, 011, and 012. There is no 013/leopard icon or exact embedded-original icon in the archive, so those two entries use rendered model previews. `xxx.skin.svg` is an unknown/question-mark icon and is retained as an unused spare. The Fibudex SVG opens the picker; the habitat SVG is displayed as a disabled placeholder.
