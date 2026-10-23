# Fibu eating and surface-fitted expressions

A separate review candidate based on the approved `Fibu.Proportions.usdz` (SHA-256 `819ef67d0d86d2572fd0fc1c4d0eca611d516c514e297225beb1e12d1ba7f4b5`). No Swift, Xcode, Watch, active character resource, or artist skin originals are changed. The user’s reference is preserved at `Assets/Source/FibuEatingReference.gif`; it is a motion reference, not executable instructions.

## What is authored

- A 2.8-second, non-looping, 30 fps eating gesture on the original 32-joint runtime skeleton: hand to mouth, bite, hand raised, cheek puff, swallow, happy expression, and return to neutral. Timing gives the original two-second reference a longer satisfied finish.
- Six transparent mouth illustrations: smile, open, lick, chew, swallow, happy. Each is mapped to a curved 17×17 mesh sampled from the actual face, not a camera-facing billboard. The patch uses interpolated body joint weights and the same facial morphs. Exposed skin is visible through transparent areas. Back faces are culled; normal depth testing lets the body occlude the mouth.
- Two genuine surface morphs: `CheekPuff` and `Swallow`. They affect the face locally, not the belly, legs, bone scale, or approved rest proportions. Smooth vertex normals and facial normal offsets are included.
- Separate, automatically repaired copies of the original and eleven available source skins, removing only a registered removal mask around each painted mouth. Artist originals are unchanged, and all pixels outside that mask remain identical. Solid skins use local diffusion and leopard uses a neighboring fur exemplar patch. Pattern repair inside the mask needs visual/artist review; newer skins available only on the Mac are not included.
- A replaceable golden bread placeholder. The preview includes decorative scores; the USD placeholder is a simple ellipsoid. Its authored position follows the eating hand with an animated grip offset. The food disappears at the bite, approximately 0.967 seconds. No app inventory, reward, health, or feeding action is implemented.

## Source versus review scene

`build.py` is the authoritative procedural animation source. It starts from the approved USD skeleton, solves bounded hand reaches, authors the skeletal clip, fitted facial meshes, normal/position morph targets, expression visibility, food track, and USD materials. It preserves the approved body's rest points, faces, UVs, weights, bind transforms, joint paths, and rest skeleton. The eating package's animation is the NEW eating clip; the original wave remains in `Fibu.Proportions.usdz`, not as a second clip in this package.

`Fibu.EatingPreview.blend` is a packed, portable review scene with the 85 evaluated skeletal/facial samples baked to shape keys, keyed expression visibility, lighting, camera and placeholder food. Scrub frames 1–85 or play at 30 fps. The skin and mouth are separate materials. This bake is for inspection and timing/art experiments, not a replacement Blender runtime rig. Rebuilding regenerates it. Use `build.py` and the USD skeleton to revise/export motion; do not default-export the baked preview over the native skeleton.

## Rebuild

Dependencies: Python 3 with numpy, scipy, Pillow and usd-core 26.11; Blender 4.3.2. From repository root, after preparing the cloud dependencies or equivalent local packages:

```sh
TMPDIR=/tmp PYTHONPATH=/path/to/usd/python python Assets/Blender/FibuEating/build.py
PYTHONPATH=/path/to/usd/python python Assets/Blender/FibuEating/validate.py
blender -t 4 --background --factory-startup --python Assets/Blender/FibuEating/preview.py
FIBU_EAT_RENDER=animation blender -t 4 --background --factory-startup --python Assets/Blender/FibuEating/preview.py
```

Omit `PYTHONPATH` if packages are installed into the chosen Python. Generated intermediates are ignored. `deliver.py` copies the validated outputs and constructs the GIF/contact sheet after renders finish. Run it with that same Python. The delivered model is `Assets/Models/FibuEating/Fibu.Eat.usdz`; see the local handoff under `Assets/Handoff/FibuEating/`.

## Verified and pending

The exporter evaluates all 85 samples, including facial offsets before skinning. The feet remain grounded. Fit error from the facial mesh to the animated barycentric surface is below 0.004 preview units at a body height of 2.7. Independent validation checks the packaged skeleton against the approved model, identical body rest topology/UVs/weights/binds, facial targets and normals, exclusive expression visibility, normalized joint weights, neutral end pose, one bite event, and package dependencies.

Blender previews are visual evidence, not a SceneKit playback test. Native USD facial morph/visibility import and animation binding must be checked on Mac. A versioned timeline and surface anchors are supplied for explicit runtime control if the importer omits tracks. Do not silently claim an iPhone or Watch test from these cloud checks.
