# Habitat-only replacement handoff

Import **codex/habitats-only**, not the mixed codex/asset-handoff branch. This branch starts from shared main and adds habitat assets/sources only. No revised Fibu, motion clips, skin changes or Swift changes are included.

## Local task

Replace the entire built-in habitat catalog with exactly these three 9×9 habitats: garden, pond, camp. Use catalog.json and the three Assets/Models/habitat_*.usdz files. Update existing resource references, selector entries and thumbnails; do not append another three alternatives to the old catalog. Map obsolete selected habitat IDs to garden without clearing unrelated preferences such as selected skins. Preserve local uncommitted work and all current character/animation code.

These replacements have stacked terrain with top surfaces at Y=1,2,3m and two stairways per scene. The garden has a raised pergola terrace and tree corner; pond has a raised fountain bank and tree corner; camp has a raised timber deck and upper tree ledge. The quarter-height stairs provide the intended route between levels. The center fountain water remains static geometry.

Adapt movement to the selected habitat's actual horizontal bounds and surface height. Read terrace-layout.json; use walkable surface queries/raycasting for stairs and prop tops. Do not clamp Fibu to one flat Y. Exclude pond water, vertical cliff faces, fire and furniture from destinations; do not allow a straight path to cut through a cliff just because the destination is on top. Grid metadata is terrain support, not a finished pathfinder or collision mesh. Suggested spawn [4,1.13,-0.45] is before character-container scale/grounding adjustments.

Load a scene at one common tile scale and check character proportions, camera framing at all elevations, shadows, texture appearance, stair traversal, and ground contact. Scene geometry is Y-up meters; rows map to -Z. Base X bounds [-0.5,8.5], Z [-8.5,0.5]. The source Blender file packs its textures; each runtime USDZ embeds its maps.

Run both simulator builds and existing movement/camera/skin checks, then visually inspect each habitat with the current Fibu. Watch remains on its current asset; any habitat rendering on Watch requires a separate performance/conversion check. Xcode, SceneKit import and gameplay traversal cannot be validated in this Linux workspace.

## Evidence and scope

Export packages pass finite indexed geometry, normal/UV/material, dependency and archive checks. All 243 terrain grid columns were checked against exported geometry: expected 1/2/3 elevations and pond openings. Eight stair meshes per habitat were checked separately. Previews reflect the terraced scene. manifest.json records hashes and triangle counts.

Character/rig redesign is paused. Do not import the experimental refined character or sitting/eating/other animation files from the mixed branch as part of this habitat task.

Day/night belongs to local SceneKit runtime work: change sun/ambient/environment, shadows, sky and lantern lights/emission over time. Texture colors do not contain baked sun shadows. Studio preview lighting is not shipped scene lighting. No day/night clock or behavior is implemented by this delivery.
