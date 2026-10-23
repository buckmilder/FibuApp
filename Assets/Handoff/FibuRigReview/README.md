# Fibu neutral skeleton inspection

The user has put the walking candidate ON HOLD because of lower-torso deformation. Do not integrate or activate `Assets/Models/FibuWalk/Fibu.Walk.usdz` based on the earlier handoff. No app model was changed by the cloud work. If the local app already integrated that candidate, the local agent should restore its previous working locomotion/model while preserving unrelated work.

These diagrams read `Assets/Models/Fibu.Proportions.usdz` directly at original neutral sample 0. They do not use the rejected walk. The model has 32 original joints. Diagrams show actual evaluated joint centers and parent connections projected over its actual neutral surface. Torso chains are gold, limbs are blue. Coincident root helper joints are omitted from the diagram; all 32 paths/parents/positions remain in `joint-centers.json`. Left and right chains overlap in the side view. Diagram names are friendly labels: Hip joint = Thigh, Knee = Calf, Ankle = Foot. This is an inspection view, not an anatomy redesign or a claim that the rig is correctly placed or weighted.

`Assets/Blender/FibuRigReview/Fibu.SkeletonReview.blend` contains the evaluated neutral mesh plus a selectable, in-front inspection armature. Joint heads and hierarchy match the source. Branch and leaf bone tails are visualization conventions; this reconstructed inspection armature is not a replacement export rig. The mesh is not rebound or modified by this inspection.

Regenerate with Python + numpy/usd-core and Blender:

```sh
python3 Assets/Blender/FibuRigReview/extract.py
blender -t 4 --background --factory-startup --python Assets/Blender/FibuRigReview/render.py
python3 Assets/Blender/FibuRigReview/diagram.py
```

Use `PYTHONPATH` for usd-core if it is installed separately. Pillow and DejaVu Sans are used by the diagram labels. No Swift, skin, animation or runtime model is changed by this inspection.
