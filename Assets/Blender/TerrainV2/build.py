"""Blender 4.3+: boundary mesh from occupied cells, then bevel only its exposed edges."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'generated';OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
layouts={'single':[(0,0,0)],'pair':[(0,0,0),(1,0,0)],
 'platform':[(x,y,0) for x in range(5) for y in range(5)],
 'corner':[(0,0,0),(1,0,0),(0,1,0)],
 'terrace':[(x,y,0) for x in range(3) for y in range(2)]+[(x,1,1) for x in range(3)]}

def material(theme,face):
    m=bpy.data.materials.new(theme+'_'+face);m.use_nodes=True
    nodes=m.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.86
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures'/f'{theme}_{face}.png'));tex.extension='REPEAT'
    m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m
mats={t:[material(t,'side'),material(t,'top')] for t in ['golden','forest','lime']}

def make(theme,layout,cells):
    cells=set(map(tuple,cells));verts=[];faces=[];lookup={}
    # Face winding points outwards.
    dirs=[((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),
          ((-1,0,0),[(0,1,0),(0,0,0),(0,0,1),(0,1,1)]),
          ((0,1,0),[(1,1,0),(0,1,0),(0,1,1),(1,1,1)]),
          ((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),
          ((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),
          ((0,0,-1),[(0,1,0),(1,1,0),(1,0,0),(0,0,0)])]
    for x,y,z in sorted(cells):
        for d,corners in dirs:
            if (x+d[0],y+d[1],z+d[2]) in cells:continue
            f=[]
            for a,b,c in corners:
                v=(x+a-.5,y+b-.5,z+c)
                if v not in lookup:lookup[v]=len(verts);verts.append(v)
                f.append(lookup[v])
            faces.append(f)
    mesh=bpy.data.meshes.new(theme+'_'+layout);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    # Remove coplanar tile boundaries BEFORE beveling: no rounded grooves at joins.
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.dissolve_limit(bm,angle_limit=.001,verts=list(bm.verts),edges=list(bm.edges),delimit=set())
    bm.to_mesh(mesh);bm.free();mesh.update()
    bevel=o.modifiers.new('Continuous exposed contour','BEVEL');bevel.width=.085;bevel.segments=5;bevel.limit_method='ANGLE'
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    mesh=o.data
    for m in mats[theme]:mesh.materials.append(m)
    uv=mesh.uv_layers.new(name='TerrainUV')
    for p in mesh.polygons:
        top=p.normal.z>.55;p.material_index=1 if top else 0
        p.use_smooth=False
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            if top:u,w=v.x+.5,v.y+.5
            else:u,w=(v.y+.5 if abs(p.normal.x)>abs(p.normal.y) else v.x+.5),v.z
            uv.data[li].uv=(u,w)
    # Weighted normals keep broad surfaces flat and bevels softly shaded.
    for p in mesh.polygons:p.use_smooth=True
    normal=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50
    bpy.ops.object.modifier_apply(modifier=normal.name)
    mesh=o.data;uv=mesh.uv_layers.active
    mesh.calc_loop_triangles()
    ns=mesh.corner_normals
    triangles=list(mesh.loop_triangles)
    data={'name':o.name,'vertices':[list(v.co) for v in mesh.vertices],
      'faces':[list(t.vertices) for t in triangles],
      'normals':[list(ns[li].vector) for t in triangles for li in t.loops],
      'uv':[list(uv.data[li].uv) for t in triangles for li in t.loops],
      'material_indices':[t.material_index for t in triangles],
      'textures':[theme+'_side.png',theme+'_top.png'],'cells':sorted(cells)}
    (OUT/(o.name+'.json')).write_text(json.dumps(data))
    o.select_set(False);return o

for row,theme in enumerate(mats):
    for col,(layout,cells) in enumerate(layouts.items()):
        o=make(theme,layout,cells)
        # Samples sit on one level, with enough space to see their silhouettes.
        o.location=(col*6,row*7,0)

floor=bpy.data.materials.new('Warm studio');floor.diffuse_color=(.16,.19,.18,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(10,8,-.015));bpy.context.object.data.materials.append(floor)
world=bpy.data.worlds.new('Soft daylight');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(7,-5,22));bpy.context.object.data.energy=6500;bpy.context.object.data.size=15
bpy.ops.object.camera_add(location=(36,-36,38));cam=bpy.context.object
cam.rotation_euler=(Vector((13,8,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=39;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=2000;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'overview.png')
for image in bpy.data.images:
    if image.source=='FILE':image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'FibuTerrainV2.blend'))
bpy.ops.render.render(write_still=True)
