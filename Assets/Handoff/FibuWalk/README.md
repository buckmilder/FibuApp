> **ON HOLD — do not integrate or activate.** The user declined this walk candidate for now because of lower-torso distortion. The material below is retained for reference only. See `Assets/Handoff/FibuRigReview/` for inspection of the approved neutral skeleton.

# Fibu soft walk — review candidate

Branch: `codex/fibu-walk`. Runtime candidate: `Assets/Models/FibuWalk/Fibu.Walk.usdz`. Editable review: `Assets/Blender/FibuWalk/Fibu.WalkPreview.blend`. Authoritative generator: `Assets/Blender/FibuWalk/build.py`.

This is a separate in-place walk loop built on the approved proportions. The app, Watch asset, eating package, wave package, skins and artist mouth inputs are untouched. Preview GIFs show the actual evaluated runtime geometry. Playback in SceneKit and both simulator builds remain local tasks.

## Motion

A 0.9-second loop contains 54 intervals at 60 fps, plus the duplicate closing sample. Each foot supports the character for 60% of its cycle. The swing foot lifts about 0.108 units (4% of height) at a 2.7-unit character height, swings forward, then returns to support; the two feet alternate by half a cycle. Matching the actor speed to the timeline makes the planted ankle stationary in world space. The upper body shifts toward support, leans forward slightly, and twists gently against opposing arm swings. Delayed forearm motion adds overlap. Arms swing ±20° and move outward along a five-degree arc. Separate geodesically pinned arm shapes add up to 10% axial extension with compensating thickness, then 3.5% return compression for a rounder resting shape. The arm seam stays fixed and the hand remains full.

The continuous, short legs compress and extend along their lengths, with a small transverse volume compensation. Hard knee folding distorted the silhouette of these broad stumps. `WalkSquash` / `WalkStretch` add a restrained 1.2% vertical torso pulse with compensating width, fading out before the feet. The belly retains its rounded form throughout. All stretch is deliberate and bounded; support soles are corrected against evaluated skinning. The finished loop is a soft walk/waddle, not a run.

Mario-inspired design goals are clear contacts, opposing arm/leg motion, readable support, rounded arcs and controlled exaggeration. Direct video access was blocked in this environment; no particular Mario clip was frame-analyzed. An uploaded screen recording/GIF can guide a subsequent performance revision.

## Rig / compatibility

The original lower-body weights include shoulder/bicep influences. The candidate smooths leg/hip support weights in that region, then rebinds the affected mesh points so the exact approved visible neutral silhouette is retained. Upper-body weights at or above 1.25 normalized height remain untouched. Weight membership uses original leg influence to avoid treating low-hanging hands as legs. The original skeleton paths, bind/rest transforms, mesh topology, material and UV coordinates are retained; embedded artist texture bytes are unchanged. Mesh bind points, lower-body weights and corresponding normals are deliberately updated. Do not copy just this animation onto the older mesh and assume identical deformation.

The Blender file is a sample-by-sample geometry review bake with packed skin, cameras and lighting. It is not a replacement skeletal rig export. Regenerate the runtime package with `build.py`, not default Blender export of its 54 review shape keys.

The runtime asset contains the skeletal walk and six additive body morph targets (two torso and two per arm). `timeline.json` carries timing, speed, foot contacts, shape weights, source/package hashes and coordinate conventions. The walk has no new face expressions, food or inventory behavior. Artist PNG mouth art can stay on the fitted face patch; local integration must keep that patch aligned with the walking/deforming face.

## Rebuild

Python 3 requires numpy, scipy, Pillow and usd-core; Blender 4.3.2 was used. From repository root:

```sh
PYTHONPATH=/path/to/usd/python python3 Assets/Blender/FibuWalk/build.py
PYTHONPATH=/path/to/usd/python python3 Assets/Blender/FibuWalk/validate.py
PYTHONPATH=/path/to/usd/python python3 Assets/Blender/FibuWalk/check_blending.py
blender -t 4 --background --factory-startup --python Assets/Blender/FibuWalk/preview.py
python3 Assets/Blender/FibuWalk/package_preview.py
```

Omit `PYTHONPATH` if usd-core is installed in the selected Python. Generated intermediates are ignored. The independent validator reopens the delivered USDZ, checks dependencies/source integrity, unchanged topology/UV/texture/skeleton, exact neutral silhouette after rebind, normalized weights, bounded deformation, sample/half-sample grounding, loop closure and stance speed matching. `validation.json` records measured errors in canonical units at height 2.7. `check_blending.py` separately evaluates eased 0.2-second local-transform/morph blends at 0.6×, 1× and 1.4× speed and verifies an exact return to neutral and distance-driven phase across variable frame schedules. Its results are in `blend-review.json`; these are offline USD checks, not SceneKit or device results. Turns, terrain and native transition visuals remain local checks.

Read `LOCAL_CODEX_PROMPT.md` before native integration. Review the front/side loop with the user before activating it as the default walk.

## Tunable parameters

Edit `Assets/Blender/FibuWalk/parameters.json` and rebuild/export/revalidate. The values are also embedded in the handoff timeline. Distances without a fraction suffix use the canonical 2.7-unit character height.

| Parameter | Starting value |
| --- | --- |
| Full cycle | 0.9 s |
| Arm swing / outward arc | ±20° / 5° |
| Arm extension / return compression | up to 10% / 3.5% |
| Body bob, peak to peak | 1.5% of character height |
| Body lateral tilt | ±3° |
| Foot lift | 4% of character height |
| Primary torso deformation | 1.2%, compensated width |
| Idle/walk blend | 0.2 s (native integration) |

The configuration controls offline asset generation; the native loader may expose playback speed and transition duration without regenerating the asset. More arm swing, extension or foot lift requires revalidation and visual review. The current SceneKit controller still needs the local integration described in the handoff.
