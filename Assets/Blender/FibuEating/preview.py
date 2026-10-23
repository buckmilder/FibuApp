"""Blender review scene, baked from the authoritative USD skeletal/morph samples."""
import bpy,json,math,os,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';data=json.loads((OUT/'preview-data.json').read_text());TEX=OUT/'source/EatingTextures'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.fps=data['fps'];scene.frame_start=1;scene.frame_end=len(data['frames']);unit=data['unit'];floor=data['floor']
def norm(p):return (p[0]/unit,p[1]/unit,(p[2]-floor)/unit)
def material(name,path=None,color=None,alpha=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
    if path:
        t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path));t.image.pack();m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color'])
        if alpha:m.node_tree.links.new(t.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=True
    else:bs.inputs['Base Color'].default_value=color
    return m
def meshobj(name,points,faces,uv,facevarying=False):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([norm(v) for v in points],[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    layer=mesh.uv_layers.new(name='UV')
    for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.index] if facevarying else uv[loop.vertex_index]
    for p in mesh.polygons:p.use_smooth=True
    return obj
def bake(obj,field):
    obj.shape_key_add(name='Basis')
    for i,row in enumerate(data['frames'][1:],start=1):
        key=obj.shape_key_add(name=f'USD_Sample_{i:03d}');flat=[v for p in row[field] for v in norm(p)];key.data.foreach_set('co',flat)
        for frame,value in [(i,0),(i+1,1),(i+2,0)]:key.value=value;key.keyframe_insert('value',frame=frame)
    for curve in obj.data.shape_keys.animation_data.action.fcurves:
        for k in curve.keyframe_points:k.interpolation='LINEAR'
body=meshobj('Fibu — approved proportions',data['frames'][0]['body'],data['faces'],data['uv'],True);body.data.materials.append(material('Skin — separate from expressions',TEX/'Skin.Original.NoSmile.png'));bake(body,'body')
body['source']='Assets/Models/Fibu.Proportions.usdz';body['animation_note']='Baked skeletal + facial samples for review; use build.py for original USD skeleton, not Blender default rig export.'
baseface=meshobj('Surface fitted mouth',data['frames'][0]['face'],data['overlayFaces'],data['overlayUV']);bake(baseface,'face');baseface.data.materials.append(material('Mouth.smile',TEX/'Mouth.smile.png',alpha=True))
faceobjects=[]
for i,name in enumerate(['smile','open','lick','chew','swallow','happy']):
    obj=baseface if i==0 else bpy.data.objects.new('Mouth.'+name,baseface.data)
    if i:scene.collection.objects.link(obj)
    obj.name='Mouth.'+name;obj.material_slots[0].link='OBJECT';obj.material_slots[0].material=material('Expression '+name,TEX/f'Mouth.{name}.png',alpha=True)
    for row in data['frames']:
        hidden=row['expression']!=name;obj.hide_render=hidden;obj.hide_viewport=hidden;obj.keyframe_insert('hide_render',frame=row['frame']+1);obj.keyframe_insert('hide_viewport',frame=row['frame']+1)
    obj['surface_offset']=.0035;obj['not_a_billboard']=True;faceobjects.append(obj)
# No food geometry. The game attaches the selected inventory item to this empty.
bpy.ops.object.empty_add();socket=bpy.context.object;socket.name='FoodSocket';socket.empty_display_type='SPHERE';socket.empty_display_size=.06
for row in data['frames']:
    socket.location=norm(row['socket']);socket.keyframe_insert('location',frame=row['frame']+1)
for curve in socket.animation_data.action.fcurves:
    for k in curve.keyframe_points:k.interpolation='LINEAR'
mat=material('Backdrop',color=(.12,.19,.18,1));bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.018));bpy.context.object.data.materials.append(mat)
world=bpy.data.worlds.new('Soft studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55
for loc,energy,size in [((-3,-4,6),500,4),((3,1,4),350,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.9,-8,3.1));cam=bpy.context.object;scene.camera=cam;cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.45
scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('FIBU_EAT_SAMPLES','24'));scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=680;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.frame_set(1);bpy.context.view_layer.objects.active=body;bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Fibu.EatingPreview.blend'))
mode=os.environ.get('FIBU_EAT_RENDER','stills')
if mode=='animation':
    scene.cycles.samples=12;scene.render.resolution_x=520;scene.render.resolution_y=560
    folder=OUT/'frames';folder.mkdir(exist_ok=True)
    for old in folder.glob('*.png'):old.unlink()
    for f in range(1,scene.frame_end+1,2):
        scene.frame_set(f);scene.render.filepath=str(folder/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
    (OUT/'render-source.json').write_text(json.dumps({'packageSHA256':hashlib.sha256((OUT/'Fibu.Eat.usdz').read_bytes()).hexdigest(),'dataSHA256':hashlib.sha256((OUT/'preview-data.json').read_bytes()).hexdigest(),'frames':43},indent=2))
else:
    for label,time in [('neutral',0),('prepare',.4),('open',.65),('bite',.93),('lick',1.2),('puff',1.83),('swallow',2.1),('happy',2.35)]:
        if label not in os.environ.get('FIBU_EAT_STILLS','neutral,prepare,open,bite,lick,puff,swallow,happy').split(','):continue
        scene.frame_set(round(time*data['fps'])+1);scene.render.filepath=str(OUT/f'{label}.png');bpy.ops.render.render(write_still=True)
    cam.location=(5.5,-5.5,3);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.frame_set(29);scene.render.filepath=str(OUT/'puff-angle.png');bpy.ops.render.render(write_still=True)
