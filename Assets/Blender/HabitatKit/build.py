import bpy, math, os, json
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(ROOT+'/models', exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1

def material(name, color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=.83
    return m

palettes={
 'meadow':(material('Warm earth',(.40,.23,.12)),material('Soft grass',(.33,.57,.13))),
 'stone':(material('Warm limestone',(.48,.46,.39)),material('Light stone top',(.64,.62,.53))),
 'timber':(material('Honey wood sides',(.43,.23,.10)),material('Honey wood ends',(.65,.40,.19)))
}

def cube(name,loc,size,mat,parts):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    bevel=o.modifiers.new('Soft exposed edges','BEVEL'); bevel.width=.012; bevel.segments=3
    bevel.affect='EDGES'
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    parts.append(o); return o

def make(theme,shape):
    side,top=palettes[theme]; parts=[]
    heights={'cube':1,'half':.5,'slab':.25,'wall':1,'post':1}
    if shape in heights:
        h=heights[shape]; w=.25 if shape=='post' else 1; d=.25 if shape in ('wall','post') else 1
        cube('Body',(0,0,(h-.06)/2),(w,d,h-.06),side,parts)
        cube('Top',(0,0,h-.03),(w,d,.06),top,parts)
    elif shape=='steps':
        for i in range(4):
            h=(i+1)*.25; y=-.375+i*.25
            cube('Riser',(0,y,(h-.04)/2),(1,.25,h-.04),side,parts)
            cube('Tread',(0,y,h-.02),(1,.25,.04),top,parts)
    elif shape=='ramp':
        verts=[(-.5,-.5,0),(.5,-.5,0),(-.5,.5,0),(.5,.5,0),(-.5,.5,1),(.5,.5,1)]
        faces=[(0,2,3,1),(2,4,5,3),(0,4,2),(1,3,5),(0,1,5,4)]
        mesh=bpy.data.meshes.new('Ramp mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
        o=bpy.data.objects.new('Ramp',mesh); scene.collection.objects.link(o); parts.append(o)
        mesh.materials.append(side); mesh.materials.append(top); mesh.polygons[4].material_index=1
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    obj=bpy.context.object; obj.name=theme+'_'+shape
    scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.data.calc_loop_triangles()
    data={'name':obj.name,'vertices':[list(obj.matrix_world @ v.co) for v in obj.data.vertices],
          'faces':[list(p.vertices) for p in obj.data.polygons],
          'materials':[{'name':m.name,'color':list(m.diffuse_color)[:3]} for m in obj.data.materials],
          'material_indices':[p.material_index for p in obj.data.polygons]}
    with open(ROOT+'/models/'+obj.name+'.json','w') as f:json.dump(data,f)
    bpy.ops.export_scene.gltf(filepath=ROOT+'/models/'+obj.name+'.glb',use_selection=True,export_format='GLB')
    return obj

objects=[]
for row,theme in enumerate(palettes):
    for col,shape in enumerate(['cube','half','slab','ramp','steps','wall','post']):
        o=make(theme,shape); o.location=(col*1.4,row*1.7,0); objects.append(o)

# A separate assembled 5x5 habitat demonstrates grid placement and stacked pieces.
for x in range(5):
    for y in range(5):
        src=objects[0]; o=src.copy(); o.data=src.data; scene.collection.objects.link(o)
        o.location=(x-1,y+7,-1); o.name='Demo_ground_%s_%s'%(x,y)
for x in range(5):
    src=objects[12]; o=src.copy(); o.data=src.data; scene.collection.objects.link(o); o.location=(x-1,11.375,0)
for x in (-.875,2.875):
    for y in (7.125,10.875):
        o=objects[20].copy(); o.data=objects[20].data; scene.collection.objects.link(o); o.location=(x,y,0)

floor=material('Backdrop',(.085,.12,.10)); p=[]
cube('Studio floor',(3.5,5,-1.15),(200,200,.1),floor,p)
world=bpy.data.worlds.new('Studio world'); scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.50,.60,.72,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.6
bpy.ops.object.light_add(type='AREA',location=(0,-3,12)); bpy.context.object.data.energy=2200; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=9
bpy.ops.object.camera_add(location=(17,-19,23)); cam=bpy.context.object
cam.rotation_euler=(Vector((3.8,4.7,0))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=19; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=False
scene.render.resolution_x=1600; scene.render.resolution_y=1600; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.filepath=ROOT+'/preview.png'
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/FibuBlockKit.blend')
bpy.ops.render.render(write_still=True)
