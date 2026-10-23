"""Nine painted terrain materials, plus three original 9×9 habitat scenes."""
from pathlib import Path
import bpy,json,math,random
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';OUT.mkdir(exist_ok=True)
base=(ROOT.parent/'TerrainV2/build.py').read_text().split('for row,theme in enumerate(mats):')[0]
base=base.replace("['golden','forest','lime']","['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']")
exec(compile(base,str(ROOT.parent/'TerrainV2/build.py'),'exec'))
for theme,materials in mats.items():
    for face,m in zip(['side','top'],materials):
        bs=m.node_tree.nodes.get('Principled BSDF')
        for kind in ['normal','roughness']:
            tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures'/f'{theme}_{face}_{kind}.png'));tex.image.colorspace_settings.name='Non-Color'
            if kind=='normal':
                normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45;m.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
            else:m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Roughness'])
for row,theme in enumerate(mats):
    for col,(layout,cells) in enumerate(layouts.items()):
        o=make(theme,layout,cells);o.location=(col*6,row*7,0);o.hide_render=True
with bpy.data.libraries.load(str(ROOT.parent/'HabitatExpansion/HabitatExpansion.blend'),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('foliage_')]
sources={}
for o in dst.objects:
    if o:scene.collection.objects.link(o);o.hide_render=True;sources[o.name]=o
rng=random.Random(913)
def solid(name,c,rough=.8,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough
    if emission:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emission
    return m
water=solid('Pond turquoise',(.055,.36,.45),.20);foam=solid('Water highlights',(.40,.75,.70),.3)
yellow=solid('Petal yellow',(.93,.67,.09));white=solid('Petal ivory',(.91,.88,.69));leaf=solid('Plant green',(.15,.38,.07));red=solid('Fruit red',(.68,.09,.045));iron=solid('Lantern iron',(.10,.12,.13));flame=solid('Fire amber',(.95,.24,.015),.6,1.2);glow=solid('Lantern warm glass',(.98,.64,.12),.5,.6)
worlds={};current=[]
def register(o,name):o.name=name;current.append(o);return o
def uvbox(o,theme):
    for m in mats[theme]:o.data.materials.append(m)
    uv=o.data.uv_layers.active or o.data.uv_layers.new(name='WorldUV')
    for p in o.data.polygons:
        top=p.normal.z>.55;p.material_index=int(top)
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x,v.y) if top else ((v.y if abs(p.normal.x)>abs(p.normal.y) else v.x),v.z)
def box(name,loc,size,theme=None,mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Soft craft edges','BEVEL');bevel.width=min(.055,min(size)*.15);bevel.segments=3;bpy.ops.object.modifier_apply(modifier=bevel.name)
    if theme:uvbox(o,theme)
    elif mat:o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    norm=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=norm.name)
    return register(o,name)
def ball(name,loc,scale,mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc);o=bpy.context.object;o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return register(o,name)
def rod(name,a,b,r,mat):
    a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return register(o,name)
def prop(name,loc,scale=1,angle=0):
    src=sources[name];o=src.copy();o.data=src.data;scene.collection.objects.link(o);o.location=loc;o.scale=(scale,)*3;o.rotation_euler.z=angle;o.hide_render=False;return register(o,name)
def flowers(x,y,count=5):
    for i in range(count):
        a=rng.uniform(0,math.tau);r=rng.uniform(0,.38);cx=x+r*math.cos(a);cy=y+r*math.sin(a);z=1.20+rng.uniform(0,.20)
        rod('Flower stem',(cx,cy,1),(cx,cy,z),.018,leaf)
        for k in range(5):
            a=k*math.tau/5;ball('Soft petal',(cx+.085*math.cos(a),cy+.085*math.sin(a),z),(.08,.08,.035),white if i%3==0 else yellow)
        ball('Flower center',(cx,cy,z+.025),(.045,.045,.025),yellow)
def bench(x,y):
    for i in range(4):box('Bench seat',(x,y+(i-1.5)*.15,1.60),(1.65,.13,.13),'timber')
    for dx in [-.60,.60]:box('Bench support',(x+dx,y,1.30),(.14,.50,.60),'timber')
    for h in [1.94,2.20]:box('Bench back',(x,y+.34,h),(1.65,.12,.20),'timber')
def pergola(x,y):
    for dx in [-1.25,1.25]:
        for dy in [-1,1]:box('Pergola post',(x+dx,y+dy,2.15),(.23,.23,2.30),'timber')
    for dx in [-1.25,1.25]:box('Pergola beam',(x+dx,y,3.35),(.25,2.65,.24),'timber')
    for i in range(8):box('Pergola roof slat',(x+(i-3.5)*.40,y,3.55),(.26,2.85,.12),'timber')
    for i in range(12):
        xx=x-1.35+i*.24;ball('Trailing vine',(xx,y-1.44,3.30-.15*(i%3)),(.10,.045,.18),leaf)
def lantern(x,y,z):
    box('Lantern base',(x,y,z+.08),(.32,.32,.12),mat=iron);box('Warm lantern',(x,y,z+.30),(.24,.24,.34),mat=glow)
    for dx in [-.14,.14]:
        for dy in [-.14,.14]:rod('Lantern rail',(x+dx,y+dy,z+.12),(x+dx,y+dy,z+.48),.022,iron)
    box('Lantern cap',(x,y,z+.52),(.34,.34,.12),mat=iron)
def baseplate(theme,name,cells=None):
    o=make(theme,'world_'+name,cells or [(x,y,0) for x in range(9) for y in range(9)]);current.append(o);(OUT/(o.name+'.json')).unlink();return o
def dump(name):
    objects=[]
    for o in current:
        if o.type!='MESH':continue
        mesh=o.data;mesh.calc_loop_triangles();tris=[t for t in mesh.loop_triangles if (mesh.vertices[t.vertices[1]].co-mesh.vertices[t.vertices[0]].co).cross(mesh.vertices[t.vertices[2]].co-mesh.vertices[t.vertices[0]].co).length>1e-9];M=o.matrix_world;NM=M.to_3x3().inverted().transposed();uv=mesh.uv_layers.active
        materials=[]
        for m in mesh.materials:
            tex=[n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'] if m.use_nodes else []
            textures={}
            for n in tex:
                filename=Path(n.image.filepath).name
                if (ROOT/'textures'/filename).exists():textures['normal' if '_normal.' in filename else 'roughness' if '_roughness.' in filename else 'color']=filename
            p=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
            materials.append({'name':m.name,'color':list(p.inputs['Base Color'].default_value)[:3] if p else list(m.diffuse_color)[:3],
               'roughness':float(p.inputs['Roughness'].default_value) if p else .8,'textures':textures,
               'emission':list(p.inputs['Emission Color'].default_value)[:3] if p and p.inputs['Emission Strength'].default_value>0 else [0,0,0]})
        objects.append({'name':o.name,'points':[list(M@v.co) for v in mesh.vertices],
           'faces':[list(t.vertices) for t in tris],
           'normals':[list((NM@(mesh.corner_normals[li].vector if mesh.corner_normals[li].vector.length>1e-6 else t.normal)).normalized()) for t in tris for li in t.loops],
           'uv':[list(uv.data[li].uv) if uv else [0,0] for t in tris for li in t.loops],
           'material_indices':[t.material_index for t in tris],'materials':materials})
    (OUT/('habitat_'+name+'.json')).write_text(json.dumps({'name':name,'objects':objects}))
    worlds[name]=current.copy()

# 1. Garden: open front, shaded bench, mature/young trees, generous planted border.
current=[];baseplate('meadow','garden');pergola(4.4,6.4);bench(4.4,6.7)
prop('foliage_round_tree',(1.0,6.6,1),1.45);prop('foliage_young_tree',(7.1,6.8,1),1.45)
for y in [.55,1.55,2.55,3.55,4.55]:box('Garden stepping stone',(4,y,1.055),(.84,.72,.11),'limestone')
for x,y in [(1,.8),(1.2,3.3),(7.2,1.1),(6.9,4.7),(2.4,7.4)]:prop('foliage_shrub',(x,y,1),.85);flowers(x-.5,y-.6,5)
for x,y in [(.2,2),(2.1,.3),(7.8,2.6),(.3,5),(6.7,7.8),(2.5,5.9),(5.7,.1),(7.8,5.2)]:prop('foliage_grass_fluffy',(x,y,1),1,rng.random()*6)
box('Picnic mat',(2.5,3.1,1.045),(1.3,1.1,.09),'lime');box('Fruit bowl',(2.5,3.1,1.15),(.5,.4,.15),'golden')
for x in [2.35,2.57]:ball('Apple',(x,3.1,1.29),(.105,.105,.11),red)
lantern(3.0,6.3,1);dump('garden')

# 2. Pond: recessed center, stone coping, fountain, resting deck and umbrella.
current=[];cells=[(x,y,0) for x in range(9) for y in range(9) if not (2<=x<=6 and 3<=y<=6)]
baseplate('forest','pond',cells);box('Pond bottom',(4,4.5,.12),(5,4,.24),'sand');box('Pond water',(4,4.5,.79),(4.9,3.9,.08),mat=water)
for x in range(2,7):
    for y in [2.7,6.6]:box('Pool coping',(x,y,1.07),(.99,.32,.14),'limestone')
for y in [3.5,4.5,5.5]:
    for x in [1.6,6.4]:box('Pool coping',(x,y,1.07),(.3,1,.14),'limestone')
box('Fountain plinth',(4,6.9,1.24),(.7,.65,.48),'cobble');rod('Fountain pillar',(4,6.9,1.35),(4,6.9,2.65),.16,mats['limestone'][0]);ball('Fountain crown',(4,6.9,2.70),(.28,.24,.18),mats['limestone'][0])
rod('Water stream',(4,6.7,2.5),(4,6.25,.85),.055,water)
for r in [.23,.43,.70]:
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.012,major_segments=40,minor_segments=6,location=(4,6.05,.84));o=bpy.context.object;o.data.materials.append(foam);register(o,'Static ripple')
prop('foliage_round_tree',(.6,7.0,1),1.35);prop('foliage_young_tree',(7.5,7.2,1),1.2)
box('Poolside deck',(.4,3.4,1.08),(1.55,2.8,.16),'timber');bench(.45,3.1)
rod('Umbrella pole',(.5,1.6,1),(.5,1.6,3.3),.045,mats['timber'][0])
for k in range(12):
    a=k*math.tau/12;b=(k+1)*math.tau/12;verts=[(.5,1.6,3.5),(.5+1.05*math.cos(a),1.6+1.05*math.sin(a),3.15),(.5+1.05*math.cos(b),1.6+1.05*math.sin(b),3.15)]
    mesh=bpy.data.meshes.new('Umbrella panel');mesh.from_pydata(verts,[],[(0,1,2),(2,1,0)]);o=bpy.data.objects.new('Umbrella panel',mesh);scene.collection.objects.link(o);mesh.materials.append(white if k%2 else yellow);register(o,'Umbrella panel')
for x,y in [(7.6,.8),(7.5,3.2),(.1,5.5),(5.8,7.8)]:flowers(x,y,5);prop('foliage_grass_small',(x-.35,y+.3,1),1.2)
for x in [3,4,5]:box('Entry paving',(x,.3,1.05),(.95,.75,.10),'sand')
lantern(7.4,5.5,1);dump('pond')

# 3. Camp: volcanic platform, warm timber deck, fire circle, log seats and supplies.
current=[];baseplate('volcanic','camp');box('Camp timber deck',(4.2,6.7,1.09),(5.7,2.6,.18),'timber')
for y in [.2,1.25,2.3]:box('Camp path',(4,y,1.06),(1.1,.9,.12),'cobble')
box('Fire hearth',(4,4.1,1.10),(2.3,2.2,.20),'cobble')
for k in range(10):
    a=k*math.tau/10;ball('Hearth stone',(4+.91*math.cos(a),4.1+.91*math.sin(a),1.28),(.22,.20,.18),mats['limestone'][0])
for a in [-.6,.6]:rod('Fire log',(3.4,3.75+a*.3,1.29),(4.6,4.45-a*.3,1.29),.14,mats['timber'][0])
for x,y,z,s in [(4,4.1,1.7,.45),(3.7,4.15,1.58,.28),(4.3,4,1.57,.27)]:ball('Static flame',(x,y,z),(s*.5,s*.4,s),flame)
for x,y in [(2,3.6),(6,4),(4.6,6.0)]:
    rod('Log stool',(x,y,1),(x,y,1.6),.32,mats['timber'][0]);ball('Stool top',(x,y,1.60),(.32,.32,.045),mats['golden'][1])
for x,y,z in [(1.4,6.7,1.65),(1.4,6.7,2.6),(2.4,7.2,1.6)]:
    box('Supply crate',(x,y,z),(.9,.85,.9),'timber')
    for dx in [-.32,.32]:box('Crate strap',(x+dx,y-.44,z),(.10,.045,.91),mat=iron)
for x in [1.4,6.9]:
    box('Camp rail post',(x,7.8,2.1),(.2,.2,2.2),'timber');lantern(x,7.8,3.2)
box('Camp crossbeam',(4.15,7.8,3.25),(5.8,.24,.22),'timber')
prop('foliage_young_tree',(7.5,6.5,1),1.4)
for x,y in [(.3,1),(7.4,.4),(.2,4),(7.7,4.3)]:
    prop('foliage_grass_tall',(x,y,1),.8)
    for k in range(3):ball('Camp rock',(x+.2*k,y+.12*k,1.12),(.22,.18,.18),mats['cobble'][0])
lantern(2,1.8,1);dump('camp')

floor=bpy.data.materials.new('Backdrop');floor.diffuse_color=(.17,.20,.18,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(4,4,-.025));bpy.context.object.data.materials.append(floor)
world=bpy.data.worlds.new('Daylight');world.use_nodes=True;scene.world=world;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(0,-4,15));light=bpy.context.object;light.data.energy=3400;light.data.size=10
bpy.ops.object.camera_add(location=(17,-20,18));cam=bpy.context.object;cam.rotation_euler=(Vector((4,4,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=15.5;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
for name,objects in worlds.items():
    for other,items in worlds.items():
        for o in items:o.hide_render=other!=name
    if name=='garden':bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'FibuHabitats9x9.blend'))
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
