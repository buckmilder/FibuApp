import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';d=json.loads((OUT/'previews.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scale=2.7/d['height'];floor=d['floor']
mat=bpy.data.materials.new('Original skin');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'source/0/Feeb_skin.png'));tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
for i,(name,pose) in enumerate(d['poses'].items()):
    # Same normalization for every clip: grounded sitting/lying keep their actual relative height.
    pts=[(p[0]*scale,p[1]*scale,(p[2]-floor)*scale) for p in pose['points']]
    angle=math.pi/2 if name=='LayDown' else math.pi/4 if name=='Sit' else 0
    pts=[(x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),z) for x,y,z in pts]
    cx=(min(p[0] for p in pts)+max(p[0] for p in pts))/2;cy=(min(p[1] for p in pts)+max(p[1] for p in pts))/2
    pts=[(x-cx,y-cy,z) for x,y,z in pts]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(pts,[],pose['faces']);mesh.update()
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.location=((i%4-1.5)*3.0,0,(1-i//4)*3.6)
    uv=mesh.uv_layers.new(name='Skin')
    for j,v in enumerate(pose['uv']):uv.data[j].uv=v
    for p in mesh.polygons:p.use_smooth=True
    mesh.materials.append(mat)
world=bpy.data.worlds.new('Studio');world.use_nodes=True;scene.world=world;world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='AREA',location=(0,-12,4));light=bpy.context.object;light.rotation_euler=(Vector((0,0,3.2))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=2600;light.data.size=10
bpy.ops.object.camera_add(location=(0,-20,5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,3.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13.5;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=2000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'poses.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'MotionPoseReview.blend'));bpy.ops.render.render(write_still=True)
