"""Render original/candidate in the SAME evaluated first-frame pose and skin."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';d=json.loads((OUT/'posed.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
base=d['before']['points'];bottom=min(p[2] for p in base);height=max(p[2] for p in base)-bottom;scale=2.7/height
mat=bpy.data.materials.new('Original skin');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
image=bpy.data.images.load(str(OUT/'original/0/Feeb_skin.png'));tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
objects=[]
for i,name in enumerate(['before','after']):
    data=d[name];v=[(p[0]*scale,p[1]*scale,(p[2]-bottom)*scale) for p in data['points']]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],data['faces']);mesh.update()
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.location.x=(i-.5)*2.1;objects.append(o)
    uv=mesh.uv_layers.new(name='SkinUV')
    for j,p in enumerate(data['uv']):uv.data[j].uv=p
    for p in mesh.polygons:p.use_smooth=True
    mesh.materials.append(mat)
floor=bpy.data.materials.new('Backdrop');floor.diffuse_color=(.19,.23,.21,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.025));bpy.context.object.data.materials.append(floor)
world=bpy.data.worlds.new('Daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=700;bpy.context.object.data.size=5
bpy.ops.object.camera_add(location=(0,-8,3.5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.2;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for label,angle in [('front',0),('side',math.pi/2),('back',math.pi)]:
    for o in objects:o.rotation_euler.z=angle
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
