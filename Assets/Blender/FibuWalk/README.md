# Authoring Fibu's soft walk

See `../../../Assets/Handoff/FibuWalk/README.md` for design, parameters and runtime handoff. `build.py` authors the USD skeleton and six localized blend shapes from the approved model, including a neutral-preserving lower-body weight cleanup. `arm_shapes.py` pins the arm attachment region geodesically. `parameters.json` is the tuning source. `validate.py` independently reopens and evaluates the final package.

`preview.py` creates the packed Blender review file and front/side/three-quarter render sequences from evaluated runtime samples. That file is a review bake, not a skeletal authoring/export replacement. It includes an `ApprovedNeutral` shape key for comparison; leave it at zero when playing the walk. `package_preview.py` packages GIFs and pose sheets. Generated source extracts/sample caches/renders stay ignored under `generated/`.

No runtime code performs the authoring-time mesh fitting, graph search, LBS inversion or normal rebuilding. Native playback should use the baked skeleton/morph channels with one clock. SceneKit integration and motion blending are covered by the local prompt.
