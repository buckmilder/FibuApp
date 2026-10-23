"""Render the delivered preview bake from angles and with every available skin."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';H=ROOT.parents[2]/'Assets/Handoff/FibuEating';scene=bpy.context.scene;cam=scene.camera
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.resolution_x=480;scene.render.resolution_y=520;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.frame_set(56)
for label,loc in [('angle',(5.5,-5.5,3)),('profile',(8,0,2.7)),('back',(0,8,3))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.45;scene.render.filepath=str(H/f'{label}.png');bpy.ops.render.render(write_still=True)
# Close views make the repaired smile area and independent mouth art easy to review.
body=bpy.data.objects['Fibu — approved proportions'];mat=body.data.materials[0];node=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');scene.frame_set(72)
cam.location=(.3,-8,2.35);cam.rotation_euler=(Vector((0,-.5,1.68))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.55;scene.render.resolution_x=320;scene.render.resolution_y=340
records=json.loads((OUT/'skins.json').read_text())['skins'];folder=OUT/'skin-reviews';folder.mkdir(exist_ok=True)
for row in records:
    node.image=bpy.data.images.load(str(OUT/'source'/row['file']));scene.render.filepath=str(folder/(row['id']+'.png'));bpy.ops.render.render(write_still=True)
