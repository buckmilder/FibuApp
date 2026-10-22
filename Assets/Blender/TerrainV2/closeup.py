"""Run Blender --background FibuTerrainV2.blend --python closeup.py."""
import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
scene=bpy.context.scene
for o in scene.objects:
    if o.type=='MESH' and o.name!='Plane':
        o.hide_render=not o.name.endswith('_single')
for i,name in enumerate(['golden','forest','lime']):
    o=bpy.data.objects[name+'_single'];o.location=(i*1.55,0,0)
cam=scene.camera;cam.location=(5,-8,5)
cam.rotation_euler=(Vector((1.55,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=6
for o in scene.objects:
    if o.type=='LIGHT':o.location=(0,-3,7);o.data.energy=900;o.data.size=6
scene.render.resolution_x=1800;scene.render.resolution_y=950
scene.cycles.samples=48
scene.render.filepath=str(root/'generated'/'closeup.png')
bpy.ops.render.render(write_still=True)
