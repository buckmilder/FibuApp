# Fibu asset handoff

## Repository and branch

Repository: https://github.com/buckmilder/FibuApp.git

The Xcode project is `FibuApp.xcodeproj` at the repository root. `main` is the app baseline. Use `codex/asset-handoff` for future cloud asset deliveries and integrate it into `main` through review. Start each new delivery from the current shared `main`, retaining any work already on the delivery branch. Never force-push or overwrite unrelated local or remote work.

## Asset locations

| Purpose | Repository-relative path |
| --- | --- |
| Editable Blender source | `Assets/Blender/Fibu.Soft.blend` |
| Exported iPhone model used by Xcode | `Assets/Models/Fibu.Soft.usdz` |
| Generated Watch model used by Xcode | `Assets/Models/Fibu.Watch.scn` |
| Current mesh statistics | `Assets/Models/mesh-report.json` |
| Original user asset, preserved | `Assets/Source/Fibu3.HD.HandWave.usdz` |
| Handoff metadata and instructions | `Assets/Handoff/` |

The Blender source was copied byte-for-byte from `Assets/Models/Fibu.Soft.blend`. That older copy is retained to preserve existing work; use `Assets/Blender/Fibu.Soft.blend` for future edits. The current runtime exports are unchanged. The manifest records baseline hashes for comparison, not hashes that future deliveries must match.

## Instructions for cloud Codex

Read root `AGENTS.md` and this document before editing. Work on `codex/asset-handoff`. Keep changes focused on Blender sources, exported assets, and the handoff notes. Preserve the Xcode project and current Swift app behavior unless the user specifically requests changes.

Keep Fibu’s established shape, UVs, texture, skeleton names/hierarchy, skin weights, scale, axes, and grounding consistent with the current USDZ. The current budget is 3,200 triangles and 32 joints; report any change. Keep the character soft and slightly plump. Visual references are Wonderbox, Animal Crossing, and Pokopia.

The Blender file includes a preview walk action. The current runtime USDZ retains the original wave; the iPhone app builds procedural walking on the supplied rig. Do not assume a default Blender USD export will preserve the same animation data. Validate the exported rig and wave before replacing the runtime model. Pack required textures into the Blender source and USDZ so the cloud handoff has no machine-specific paths.

Return the updated `.blend` and `.usdz` at the exact paths above, updated mesh statistics, front/side previews, and a short `Assets/Handoff/CHANGES.md` describing changes and validation. Do not rename runtime assets or add duplicate Xcode resource references.

The modular habitat kit will contain multiple separately named USDZ files directly under `Assets/Models/`. Deliver each module as its own file; list filenames, dimensions/units, pivots, axes, and intended connections in `CHANGES.md`. Keep editable Blender sources under `Assets/Blender/`. Preserve `Assets/Models/Fibu.Soft.usdz` as the character model: habitat exports must never replace it. Add new habitat resource references only during the local integration pass; asset delivery alone should not change the current island gameplay.

## Local integration checks

On macOS with Xcode, regenerate the Watch scene from the delivered USDZ:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift scripts/prepare-watch-asset.swift
./scripts/build-simulators.sh
./scripts/test-camera.sh
./scripts/test-movement.sh
```

The Watch exporter checks that its scene reloads with all 32 bones and both animation groups. Inspect the iPhone island, tap-to-walk, zoom/orbit, and Watch tap-to-wave in simulators. If the cloud environment lacks Xcode, state that clearly and leave these checks for the local integration pass. Do not claim simulator or physical-device validation without performing it.
