import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;scene=bpy.context.scene
for o in scene.objects:
    if o.type=='MESH' and o.name!='Plane':o.hide_render=True
for i,theme in enumerate(['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']):
    o=bpy.data.objects[theme+'_single'];o.hide_render=False;o.location=((i%3)*1.6,(i//3)*1.6,0)
cam=scene.camera;cam.location=(8,-11,10);cam.rotation_euler=(Vector((1.6,1.6,.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=7.1
for o in scene.objects:
    if o.type=='LIGHT':o.location=(0,-3,9);o.data.energy=1500;o.data.size=8
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.cycles.samples=24;scene.render.filepath=str(ROOT/'generated'/'materials.png');bpy.ops.render.render(write_still=True)
