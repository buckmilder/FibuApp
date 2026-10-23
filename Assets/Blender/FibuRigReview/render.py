"""Render actual neutral geometry and project exact joint centers for an x-ray diagram."""
from pathlib import Path
import bpy,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';data=json.loads((OUT/'rig.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene
mesh=bpy.data.meshes.new('Approved neutral surface');mesh.from_pydata(data['points'],[],data['faces']);mesh.update();body=bpy.data.objects.new('Fibu - approved neutral',mesh);scene.collection.objects.link(body)
for p in mesh.polygons:p.use_smooth=True
m=bpy.data.materials.new('Muted surface for joint diagram');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.36,.44,.47,1);bs.inputs['Roughness'].default_value=.9;mesh.materials.append(m)
# A selectable neutral-pose armature made from actual source parent/child centers.
arm=bpy.data.armatures.new('Source skeleton - neutral joint centers');rig=bpy.data.objects.new('Fibu skeleton - 32 source joints',arm);scene.collection.objects.link(rig);rig.show_in_front=True;bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bones=[]
for i,j in enumerate(data['joints']):
 bone=arm.edit_bones.new(j['name']);bone.head=j['position'];children=[a for a in data['joints'] if a['parent']==i and (Vector(a['position'])-Vector(j['position'])).length>.001]
 bone.tail=children[0]['position'] if children else Vector(j['position'])+Vector((0,0,.045))
 if j['parent']>=0:bone.parent=bones[j['parent']]
 bones.append(bone)
bpy.ops.object.mode_set(mode='OBJECT');rig['note']='Joint heads and hierarchy copied from source; viewport bone tails for branches/leaves are display conventions. Not a replacement export rig.'
world=bpy.data.worlds.new('Diagram world');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.15,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8
for location,energy in [((-3,-4,6),450),((3,2,4),200)]:
 bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.data.energy=energy;o.data.size=4;o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.2;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
projection={}
for name,loc in [('front',(0,-8,1.35)),('side',(8,0,1.35))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
 projection[name]=[]
 for j in data['joints']:
  p=world_to_camera_view(scene,cam,Vector(j['position']));projection[name].append([p.x*640,(1-p.y)*800])
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'projection.json').write_text(json.dumps(projection));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Fibu.SkeletonReview.blend'))
