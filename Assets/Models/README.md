# Runtime models

- `Fibu.Soft.usdz`: the existing Fibu character, including its rig and original wave. Preserve this file when delivering habitat assets.
- `Fibu.Watch.scn`: generated Watch-compatible character scene. Regenerate with `scripts/prepare-watch-asset.swift` when the character model intentionally changes.
- Future habitat kit: multiple separately named `.usdz` modules directly in this folder. Do not combine them into or replace the Fibu character file. Record module scale, axes, pivots, and connections in `Assets/Handoff/CHANGES.md`.

Editable Blender sources belong in `Assets/Blender/`. The older `.blend` file in this folder is a preserved setup snapshot. See `Assets/Handoff/README.md` for the cloud delivery workflow.
