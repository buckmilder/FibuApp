"""Blender --background HabitatExpansion.blend --python demo.py."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;scene=bpy.context.scene
for o in scene.objects:
    if o.type=='MESH' and o.name!='Plane':o.hide_render=True
def place(name,loc,scale=(1,1,1)):
    src=bpy.data.objects[name];o=src.copy();o.data=src.data;bpy.context.collection.objects.link(o)
    o.hide_render=False;o.location=loc;o.scale=scale;return o
place('meadow_platform',(0,0,0))
place('foliage_round_tree',(.25,2.85,1))
place('foliage_young_tree',(3.5,3.35,1))
place('foliage_shrub',(3.7,.5,1))
for i in range(3):place('limestone_single',(1.8,i*.9,1),(.78,.68,.13))
for x,y in [(-.1,.0),(.7,.25),(3.3,.0),(3.8,1.5),(2.9,3.8),(-.1,1.6),(1.0,3.7),(3.7,2.4)]:
    o=place('foliage_grass_fluffy',(x,y,1));o.rotation_euler.z=(x+y)*2
for x,y in [(.1,.6),(1,1),(3.0,1.6),(2.8,3.3)]:place('foliage_grass_small',(x,y,1))
for o in scene.objects:
    if o.type=='LIGHT':o.location=(0,-3,10);o.data.energy=1600;o.data.size=8
cam=scene.camera;cam.location=(9,-12,10);cam.rotation_euler=(Vector((1.7,1.6,1.25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=8.8
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.cycles.samples=32
scene.render.filepath=str(ROOT/'generated'/'habitat-demo.png')
bpy.ops.render.render(write_still=True)
