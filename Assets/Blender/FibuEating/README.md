# Fibu eating — elastic arm, fixed torso

Separate review candidate based on approved `Fibu.Proportions.usdz`, SHA-256 `819ef67d0d86d2572fd0fc1c4d0eca611d516c514e297225beb1e12d1ba7f4b5`. No active app, Swift, Xcode, Watch, approved model, or artist source textures are changed. The user's original 2D motion reference is retained at `Assets/Source/FibuEatingReference.gif`.

## Motion design

The 2.8-second, non-looping eating action uses a fixed neutral skeleton. The feeding arm alone moves out in front of the torso and then curves up/across to the mouth, lengthening the forearm and expanding its cross sections before returning along the same path. The authoring helper keeps the shoulder/upper arm fixed; wrist translation supplies the extra reach. A geodesically pinned attachment seam and an explicit right-arm vertex region prevent torso, leg, and opposite-arm displacement. The face retains local cheek/swallow deformation. Neck nods, runtime shoulder rotation and the raised-hand flourish from the first pass were removed.

`elastic_arm.py` computes the arm-only deformation. It preserves the rest mesh and its UVs; runtime motion uses `ArmPrepare` and `ArmBite` morph targets. `CheekPuff` and `Swallow` are confined to facial support above the torso and excluded from the arm. Smooth position/normal targets accompany every morph. All original 32 joint paths, skeleton rest/bind transforms, approved mesh points/faces/UVs and skin weights remain intact.

The mouth is six transparent artworks on a curved, skinned 17×17 surface fitted to the face. It follows facial deformation, uses depth testing, and is not a billboard. NoSmile texture derivatives remove only each skin's registered painted-mouth region. Solid colors use local diffusion; leopard uses a neighboring fur exemplar. Artist originals and all pixels outside removal masks remain unchanged. Pattern repair and newer locally held skins need artist review.

## Food attachment

There is no food geometry in the animation or Blender review scene. The empty animated `FoodSocket` follows a surface contact that rolls from the front to the inner palm as the hand stretches, which no longer follows the static `Hand_R_end` bone during this action. The app must attach the model corresponding to the ready food the user manually taps, at time zero. It stays parented to the socket until the bite event at frame 29 (0.9667 seconds). The asset does not select, award or consume inventory. See the detailed local handoff for ownership/interruption behavior.

Timeline schema 2 intentionally replaces the first pass's hand-bone offset fields. It includes four body morph weights, expressions, socket position samples and bite timing. A single animation clock must own those tracks.

## Editable source and review bake

`build.py` is the authoritative authoring/export source. It starts with the approved USD skeleton and rest mesh, creates arm/facial targets and fitted mouth surfaces, then authors the USD action and empty socket. The new eating package contains the eating action; the original wave remains available in the approved proportions package.

`Fibu.EatingPreview.blend` packs materials, camera, lighting, empty socket, and 85 evaluated body/face samples baked to shape keys. Scrub frames 1–85 or play at 30 fps. This is a review bake, not a replacement native skeletal rig. Rebuilding overwrites it. Use build.py for runtime export, rather than default-exporting the baked shape keys over the original skeleton.

Dependencies: Python with numpy, scipy, Pillow, usd-core 26.11; Blender 4.3.2. From repository root:

```sh
TMPDIR=/tmp PYTHONPATH=/path/to/usd/python python Assets/Blender/FibuEating/build.py
PYTHONPATH=/path/to/usd/python python Assets/Blender/FibuEating/validate.py
blender -t 4 --background --factory-startup --python Assets/Blender/FibuEating/preview.py
FIBU_EAT_RENDER=animation blender -t 4 --background --factory-startup --python Assets/Blender/FibuEating/preview.py
blender -t 4 --background Assets/Blender/FibuEating/Fibu.EatingPreview.blend --python Assets/Blender/FibuEating/review.py
python Assets/Blender/FibuEating/deliver.py
```

Omit PYTHONPATH when dependencies are installed into the selected Python. Intermediates stay under ignored generated/. The exporter rejects a changed approved-model hash pending deliberate re-review.

Independent validation reopens the actual USDZ, evaluates all 85 morph/skinning samples, measures fixed torso vertices, checks arm isolation, static joint transforms, neutral return, normalized weights/normals, unchanged rest geometry and skin hashes, exclusive expression visibility, no food meshes, socket positions, grounding and resolved dependencies. Blender renders are review evidence; SceneKit/Xcode playback and manual tap-to-feed behavior remain to be verified on Mac.
