# Sky & Atmosphere v1

The six initial presets are complete visual moods, not six copies of a habitat. A habitat stores one editable `environment` dictionary. Geometry, object placements and construction bounds are independent. There is no automatic day/night clock in this delivery.

## Authoring

Open **Sky & Atmosphere**. Preset buttons include thumbnails rendered from the actual procedural backgrounds. Controls update the viewport immediately. Save/duplicate named custom presets, reload them through Saved presets, or revert to the settings present when the panel opened. Habitat Save/Save As stores the current settings regardless of whether they were saved as a named preset. Undo/redo includes environment edits.

Optional panoramic art must be equirectangular (normally 2:1). Import PNG/JPEG/HDR/EXR; the editor validates that it can decode the image, copies it to `Assets/Habitats/SkyArt/<content-hash>.<extension>`, and saves a relative reference. Commit that file with the habitat. Imported panoramas replace procedural sky/cloud/landscape rendering, while sun, ambient and fog remain controlled by the environment. Missing artwork is reported when a habitat opens; the reference is preserved and a procedural fallback appears.

Custom preset files are portable settings snapshots under `Assets/Habitats/SkyPresets/`. Built-in defaults are exported into `assets/skies/presets.json`; regenerate with `godot --headless --path Tools/HabitatEditor --script tests/export_sky_definitions.gd`. A level is not linked live to its named preset, so modifying one preset does not rewrite other levels.

## Serialized fields

All fields live under the existing habitat `environment` key. `version` is 1. `preset` is a starting-point identifier and `name` a display name. Fully resolved settings are stored when editing or choosing a preset. Empty legacy `{}` resolves to Sunny Highlands. Unknown keys are retained; unsupported atmosphere versions are rejected.

| Fields | Meaning / units |
|---|---|
| `sky_top`, `horizon`, `lower_sky` | sRGB hex RGB colors, no alpha |
| `cloud_color`, `landscape_tint`, `fog_color` | sRGB hex RGB colors |
| `sun_color`, `ambient_color` | sRGB hex RGB light colors |
| `sun_azimuth`, `sun_elevation` | degrees; light Euler rotation `[-elevation, azimuth, 0]`, Godot directional emission along local -Z |
| `sun_energy` | direct-light multiplier, UI 0–4 |
| `ambient_energy` | ambient multiplier, UI 0–2 |
| `cloud_density`, `cloud_softness` | normalized 0–1 |
| `cloud_motion`, `cloud_speed` | optional motion flag and noise-space units/second; default motion off |
| `fog_density` | nonvolumetric exponential distance fog density; 0–0.05 |
| `fog_height`, `fog_height_density` | height-fog reference in meters and falloff density; zero density disables height component |
| `landscape_visible` | show/hide the procedural silhouette layers |
| `landscape_kind` | 0 mountains, 1 forest, 2 mesas, 3 icy mountains |
| `background_rotation` | degrees around Y; panorama rotation or procedural azimuth offset |
| `horizon_offset` | normalized vertical direction offset, default 0.55; art direction for an angled diorama camera, not a world-height limit |
| `stars`, `moon` | star brightness 0–2; moon brightness 0–1 |
| `haze` | silhouette color blending with horizon, 0–1 |
| `panorama` | empty for procedural, otherwise path relative to the authored habitat content root, e.g. `SkyArt/abc.png` |

Colors convert to linear rendering space in the shader/light pipeline. The UI exposes colors, lighting, clouds, fog, silhouette style/visibility/tint, background rotation, and horizon framing. The default source presets and rendered reference images are checked in alongside the shader.

## Rendering design

`HabitatAtmosphere` owns a WorldEnvironment, one DirectionalLight3D and a shared sky ShaderMaterial. It has no construction or physics objects. All backdrop layers are evaluated from normalized view direction; camera position/height does not move the habitat into a sky dome or collide with a finite background.

The shader uses periodic integer angular harmonics for three silhouette bands, directional 3D noise for soft clouds, a deterministic star field, and a small moon disk/halo. Forest and mesa modes alter the silhouette profile; frozen mode adds sharper peaks and pale caps. Directional sampling avoids a pasted panorama seam. The shifted artistic horizon keeps backgrounds visible when looking down on the diorama. Extreme top-down views naturally show mostly lower atmosphere; adjust horizon offset to change composition.

No physics layers, 9×9 occupancy limits, or vertical construction bounds are added by backgrounds. Background rotation and camera orbit leave authored geometry unchanged. Editor and desktop Preview use the same environment module and parameters.

Compatibility renderer is supported. No volumetric fog, detailed distant landscape meshes, or Forward+-only features are used. Ambient lighting is an explicit color, reflections from sky radiance are disabled, sky radiance size is 32 and processing is incremental. Optional cloud movement updates its phase at at most 10 Hz; there is no shader TIME dependency. Settings edits update lighting, not texture bakes. Native-device performance has **not** been measured; these choices are a lightweight starting point, not an iPhone performance guarantee.

## Native Swift and later day/night

Fibu is a native Swift/SceneKit app. Godot shaders and WorldEnvironment resources cannot be imported directly. Local Codex should preserve/decode the settings and either port the directional shader to a native background renderer or bake an equirectangular panorama per selected mood. Apply matching native directional/ambient lights and fog. Godot's fog/tonemapping and SceneKit's differ, so visual comparison against the six reference renders is required; pixel-identical output is not claimed. User-imported panoramas can be reused directly with the native sky background, with orientation verified.

An automatic cycle can later interpolate numeric fields and colors between time-of-day settings while leaving terrain and assets unchanged. Treat discrete landscape type and panoramic artwork separately from those continuous values. A painted panorama may need day/night artwork or a blending renderer; procedural settings do not require separate habitat copies. Lantern activation/emission is also native runtime work, not currently part of the sky editor.

## Validation

Headless checks cover all presets, immediate settings/light updates, geometry/node isolation, habitat save/reload, undo/redo, optional cloud motion, preview continuity, invalid values, preset save/duplicate/revert, imported panorama copying/application, and missing-art fallback. `tests/render_skies.gd` renders the six actual preset thumbnails and larger reference images using the Compatibility renderer; run it with a graphical display. Native Mac UI and iOS rendering/performance remain local verification tasks.
