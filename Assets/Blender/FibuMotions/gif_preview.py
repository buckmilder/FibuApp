"""Render sampled, evaluated USD poses from generated/gif-data.json."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';d=json.loads((OUT/'gif-data.json').read_text());scale=2.7/d['height']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene
mesh=bpy.data.meshes.new('Fibu');mesh.from_pydata(d['clips']['Jump'][0],[],d['faces']);mesh.update();body=bpy.data.objects.new('Fibu',mesh);scene.collection.objects.link(body)
uv=mesh.uv_layers.new(name='Skin')
for i,v in enumerate(d['uv']):uv.data[i].uv=v
for p in mesh.polygons:p.use_smooth=True
m=bpy.data.materials.new('Original skin');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'source/0/Feeb_skin.png'));m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));bpy.context.object.data.materials.append(bpy.data.materials.new('Floor'))
world=bpy.data.worlds.new('Studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[1].default_value=.6
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=750;bpy.context.object.data.size=5
bpy.ops.object.camera_add(location=(4,-8,4));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.2;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.resolution_x=480;scene.render.resolution_y=480;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for name,frames in d['clips'].items():
    folder=OUT/(name+'-frames');folder.mkdir(exist_ok=True)
    for i,points in enumerate(frames):
        for v,p in zip(mesh.vertices,points):v.co=(p[0]*scale,p[1]*scale,(p[2]-d['floor'])*scale)
        mesh.update();scene.render.filepath=str(folder/f'{i:02d}.png');bpy.ops.render.render(write_still=True)
