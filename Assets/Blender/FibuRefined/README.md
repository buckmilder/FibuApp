# Fibu refined — review candidate, original preserved

`Assets/Models/Fibu.Refined.usdz` is a separate candidate. Existing `Fibu.Soft.usdz`, both old Blender sources, Watch SCN, skin PNGs/icons, app code, and Xcode references remain unchanged. Do not replace the active character until the candidate is checked in SceneKit.

## Shape and deformation

Smooths irregular arm/hip rings, adds fuller rounded arms, smooths arm joint-weight transitions, lifts/tucks the lower belly, brings the feet slightly forward and apart, and fills the posterior into a single smooth rounded volume without a modeled cleft. One subdivision level supplies a smoother silhouette. A local linear reference protects the painted smile during refinement.

The mesh grows from 1,602 vertices / 3,200 triangles to 7,642 vertices / 15,280 triangles. Treat it as an iPhone candidate; measure frame time before changing the Watch asset. All 32 original USD joint paths, hierarchy, rest/bind transforms, mesh binding transform, and animation attributes/time samples are retained. Arm weights are intentionally smoothed, then interpolated through subdivision and normalized to at most ten influences per vertex. The largest discarded influence sum is 0.002193 (about 0.22%) before normalization. A follow-up reach test also isolated torso weights from arm controls and corrected lower-leg side assignments, preventing hand-to-face poses from dragging torso vertices. The active Fibu.Soft.usdz remains untouched.

## Skins

No textures are repainted. UVs are interpolated within the existing charts, keeping their boundaries and coverage rather than doing a new unwrap. The total UV area agrees within numerical tolerance, and the embedded original texture bytes are unchanged. This is compatibility evidence, not a guarantee of identical appearance: the surface and topology changed, so pattern stretch and bending must be inspected. The gallery renders the original texture plus all eleven source skins on the candidate, with filename order recorded in `skin-order.json`. Local skins created after the last pushed baseline are not included.

## Editable source and pipeline

The original Blender source has a Blender 5.2 header and cannot be opened by this environment's Blender 4.3.2. The runtime USDZ is the authoritative source for this refinement. `Fibu.Refined.blend` reconstructs its rest surface and a 32-joint EDITING rig in upright Blender coordinates. Compact bone/group names map by index to the original full USD paths stored on the rig as `usd_joint_paths`. The source embeds the original texture. Its editing bone orientations are reconstructed, and it does not import the original animation timeline or original Blender controls. Do not replace the original runtime skeleton with a default export of this editing rig.

Instead, the export pipeline replaces only the USD surface data while retaining the original runtime skeleton, transforms, material graph, and wave. It maps editing coordinates back into the original mesh coordinates. `body['raw_height_offset']` records that conversion. Keep object transforms and joint mapping intact when editing; work on the rest mesh. No character geometry is included in the habitat generator.

Dependencies: Blender 4.3.2, Python with NumPy and usd-core 26.11. From this directory:

```sh
PYTHONPATH=/path/to/usd/python python prepare.py
blender -t 4 --background --factory-startup --python build.py
TMPDIR=/tmp PYTHONPATH=/path/to/usd/python python export.py
PYTHONPATH=/path/to/usd/python python validate.py
blender -t 4 --background --factory-startup --python preview.py
blender -t 4 --background --factory-startup --python skin_preview.py
```

If `usd-core` is already installed in that Python, omit PYTHONPATH. Paths are examples, not a required global installation. `prepare.py` reads the original `Assets/Models/Fibu.Soft.usdz` without changing it. Generated files stay under ignored `generated/`. The exporter must use the original baseline against which this candidate was made; do not silently rebase onto a replacement character.

To capture manual edits to the provided candidate source, run `prepare.py`, then `blender --background Fibu.Refined.blend --python export_edit.py`, then `export.py` and `validate.py`. Do not run `build.py` after manual edits: it regenerates the source. Topology/UV changes need deliberate review of validation expectations.

## Verified here and required on Mac

All skeleton and animation attributes match the original, including values at every authored sample. Skinning evaluation runs over all 51 wave rotation samples with finite geometry and bounded dimensions. Joint indices, normalized weights, normals, UV coverage, texture identity, package reopening, and dependency resolution pass. Front/side/back previews use the exact same evaluated first animation frame, camera, scale, material, and lighting for the original (left) and candidate (right).

macOS checks remain: load as a separate SceneKit resource, inspect all skins front/side/back, idle, tap-to-walk, wave, scale/grounding, and frame time. Build both schemes and run existing tests. Keep Watch using its original SCN until an independently budgeted conversion passes. Update skin picker thumbnails only after choosing the candidate; do not overwrite artist source textures to hide a mapping issue. Rig preservation alone does not establish procedural walking or Watch compatibility.
