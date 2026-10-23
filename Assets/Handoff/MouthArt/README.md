# Artist mouth flipbooks — cloud / local contract v1

This prepares future artist input. The included drawing template is BLANK and must not replace the current mouth art. No new artist animation or Swift player is activated by this delivery. The existing eating model, skin derivatives and animation files remain unchanged.

## Artist delivery

Recommended: fixed-size RGBA PNG sequences (512-square, or 1024-square for finer work) with a transparent background, a stable canvas/anchor, and explicit order/timing. The artist can upload a ZIP of numbered PNGs and provide FPS or durations in the chat; cloud Codex prepares the manifest. Do not make the user hand-edit JSON. The downloadable template ZIP contains a blank canvas, a separate registration guide, README and example manifest.

Preserve image pixels and placement as supplied. Do not trace, redraw, crop transparent borders, resize, quantize, recolor, retime or center by each frame's ink bounds. Original PNG bytes and the source manifest are copied exactly, verified by SHA-256. 3D projection naturally curves/foreshortens the art on Fibu's surface; exact source pixels do not imply identical screen pixels from every camera angle.

GIF import composites each complete displayed frame, including disposal behavior, into a full-size RGBA PNG. The original GIF is retained, its original timing is used, and decoded pixels are verified. A GIF's palette/transparency limitations cannot be undone, so PNG is the final-art preference. GIF loop metadata is retained as source information; action looping is an explicit manifest choice.

## Format

`mouth.json`: `format: "fibu-mouth-art"`, `version: 1`, `canvas: {width,height}`, `registration: {anchor_px:[x,y]}`, and `clips`. Each clip has a unique `id`, explicit `loop`, `end_behavior` (`hold_last` or `return_to_smile`), and ordered `frames` with `file` and positive finite `duration_ms`. Fractional milliseconds are allowed to represent rates such as 24 or 30 fps accurately. Frame paths are folder-relative PNGs; all must match the declared canvas and have RGBA pixels. See `Assets/Source/MouthArtTemplate/mouth.json`.

Registration is measured in pixels from the PNG's TOP LEFT. No frame-specific trimming offsets are permitted. Every image maps over the entire curved patch UV range. With the default center anchor use the existing fitted mouth mesh. For a different anchor, refit the patch so its local horizontal position is `(u-anchor_x/width)*patch_width`, vertical position is `(v-(1-anchor_y/height))*patch_height`; preserve full UV coverage and do not transform the image to compensate. The existing patch is approximately 0.67 × 0.61 preview units at a 2.7-unit character height.

## Cloud import

Python 3 + Pillow is required. From repository root:

```sh
python scripts/mouth-art/import_art.py /path/to/art-folder
python scripts/mouth-art/import_art.py /path/to/art-folder --output Assets/Models/MouthArt/my-art-v001
python scripts/mouth-art/import_art.py /path/to/reference.gif --gif --clip eat --output /tmp/decoded-mouth-art
python scripts/mouth-art/test_import.py
```

Choose a new version folder; existing outputs are never overwritten. PNG import produces a hash/timing report and copies all supplied frame bytes unchanged. Missing/inconsistent canvases, opaque RGB exports, invalid durations and escaping frame paths are rejected before copying. A decoded GIF folder can then be imported through the PNG path. The importer does not alter `Fibu.Eat.usdz` or native resource references.

## Local Codex implementation when final art arrives

1. Bundle the imported art directory, `mouth.json`, import report and original supplied art. Resolve paths inside that directory and load RGBA frames with their alpha/sRGB colors intact. Keep artist inputs unchanged. Do not generate another interpretation of the art.
2. Display one existing curved mouth patch (for example `Face_smile`), hide the other generated `Face_*` surfaces, and swap its diffuse image according to the clip's frame durations. The patch remains skinned/fitted to the surface. It does not billboard. Use constant/unlit color as the artist preview default to avoid recoloring their mouth with scene lighting. Keep depth testing, correct transparent edges, single-sided visibility and body occlusion; invisible pixels must not create a rectangular occluder.
3. Disable the old expression-visibility/texture controller while a custom-art clip owns the mouth. Keep body `CheekPuff`/`Swallow` plus arm shapes running independently using additive morphs. Swap only the mouth image, never the body skin material. All skins use the same mouth frames with their existing NoSmile body derivatives.
4. Play at rate 1.0 with the manifest durations. Select a frame by cumulative duration, not assumed uniform FPS. At the exact boundary advance to the next frame. For a one-shot shorter than its owning action, hold the last frame by default. Never silently stretch its timing to fit eating. Longer art also keeps its timing; hold the body at its returned neutral pose until the art action finishes, or obtain a deliberate edit from the artist.
5. For eating, use the same action clock as body/arm and `FoodSocket`: attach the manually tapped food at time zero, remove it once at the bite event (0.9667s), and let mouth art use its own cumulative timing on that clock. If artist mouth-bite timing differs, coordinate a deliberate timeline revision; do not silently move either event. No autoplay feeding and no baked food.
6. Cache or preload a bounded set of frames to avoid texture-upload stalls, while preserving source dimensions/pixels. A future atlas is optional only if it is lossless, unscaled, correctly padded and visually verified. Do not substitute GIF playback widgets for a surface-fitted 3D mouth.
7. Check all skins, frame positioning, soft alpha edges, variable durations, loops/one-shots, return/interruption, food timing and front/side/back views in the iPhone simulator. Build both schemes if integrating. Keep Watch assets unchanged pending a separate review.

Cloud validation covers source preservation and the import format. Native flipbook-player implementation and SceneKit verification remain local work after final art is supplied.
