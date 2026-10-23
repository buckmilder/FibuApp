# Fibu motion starter set

Seven new skeletal clips at 24 fps, supplied as self-contained USDZ character scenes under `Assets/Animations/`. They use the **latest corrected Fibu.Refined.usdz geometry and weights**, not Fibu.Soft.usdz. The original wave remains in Fibu.Refined.usdz and the untouched Fibu.Soft.usdz.

| Clip | Seconds | Playback |
| --- | --- | --- |
| IdleBreath | 4 | Loop |
| Sit | 3 | Enter seated pose, then hold; do not loop transition |
| Whistle | 4 | Loop body sway / hand-to-mouth gesture |
| LayDown | 4 | Enter lying pose, then hold; do not loop transition |
| Hungry | 4 | Loop subtle lean / belly-hand gesture |
| Eat | 3 | Two mimed bites, return to standing |
| Jump | 1.5 | Anticipation, lift, landing, settle |

These are first-pass procedural animation assets for visual review, not application behavior. Whistle has no audio or facial pucker; Eat has no food attached. Neither implements hunger rules, sound, rewards, HealthKit, or automatic state selection. Near-body contacts, skin appearance during large bends, and transitions between actions require local visual review. Sit/LayDown need blend-out or a return-to-standing state. Do not replay their entry on a loop.

## Runtime integration

Read `Assets/Handoff/FibuMotions/manifest.json` and `validated-manifest.json`. Each USDZ has the same named hierarchy and 32-joint skeleton/bind transforms as the refined candidate. It embeds a complete duplicate mesh and original texture for independent inspection. New curves use all 32 joint paths; the old wave's source uses a sparse 30-joint animation. That distinction is intentional. Runtime geometry, UVs, weights, and original material are checked against the candidate.

First load each USDZ as its OWN SceneKit scene and inspect its imported animation players, timing, scale, and material. Then integrate the imported players with the refined character's matching hierarchy. Do not assume an arbitrary animation identifier or node path from another importer; inspect the actual imported entries. The current `FibuWalker` deliberately freezes imported animation at frame zero and drives bones procedurally: suspend that mechanism while an authored clip plays, then blend back to its captured rest pose. Do not apply procedural movement and full-body clips to the same bones simultaneously.

Root motion is grounded using the deformed mesh at every authored sample. Jump includes its own vertical root displacement; avoid applying a second jump offset in Swift. The clips retain the original asset's units/transforms rather than normalizing the rig to meters; use the existing character container scale. Place a seat/bed by positioning the character container against an appropriate scene anchor after checking its seated/lying bounds. They are not automatically aligned to the habitat furniture.

Keep all artist skin images unchanged; reapply the selected skin to the loaded candidate or its cloned material. Update thumbnails only after choosing the refined candidate. Keep Watch on its existing asset until conversion and frame/battery budgets are tested. No Xcode project or app logic was changed by this delivery.

## Authoring and verification

`build.py` is the editable animation source. It reads the tracked `Assets/Models/Fibu.Refined.usdz`, starts with its evaluated first wave pose, authors the gestures, solves hand-to-mouth reach, and grounds the surface. It does not modify that model or the original wave. `MotionPoseReview.blend` is a packed, static key-pose review sheet, **not a Blender animation timeline or the authoritative rig**. Use `../FibuRefined/Fibu.Refined.blend` for the editing mesh, and the USD authoring pipeline for these clips.

Requires Python with NumPy/usd-core 26.11 and Blender 4.3.2:

```sh
TMPDIR=/tmp python build.py
python validate.py
blender -t 4 --background --factory-startup --python preview.py
```

Copy `generated/Fibu.Anim.*.usdz` into `Assets/Animations/`; copy manifests and poses into `Assets/Handoff/FibuMotions/`. Generated files remain ignored. All 571 authored frames are evaluated before export for finite geometry and grounding; the seven packaged scenes are then reopened and all 571 frames checked again. Checks also verify candidate mesh/UV/weight/bind identity, actual nonstatic motion, and loop endpoint agreement. No SceneKit playback, Xcode compilation, device performance, or Watch tests were performed in Linux. Numeric checks do not establish collision-free, polished character acting.

Optional GIF review: run `python sample_gifs.py`, then Blender with `--python gif_preview.py`, then `python pack_gifs.py` (Pillow required). GIFs loop for review; the Sit runtime clip itself remains a non-looping entry with a held final pose.
