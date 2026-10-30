"""Import exact builder meshes to editable Blender, export paired GLBs, render studies."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];GEN=ROOT/'generated';DEST=REPO/'Assets/Models/SoftTerrain';HAND=REPO/'Assets/Handoff/SoftTerrain';scene=bpy.context.scene
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
materials={};objects={}
def material(name):
 if name in materials:return materials[name]
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.92;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(REPO/'Tools/HabitatEditor/assets/textures'/name));t.image.pack();m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color']);materials[name]=m;return m
for info in json.loads((GEN/'study-manifest.json').read_text()):
 data=json.loads((GEN/(info['id']+'.json')).read_text());points=[];faces=[];uv=[];normals=[];mi=[];mats=[]
 for surface in data['surfaces']:
  offset=len(points);points.extend([(p[0],-p[2],p[1]) for p in surface['points']]);uv.extend([(u,1-v) for u,v in surface['uv']]);normals.extend([(n[0],-n[2],n[1]) for n in surface['normals']]);tri=[surface['indices'][i:i+3] for i in range(0,len(surface['indices']),3)];faces.extend([(a+offset,c+offset,b+offset) for a,b,c in tri]);mi.extend([len(mats)]*len(tri));mats.append(material(surface['texture']))
 mesh=bpy.data.meshes.new(info['id']);mesh.from_pydata(points,[],faces);mesh.update();obj=bpy.data.objects.new(info['id'],mesh);scene.collection.objects.link(obj);objects[info['id']]=obj
 for m in mats:mesh.materials.append(m)
 for p,index in zip(mesh.polygons,mi):p.material_index=index;p.use_smooth=True
 mesh.normals_split_custom_set_from_vertices(normals);layer=mesh.uv_layers.new(name='UV')
 for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
 obj['generator']='fibu-soft-turf-v2; exact builder mesh';obj['triangles']=info['triangles'];obj['collision_note']='Decorative grass does not change logical soil support height. Do not auto-collide the visual mesh.'
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(DEST/(info['id']+'.glb')),export_format='GLB',use_selection=True,export_yup=True)
 obj.hide_render=True;obj.hide_set(True)
world=bpy.data.worlds.new('Neutral studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.40,.48,.52,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035));ground=bpy.context.object;m=bpy.data.materials.new('Backdrop');m.diffuse_color=(.12,.17,.18,1);ground.data.materials.append(m)
for loc,energy,size in [((-3,-4,8),700,5),((5,4,5),350,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.resolution_x=900;scene.render.resolution_y=760;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def render(name,ids,target,location,scale):
 for o in objects.values():o.hide_render=True;o.hide_set(True)
 for id in ids:objects[id].hide_render=False;objects[id].hide_set(False)
 cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(HAND/(name+'.png'));bpy.ops.render.render(write_still=True)
# Keep source overview organized while exporting module files with the original grid pivots.
for i,theme in enumerate(['forest','meadow','lime']):objects[theme+'_single'].location=(i*1.6,0,0)
render('grass-variants',['forest_single','meadow_single','lime_single'],(1.6,0,.45),(5,-6,5),5.7)
for o in objects.values():o.location=(0,0,0)
for theme in ['meadow','forest','lime']:
 render(theme+'-single',[theme+'_single'],(0,0,.48),(2.5,-3,2.6),1.95)
 # Palette thumbnails match the changed actual builder geometry.
 thumb=bpy.data.images.load(str(HAND/(theme+'-single.png')));thumb.scale(192,162)
 thumb.filepath_raw=str(REPO/'Tools/HabitatEditor/assets/thumbnails'/('terrain_'+theme+'.png'));thumb.file_format='PNG';thumb.save()
render('connected-3x3',['meadow_patch'],(1,1,.45),(5,-5,5),4.9)
render('raised-terrace',['meadow_terrace'],(1,1,1.15),(5,-5,5.7),5.3)
for i,theme in enumerate(['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']):objects[theme+'_single'].location=((i%3)*1.6,(i//3)*1.6,0)
for id,o in objects.items():o.hide_render=not id.endswith('_single');o.hide_set(not id.endswith('_single'))
cam.location=(7,-8,8);cam.rotation_euler=(Vector((1.6,1.6,.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=7
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Fibu.SoftTerrain.blend'))
