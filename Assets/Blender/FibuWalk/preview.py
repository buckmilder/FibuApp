"""Editable Blender review bake from evaluated runtime USD sample data."""
from pathlib import Path
import bpy,json,math,os
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';data=json.loads((OUT/'preview-data.json').read_text());unit=data['unit'];floor=data['floor']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.fps=data['fps'];scene.frame_start=1;scene.frame_end=len(data['frames'])-1
# Preview loop omits the duplicated closing sample; export retains it.
def norm(p):return (p[0]/unit,p[1]/unit,(p[2]-floor)/unit)
mesh=bpy.data.meshes.new('Approved mesh');mesh.from_pydata([norm(p) for p in data['frames'][0]['points']],[],data['faces']);mesh.update();obj=bpy.data.objects.new('Fibu Walk — runtime evaluation',mesh);scene.collection.objects.link(obj)
layer=mesh.uv_layers.new(name='UV')
for loop in mesh.loops:layer.data[loop.index].uv=data['uv'][loop.index]
for poly in mesh.polygons:poly.use_smooth=True
mat=bpy.data.materials.new('Original preserved skin');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'source/0/Feeb_skin.png'));tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
obj.shape_key_add(name='Basis')
for i,row in enumerate(data['frames'][1:],1):
    key=obj.shape_key_add(name=f'Evaluated_{i:03d}');key.data.foreach_set('co',[v for p in row['points'] for v in norm(p)])
    for frame,value in [(i,0),(i+1,1),(i+2,0)]:key.value=value;key.keyframe_insert('value',frame=frame)
for curve in mesh.shape_keys.animation_data.action.fcurves:
    for k in curve.keyframe_points:k.interpolation='LINEAR'
neutral_key=obj.shape_key_add(name='ApprovedNeutral');neutral_key.data.foreach_set('co',[v for p in data['neutral'] for v in norm(p)]);neutral_key.value=0
obj['note']='Review bake. Author/export original rig with build.py, not default Blender shape-key export.'
world=bpy.data.worlds.new('Studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.6,.65,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));ground=bpy.context.object;m=bpy.data.materials.new('Ground');m.diffuse_color=(.11,.17,.17,1);ground.data.materials.append(m)
for loc,energy,size in [((-3,-4,6),450,4),((3,1,4),250,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.3
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.resolution_x=360;scene.render.resolution_y=400;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
view=os.environ.get('FIBU_WALK_VIEW','front');cam.location={'front':(.5,-8,2.7),'side':(8,0,2.5),'angle':(5,-7,3)}[view];cam.rotation_euler=(Vector((0,0,1.26))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Fibu.WalkPreview.blend'))
for view in ['front','side','angle']:
    cam.location={'front':(.5,-8,2.7),'side':(8,0,2.5),'angle':(5,-7,3)}[view];cam.rotation_euler=(Vector((0,0,1.26))-cam.location).to_track_quat('-Z','Y').to_euler()
    folder=OUT/view;folder.mkdir(exist_ok=True)
    for old in folder.glob('*.png'):old.unlink()
    scene.frame_set(1);neutral_key.value=1;scene.render.filepath=str(OUT/('idle-'+view+'.png'));bpy.ops.render.render(write_still=True);neutral_key.value=0
    for frame in range(1,len(data['frames']),2):
        scene.frame_set(frame);scene.render.filepath=str(folder/f'{frame:03d}.png');bpy.ops.render.render(write_still=True)
