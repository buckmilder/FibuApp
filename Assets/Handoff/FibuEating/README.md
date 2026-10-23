# Elastic-arm eating / facial-expression handoff

Branch: `codex/fibu-eating`, based on approved proportions commit `113eb87`. This revision supersedes the first eating pass (`31fbe7e`). **Timeline version 2 is incompatible with the old hand-bone attachment track.** This delivery does not modify Swift, Xcode references, artist source skins, the active character resource, or Watch assets.

## Revised animation

The torso, legs, opposite arm, and complete skeleton pose stay fixed. Local cheek/swallow shapes remain on the face. The feeding arm stretches along a curved path: first out in front of the belly, then across/up toward the mouth, then back along the same route. The shoulder and upper arm stay fixed during authoring; the forearm lengthens through its wrist endpoint and expands radially to about 1.40 before smoothing. A pinned shoulder boundary keeps the elastic deformation off the torso. The approved body's rest points, topology, UVs, skin weights, joint hierarchy and bind/rest transforms are preserved.

The body now has FOUR morph targets: `CheekPuff`, `Swallow`, `ArmPrepare`, `ArmBite`. Each mouth mesh has only the two facial targets. The 2.8-second clip is non-looping, with 85 samples at 30 fps. All skeletal transforms remain in the approved first-wave pose; the elastic arm uses surface morphs, not shoulder rotation. The original wave remains in `Fibu.Proportions.usdz`.

## Food belongs to the game

There is **no baked food mesh**, bread placeholder, inventory item, or automatic feeding action in the USDZ or Blender review scene. `FoodSocket` is an empty, animated transform following the actual elastic hand. The original `Hand_R_end` bone stays fixed and is NOT the correct attachment for this morph-driven arm.

The socket follows a rolling palm contact as the hand expands; its center is 0.11 preview units above the surface for the suggested 0.22-diameter item. Normalize a different food visual to that grip size or supply a per-food local adjustment.

On scene load, stop automatic playback of the imported eating action and hold its time-zero pose. Start it only after a manual tap on a ready food.

Local Codex should implement this sequence for that tap:

1. Reserve the tapped food and guard against a second feed starting while eating is in progress. Load/clone that food's actual in-game visual (model or textured sprite), preserving the inventory's original asset.
2. Apply animation time zero before making the selected food visible. Parent the food instance under `FoodSocket` once at the start, center its grip pivot at socket-local origin, and apply the food's intended local scale/orientation. The socket already follows the animated hand. Do not reparent the item every frame or also apply a hand-bone transform.
3. Play the eating action and expression/morph/socket tracks on one clock. At zero-based runtime frame 29 (Blender review frame 30; 0.9667 seconds), hide/remove the attached food exactly once and call the app's consumption logic once. The animation asset itself does not change inventory or rewards. `foodVisible` in the timeline describes the selected game's item, not an embedded mesh.
4. On completion restore the smile/zero morphs and normal controller ownership. On interruption remove the temporary food instance, clear the action's morphs, restore smile/neutral pose, and resolve the reserved inventory item according to whether the bite already happened. Never consume again from both the bite event and completion callback.

`FoodSocket` is a sibling of `Fibu_body` in the original skeleton space. Its transforms are authored in the USDZ. If native import does not retain that track, create an empty sibling there and interpolate `foodSocketPosition` from the version 2 timeline. Use either the imported socket animation or the explicit timeline, not both. Positions retain original runtime units; the whole character wrapper transform must be applied once. `skeletonUnitsPerPreviewUnit` and `suggestedFoodDiameterSkeletonUnits` help size diverse food models. These are starting dimensions; each food may need its own grip pivot/scale.

## Delivered files

- `Assets/Models/FibuEating/Fibu.Eat.usdz`: body, new facial/arm targets, six fitted mouth meshes, empty food socket, and revised eating action.
- `Assets/Models/FibuEating/EatingTextures/`: transparent mouth art and separate NoSmile skin derivatives. Original/supplied skins use different registered masks; leopard uses a fur exemplar patch. Preserve all artist originals and review repaired pattern areas. Newer Mac-only skins need derivatives too.
- `timeline.json`: version 2; expression names, cheek/swallow and arm weights, empty socket positions, selected-food visibility, one bite event, and timing.
- `arm-region.json`: source vertex IDs allowed to move with the arm, fixed seam counts, helper-pose expansion settings. `face-anchors.json`: version 1 barycentric anchors on source body triangles. Imported SceneKit geometry may reindex UV-seam vertices; remap source IDs before reconstructing anchors.
- `validation.json`, `eating-preview.gif`, `expressions.png`, angle/profile/back views and skin sheet: review evidence.
- `Assets/Blender/FibuEating/Fibu.EatingPreview.blend`: packed review bake, frames 1–85, with an empty food socket. See source README before exporting; this bake is not the runtime rig.

## Native loader checks

Verify the skeletal clip, all FOUR body morph channels, TWO face channels, exclusive `Face_smile/open/lick/chew/swallow/happy` visibility, and `FoodSocket` movement in SceneKit. If native USD import omits channels, drive `SCNMorpher` weights and expression `isHidden` from version 2 timeline fields on the same clock. Set each body/face morpher’s `calculationMode` to `.additive`; the tracks are additive offsets from the approved surface. Resolve target names/indexes explicitly and update all six face morphers so expression switches retain the current facial deformation. Do not crossfade overlapping dark mouth decals.

Skin selection changes only the body's diffuse image to the corresponding NoSmile derivative. Mouth materials remain separate, transparent, depth-tested, and single-sided; the patch must follow the surface rather than billboard. Verify no rectangular shadow or doubled painted mouth.

Pause competing procedural body/arm/idle/walking/wave deformations during the one-shot action so they cannot twist the fixed torso or fight the elastic shapes. Check the selected game's food from start to bite, first-frame attachment, reentry/interruption, all local skins, return to idle, front/side/back visibility, grounding and performance. Build both schemes and run relevant existing checks if integrating. Keep Watch unchanged.

Cloud validation evaluates all 85 exported samples, proves the torso stays fixed within floating-point tolerance, checks unchanged skeleton/rest geometry/UVs/binds/weights, arm isolation, targets/normals, expression exclusivity, food-free geometry, socket tracks, grounding and package dependencies. Native SceneKit import and manual tap-to-feed behavior require local verification.
