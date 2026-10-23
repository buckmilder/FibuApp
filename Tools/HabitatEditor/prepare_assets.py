"""Run in Blender: convert existing habitat geometry; never touch Fibu."""
from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
scratch=HERE/'assets'/'conversion';scratch.mkdir(exist_ok=True)
entries=[]
def publish(ident,name,category,objects,solid=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    # Assets are in Blender world space; center horizontally and ground at z=0.
    pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    for o in objects:o.location-=center
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(HERE/'assets/models'/f'{ident}.glb'),use_selection=True,export_format='GLB',export_yup=True)
    data=[]
    for o in objects:
        m=o.data;m.calc_loop_triangles();tris=list(m.loop_triangles);M=o.matrix_world;N=M.to_3x3().inverted().transposed();uv=m.uv_layers.active
        mats=[]
        for mat in m.materials:
            p=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
            textures={}
            for n in mat.node_tree.nodes if mat.use_nodes else []:
                if n.type=='TEX_IMAGE' and n.image:
                    f=Path(n.image.filepath).name
                    if (ROOT/'Assets/Blender/HabitatWorlds/textures'/f).exists():textures['normal' if '_normal.' in f else 'roughness' if '_roughness.' in f else 'color']=f
            mats.append({'name':mat.name,'color':list(p.inputs['Base Color'].default_value)[:3] if p else list(mat.diffuse_color)[:3], 'textures':textures,'roughness':.85})
        data.append({'name':o.name,'points':[list(M@v.co) for v in m.vertices],'faces':[list(t.vertices) for t in tris], 'normals':[list((N@m.corner_normals[li].vector).normalized()) for t in tris for li in t.loops], 'uv':[list(uv.data[li].uv) if uv else [0,0] for t in tris for li in t.loops], 'material_indices':[t.material_index for t in tris],'materials':mats})
    (scratch/f'{ident}.json').write_text(json.dumps(data))
    size=hi-lo
    entries.append({'id':ident,'name':name,'category':category,'kind':'prop','godot':f'res://assets/models/{ident}.glb','ios':f'Assets/Models/EditorKit/{ident}.usdz','dimensions':[size.x,size.z,size.y],'solid':solid,'rotations':[0,90,180,270] if solid else [],'scale_range':[1,1] if solid else [.25,3], 'footprint':[1,1] if solid else [],'overhang':not solid})
    for o in objects:o.hide_set(True);o.hide_render=True
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Assets/Blender/HabitatExpansion/HabitatExpansion.blend'))
for name in ['foliage_round_tree','foliage_young_tree','foliage_shrub','foliage_grass_small','foliage_grass_fluffy','foliage_grass_tall']:
    o=bpy.data.objects[name];o.location=(0,0,0);o.hide_set(False);publish(name,name.replace('foliage_','').replace('_',' ').title(),'Nature',[o])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Assets/Blender/HabitatWorlds/FibuHabitats9x9.blend'))
# Match exact object memberships captured by the existing source generator.
worlds={n:json.loads((ROOT/f'Assets/Blender/HabitatWorlds/generated/habitat_{n}.json').read_text())['objects'] for n in ['garden','pond','camp']}
groups=[('bench','Garden Bench','Furniture','garden',['Bench ']),('pergola','Vine Pergola','Structures','garden',['Pergola ','Trailing vine']),('picnic','Picnic & Fruit','Furniture','garden',['Picnic mat','Fruit bowl','Apple']),('fountain','Stone Fountain','Structures','pond',['Fountain ']),('umbrella','Sun Umbrella','Furniture','pond',['Umbrella ']),('hearth','Camp Hearth','Furniture','camp',['Fire hearth','Hearth stone','Fire log','Static flame']),('supplies','Stacked Supplies','Furniture','camp',['Supply crate','Crate strap'])]
for ident,name,cat,world,prefixes in groups:
    names=[d['name'] for d in worlds[world] if any(d['name'].startswith(p) for p in prefixes)]
    objects=[bpy.data.objects[n] for n in names]
    for o in objects:o.hide_set(False)
    publish(ident,name,cat,objects)
# Reusable stair: bottom at 0, ascent toward -Z in canonical coordinates.
bpy.ops.object.select_all(action='DESELECT');objects=[]
mat=bpy.data.materials.get('limestone_top')
for i in range(4):
    h=(i+1)/4
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,(i+.5)/4-.5,h/2));o=bpy.context.object;o.dimensions=(1,.25,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    objects.append(o)
publish('stairs','Stone Stairs','Structures',objects,True)
for theme in ['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']:
    for face in ['top','side']:
        for suffix in ['', '_normal','_roughness']:
            f=f'{theme}_{face}{suffix}.png';shutil.copy2(ROOT/'Assets/Blender/HabitatWorlds/textures'/f,HERE/'assets/textures'/f)
    entries.append({'id':'terrain_'+theme,'name':theme.title(),'category':'Terrain','kind':'terrain','theme':theme,'dimensions':[1,1,1],'footprint':[1,1],'rotations':[0],'connection_group':'terrain','ios':{'generator':'fibu-rounded-boundary-v1','material':theme},'godot':{'generator':'fibu-rounded-boundary-v1'},'solid':True})
(HERE/'assets/catalog.json').write_text(json.dumps({'version':1,'assets':entries},indent=2)+'\n')
print('Prepared',len(entries),'assets')
