"""Blender: reshape the existing surface, interpolate UVs/weights, add one subdivision level."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';d=json.loads((OUT/'original.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
height_offset=max(p[0] for p in d['points'])
def canonical(p):return Vector((p[2],p[1],height_offset-p[0]))
def original(p):return [height_offset-p.z,p.y,p.x]
verts=[canonical(p) for p in d['points']]
mesh=bpy.data.meshes.new('Fibu refined surface');mesh.from_pydata(verts,[],d['faces']);mesh.update()
body=bpy.data.objects.new('Fibu.Refined',mesh);bpy.context.collection.objects.link(body);bpy.context.view_layer.objects.active=body;body.select_set(True)
body['raw_height_offset']=height_offset
uv=mesh.uv_layers.new(name='OriginalSkinUV')
for i,p in enumerate(d['uv']):uv.data[i].uv=p
groups=[body.vertex_groups.new(name=f'J{i:02d}_'+n.split('/')[-1]) for i,n in enumerate(d['joints'])]
weights=[];K=d['influences']
for i in range(len(verts)):
    row={}
    for j,w in zip(d['indices'][i*K:(i+1)*K],d['weights'][i*K:(i+1)*K]):
        if w>0:row[j]=row.get(j,0)+w
    weights.append(row)
    for j,w in row.items():groups[j].add([i],w,'REPLACE')
neighbors=[set() for _ in verts]
for e in mesh.edges:a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
armids={i for i,n in enumerate(d['joints']) if any(t in n.split('/')[-1] for t in ['Shoulder','Bicep','Forearm','Hand'])}
legids={i for i,n in enumerate(d['joints']) if any(t in n.split('/')[-1] for t in ['Thigh','Calf','Foot','Toe'])}
def gaussian(v,center,scale):return math.exp(-sum(((v[i]-center[i])/scale[i])**2 for i in range(3)))
originalverts=[v.copy() for v in verts]
# Local smoothing blends irregular elbow/hip rings without smoothing facial UV landmarks.
for step in range(9):
    new=[]
    for i,v in enumerate(verts):
        arm=sum(weights[i].get(j,0) for j in armids)*min(1,max(0,(abs(v.x)-.42)/.28))
        hips=gaussian(v,(0,0,.62),(.65,.75,.40))
        strength=.32*arm+.15*hips
        avg=sum((verts[j] for j in neighbors[i]),Vector())/len(neighbors[i]) if neighbors[i] else v
        new.append(v.lerp(avg,min(.36,strength)))
    verts=new
for i,v in enumerate(verts):
    arm=sum(weights[i].get(j,0) for j in armids)*min(1,max(0,(abs(v.x)-.52)/.25))
    # Full, rounded arms, with a continuous shoulder-to-mitten silhouette.
    v.y=-.12+(v.y+.12)*(1+.18*arm)
    v.z=1.39+(v.z-1.39)*(1+.18*arm)
    # Lift and tuck the lower belly; keep the middle torso softly plump.
    lower=gaussian(v,(0,-.32,.62),(.46,.52,.32))
    v.z+=.12*lower;v.y+=.10*lower
    belly=gaussian(v,(0,-.42,1.03),(.52,.44,.43));v.y-=.025*belly
    # Smooth single rounded posterior, with no modeled cleft.
    rear=gaussian(v,(0,.34,.69),(.60,.34,.36));v.y+=.10*rear
    # Slightly separate the feet while leaving the rig in its existing bind pose.
    leg=sum(weights[i].get(j,0) for j in legids)
    lowleg=leg*math.exp(-((v.z-.27)/.40)**2)
    v.x+=math.copysign(.055*lowleg,v.x);v.y-=.10*lowleg
    mesh.vertices[i].co=v
# Smooth the bending gradients as well as the geometry to remove elbow pinching.
for step in range(8):
    updated=[]
    for i,v in enumerate(verts):
        arm=sum(weights[i].get(j,0) for j in armids)*min(1,max(0,(abs(v.x)-.45)/.24))
        strength=.42*arm;row={}
        for j in range(32):
            mean=sum(weights[k].get(j,0) for k in neighbors[i])/len(neighbors[i]) if neighbors[i] else weights[i].get(j,0)
            w=weights[i].get(j,0)*(1-strength)+mean*strength
            if w>1e-8:row[j]=w
        total=sum(row.values());updated.append({j:w/total for j,w in row.items()})
    weights=updated
body.vertex_groups.clear();groups=[body.vertex_groups.new(name=f'J{i:02d}_'+n.split('/')[-1]) for i,n in enumerate(d['joints'])]
for i,row in enumerate(weights):
    for j,w in row.items():groups[j].add([i],w,'REPLACE')
# Protect the painted smile: triangulate its patch before refinement so interpolation
# follows the original rendered triangles, then retain that patch's linear surface.
bm=bmesh.new();bm.from_mesh(body.data)
patch=[f for f in bm.faces if (lambda c: abs(c.x)<.4 and c.y<-.67 and 1.25<c.z<1.95)(f.calc_center_median())]
bmesh.ops.triangulate(bm,faces=patch,quad_method='BEAUTY');bm.to_mesh(body.data);bm.free()
reference=body.copy();reference.data=body.data.copy();bpy.context.collection.objects.link(reference)
bpy.context.view_layer.objects.active=reference;body.select_set(False);reference.select_set(True)
linear=reference.modifiers.new('Facial reference','SUBSURF');linear.subdivision_type='SIMPLE';linear.levels=1;linear.uv_smooth='NONE'
bpy.ops.object.modifier_apply(modifier=linear.name)
bpy.context.view_layer.objects.active=body;reference.select_set(False);body.select_set(True)
sub=body.modifiers.new('Soft continuous silhouette','SUBSURF');sub.levels=1;sub.render_levels=1;sub.uv_smooth='NONE'
bpy.ops.object.modifier_apply(modifier=sub.name)
mesh=body.data
assert len(mesh.vertices)==len(reference.data.vertices)
for v,rv in zip(mesh.vertices,reference.data.vertices):
    q=rv.co
    amount=math.exp(-((q.x/.32)**8+((q.z-1.60)/.36)**8+((q.y+.84)/.20)**8))
    v.co=v.co.lerp(q,amount)
bpy.data.objects.remove(reference,do_unlink=True)
# Keep the torso independent from the arm controls during larger reaches.
def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
leafids={n.split('/')[-1]:i for i,n in enumerate(d['joints'])}
corrected=[]
for v in mesh.vertices:
    row={g.group:g.weight for g in v.groups if g.weight>1e-8};x,y,z=v.co
    factor=smoothstep(.50,.82,abs(x))*smoothstep(0,.24,.60-abs(y+.12))*smoothstep(0,.15,.45-abs(z-1.39))
    removed=sum(w for j,w in row.items() if j in armids)*(1-factor)
    nonarm=sum(w for j,w in row.items() if j not in armids)
    if removed>0:
        for j in list(row):row[j]*=factor if j in armids else (1+removed/nonarm if nonarm>1e-8 else 1)
        if nonarm<=1e-8:
            joint='Neck' if z>1.45 else 'Chest' if z>1.15 else 'Stomach'
            row[leafids[joint]]=row.get(leafids[joint],0)+removed
    if z<.65 and abs(x)>.12:
        side='_L' if x>0 else '_R';mapped={}
        for j,w in row.items():
            name=d['joints'][j].split('/')[-1]
            if any(k in name for k in ['Thigh','Calf','Foot','Toe']) and (name.endswith('_L') or name.endswith('_R')):
                j=leafids.get(name[:-2]+side,j)
            mapped[j]=mapped.get(j,0)+w
        row=mapped
    total=sum(row.values());corrected.append({j:w/total for j,w in row.items() if w>1e-8})
body.vertex_groups.clear();groups=[body.vertex_groups.new(name=f'J{i:02d}_'+n.split('/')[-1]) for i,n in enumerate(d['joints'])]
for i,row in enumerate(corrected):
    for j,w in row.items():groups[j].add([i],w,'REPLACE')
for p in mesh.polygons:p.use_smooth=True
mesh.calc_loop_triangles();loops=mesh.uv_layers.active.data
newweights=[];newindices=[];maxdrop=0
for v in mesh.vertices:
    pairs=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-8],key=lambda g:-g[1])
    maxdrop=max(maxdrop,sum(w for j,w in pairs[10:]));pairs=pairs[:10];total=sum(w for j,w in pairs)
    assert total>0
    pairs=[(j,w/total) for j,w in pairs]+[(0,0)]*(10-len(pairs))
    newindices.extend(j for j,w in pairs);newweights.extend(w for j,w in pairs)
data={'points':[original(v.co) for v in mesh.vertices],
      'faces':[list(p.vertices) for p in mesh.polygons],
      'uv':[list(loops[i].uv) for p in mesh.polygons for i in p.loop_indices],
      'normals':[[-mesh.corner_normals[i].vector.z,mesh.corner_normals[i].vector.y,mesh.corner_normals[i].vector.x] for p in mesh.polygons for i in p.loop_indices],
      'indices':newindices,'weights':newweights,'max_discarded_weight':maxdrop,'triangles':len(mesh.loop_triangles)}
(OUT/'refined.json').write_text(json.dumps(data))
# A reconstructed editing rig: authoritative export retains the original USD skeleton and animation.
arm=bpy.data.armatures.new('Original 32-joint editing rig');rig=bpy.data.objects.new('Fibu editing rig',arm);bpy.context.collection.objects.link(rig)
rig['usd_joint_paths']=json.dumps(d['joints'])
bpy.context.view_layer.objects.active=rig;body.select_set(False);rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
bones={}
for i,name in enumerate(d['joints']):
    bone=arm.edit_bones.new(groups[i].name);bone.head=canonical(d['heads'][i]);bone.tail=bone.head+Vector((0,0,.08));bones[name]=bone
    parent=name.rsplit('/',1)[0] if '/' in name else None
    if parent in bones:bone.parent=bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
modifier=body.modifiers.new('Original joint influences','ARMATURE');modifier.object=rig
image=bpy.data.images.load(str(OUT/'original/0/Feeb_skin.png'));image.pack()
mat=bpy.data.materials.new('Fibu original skin');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.88
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);body.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Fibu.Refined.blend'))
print('Refined:',len(mesh.vertices),'vertices;',data['triangles'],'triangles; max trimmed weight',maxdrop)
