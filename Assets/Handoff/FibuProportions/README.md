# Fibu proportions review

Branch: `codex/fibu-proportions`. Candidate: `Assets/Models/Fibu.Proportions.usdz`. Editable source and regeneration instructions: `Assets/Blender/FibuRefined/`.

## Visual changes

Both arms are thicker, with additional fullness on anatomical left. Legs are fuller in width and depth, closer together, and shifted forward. Upper hips blend forward under the shoulders. The earlier added rear bulge is removed; the butt remains round without a cleft. Shoulder and hip skeleton transforms are preserved, so this is a surface proportion revision rather than a rig repositioning.

Each comparison shows **previous candidate left / revised candidate right**, at the same first-wave pose, scale, camera and lighting. Anatomical left appears on the viewer’s right in the front view.

## Local Codex handoff

Review the separate USDZ in SceneKit before activating it. Preserve the active Fibu.Soft.usdz, Watch SCN, artist textures, and existing app resource references. Inspect all locally available skins, procedural idle/walking, original wave, and grounding. Run both simulator builds and existing app checks if integrating. Do not import the earlier sitting experiment; sitting animation work remains paused. No new animation clips are delivered here.

Cloud validation passed: 32 original joints and original skeleton/animation attributes retained, normalized weights, UV area retained within tolerance, original embedded texture bytes unchanged, package dependencies resolved, and all 51 wave samples evaluated. Native rendering and local skin compatibility remain to be checked on Mac.
