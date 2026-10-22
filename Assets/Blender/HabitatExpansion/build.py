"""Reuse the tested fused-boundary generator, then create original foliage meshes."""
from pathlib import Path
import json,math,random
ROOT=Path(__file__).resolve().parent
base=(ROOT.parent/'TerrainV2/build.py').read_text().split('for row,theme in enumerate(mats):')[0]
base=base.replace("['golden','forest','lime']","['meadow','sand','limestone','cobble','timber','volcanic']")
exec(compile(base,str(ROOT.parent/'TerrainV2/build.py'),'exec'))
terrain=[]
for row,theme in enumerate(mats):
    for col,(layout,cells) in enumerate(layouts.items()):
        o=make(theme,layout,cells);o.location=(col*6,row*7,0);terrain.append(o)

rng=random.Random(147)
def solid(name,c):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.85
    return m
greens=[solid('Leaf_'+str(i),c) for i,c in enumerate([(.055,.16,.018),(.10,.27,.025),(.17,.38,.05),(.27,.49,.08)])]
bark=[solid('Bark_'+str(i),c) for i,c in enumerate([(.35,.18,.08),(.46,.25,.11),(.52,.31,.14)])]
grassm=[solid('Grass_'+str(i),c) for i,c in enumerate([(.10,.28,.03),(.19,.40,.06),(.28,.52,.10),(.36,.60,.14)])]
def ball(loc,scale,mat,parts):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=loc)
    o=bpy.context.object;o.scale=scale;o.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for f in o.data.polygons:f.use_smooth=True
    parts.append(o)
def branch(a,b,r1,r2,parts):
    a,b=Vector(a),Vector(b);delta=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=r1,radius2=r2,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    for m in bark:o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=p.index%3;p.use_smooth=True
    parts.append(o)
def export_prop(name,parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    mesh=o.data;mesh.calc_loop_triangles();tris=list(mesh.loop_triangles);ns=mesh.corner_normals
    data={'name':name,'vertices':[list(v.co) for v in mesh.vertices],'faces':[list(t.vertices) for t in tris],
          'normals':[list(ns[li].vector) for t in tris for li in t.loops],
          'material_indices':[t.material_index for t in tris],
          'colors':[list(m.diffuse_color)[:3] for m in mesh.materials]}
    (OUT/(name+'.json')).write_text(json.dumps(data));o.select_set(False);return o
def tree(name,small=False):
    parts=[]
    branch((0,0,0),(.04,0,.9),.16,.10,parts)
    branch((.04,0,.8),(-.17,.02,1.5),.105,.045,parts)
    branch((.04,0,.85),(.40,.02,1.5),.09,.035,parts)
    branch((0,0,.9),(-.04,.35,1.45),.075,.025,parts)
    for k in range(5):
        a=k*math.tau/5;branch((.27*math.cos(a),.27*math.sin(a),.015),(0,0,.32),.055,.07,parts)
    # Scalloped crown: overlapping lobes form a full silhouette with three soft tiers.
    for tier,(z,r,count,s) in enumerate([(1.42,.49,8,.43),(1.82,.45,8,.40),(2.12,.26,6,.34)]):
        ball((0,0,z+.14),(.58,.58,.38),greens[min(tier+1,3)],parts)
        for k in range(count):
            a=math.tau*(k/count+tier*.07);j=rng.uniform(.94,1.06)
            ball((r*math.cos(a),r*math.sin(a),z+rng.uniform(-.04,.04)),(s*j,s*j,.33),greens[min(3,tier+rng.choice([0,1]))],parts)
    o=export_prop(name,parts)
    if small:
        # Scale source geometry before export so bounds and pivots remain exact.
        for v in o.data.vertices:v.co*=.65
        # Re-export the scaled object, replacing the first mesh snapshot.
        o=export_prop(name,[o])
    return o
props=[]
props.append(tree('foliage_round_tree'));props[-1].location=(0,46,0)
props.append(tree('foliage_young_tree',True));props[-1].location=(3,46,0)
parts=[]
for k in range(7):
    a=k*math.tau/7;ball((.25*math.cos(a),.22*math.sin(a),.30),(.29,.26,.30),greens[1+k%3],parts)
ball((0,0,.48),(.31,.30,.30),greens[3],parts)
props.append(export_prop('foliage_shrub',parts));props[-1].location=(6,46,0)

def grass(name,count,height):
    parts=[]
    for j in range(count):
        a=rng.uniform(0,math.tau);r=rng.uniform(.02,.22);h=height*rng.uniform(.70,1.15)
        bend=rng.uniform(.13,.27);width=rng.uniform(.055,.09);verts=[]
        # Closed thick leaves: elliptical sections, tapered tip, no alpha cards.
        for t in [0,.22,.48,.73,.90]:
            cx=(r+bend*t*t)*math.cos(a);cy=(r+bend*t*t)*math.sin(a)
            w=width*math.sin((t*.90+.1)*math.pi)
            for q in range(6):
                phi=q*math.tau/6;across=math.cos(phi)*w;thick=math.sin(phi)*.018*(1-t)
                verts.append((cx-math.sin(a)*across+math.cos(a)*thick,cy+math.cos(a)*across+math.sin(a)*thick,h*t))
        verts.append(((r+bend)*math.cos(a),(r+bend)*math.sin(a),h))
        faces=[tuple(reversed(range(6)))]
        for ring in range(4):
            for q in range(6):faces.append((ring*6+q,ring*6+(q+1)%6,(ring+1)*6+(q+1)%6,(ring+1)*6+q))
        for q in range(6):faces.append((24+q,24+(q+1)%6,30))
        faces=[tuple(reversed(f)) for f in faces]
        mesh=bpy.data.meshes.new('Leaf');mesh.from_pydata(verts,[],faces);mesh.update()
        o=bpy.data.objects.new('Leaf',mesh);scene.collection.objects.link(o);mesh.materials.append(grassm[j%4])
        for p in mesh.polygons:p.use_smooth=True
        parts.append(o)
    return export_prop(name,parts)
for i,(name,count,h) in enumerate([('foliage_grass_small',12,.30),('foliage_grass_fluffy',22,.46),('foliage_grass_tall',16,.68)]):
    o=grass(name,count,h);o.location=(9+i*2,46,0);props.append(o)

# Product sheet: six material singles and all foliage, larger joined forms in source.
for o in terrain:o.hide_render=not o.name.endswith('_single')
for i,o in enumerate(o for o in terrain if o.name.endswith('_single')):o.location=((i%3)*1.7,(i//3)*1.7,0)
for i,o in enumerate(props):o.location=(6+(i%3)*2,(i//3)*2.4,0)
floor=solid('Studio',(.18,.21,.19));bpy.ops.mesh.primitive_plane_add(size=200,location=(4,1,-.015));bpy.context.object.data.materials.append(floor)
world=bpy.data.worlds.new('Daylight');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.90,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(2,-4,12));bpy.context.object.data.energy=1900;bpy.context.object.data.size=10
bpy.ops.object.camera_add(location=(14,-18,16));cam=bpy.context.object
cam.rotation_euler=(Vector((5,1.5,.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=15;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=False
scene.render.resolution_x=2000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'preview.png')
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'HabitatExpansion.blend'))
bpy.ops.render.render(write_still=True)
