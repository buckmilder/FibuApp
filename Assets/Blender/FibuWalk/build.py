"""Contact-based soft walk on the approved rig. Run with usd-core, scipy, Pillow, numpy."""
from pathlib import Path
import json, math, zipfile, hashlib, subprocess, sys
import numpy as np
from scipy.spatial.transform import Rotation
from arm_shapes import shapes as make_arm_shapes
from pxr import Usd, UsdGeom, UsdSkel, UsdUtils, Gf, Vt, Sdf
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]; OUT=ROOT/'generated'; SOURCE=OUT/'source'
SOURCE.mkdir(parents=True,exist_ok=True)
PARAM=json.loads((ROOT/'parameters.json').read_text())
source=REPO/'Assets/Models/Fibu.Proportions.usdz'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='819ef67d0d86d2572fd0fc1c4d0eca611d516c514e297225beb1e12d1ba7f4b5'
with zipfile.ZipFile(source) as z:
    for entry in z.infolist():
        target=SOURCE/entry.filename; assert target.resolve().is_relative_to(SOURCE.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(entry))
    rootname=z.namelist()[0]
stage=Usd.Stage.Open(str(SOURCE/rootname)); sk=next(UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton)); body=next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh));anim=next(UsdSkel.Animation(p) for p in stage.Traverse() if p.IsA(UsdSkel.Animation))
cache=UsdSkel.Cache()
for p in stage.Traverse():
    if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
query=cache.GetSkelQuery(sk); skin=cache.GetSkinningQuery(body.GetPrim());names=list(sk.GetJointsAttr().Get()); ids={n.split('/')[-1]:i for i,n in enumerate(names)};parents=list(UsdSkel.Topology(names).GetParentIndices())
neutral=np.array([np.array(m).T for m in query.ComputeJointSkelTransforms(0)])
base_local=query.ComputeJointLocalTransforms(0)
rest=np.array(body.GetPointsAttr().Get(),float)
def evaluated(points,frame):
    c=UsdSkel.Cache()
    for prim in stage.Traverse():
        if prim.IsA(UsdSkel.Root):c.Populate(UsdSkel.Root(prim),Usd.PrimDefaultPredicate)
    q=c.GetSkelQuery(sk);sq=c.GetSkinningQuery(body.GetPrim())
    v=Vt.Vec3fArray([Gf.Vec3f(*map(float,p)) for p in points]);assert sq.ComputeSkinnedPoints(q.ComputeSkinningTransforms(frame),v,frame);return np.array(v,float)
pose=evaluated(rest,0);floor=float(pose[:,2].min());unit=float(np.ptp(pose[:,2])/2.7)
# The inherited lower-body weights contain shoulder/bicep influence on the belly/legs.
# Replace only the lower support region with smooth leg/hip weights; keep mesh and UVs.
original_pose=pose.copy();binding=UsdSkel.BindingAPI(body);K=binding.GetJointIndicesPrimvar().GetElementSize()
old_indices=np.array(binding.GetJointIndicesPrimvar().Get()).reshape(-1,K);old_weights=np.array(binding.GetJointWeightsPrimvar().Get()).reshape(-1,K)
def smooth_range(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
new_indices=old_indices.copy();new_weights=old_weights.copy();edited=0
for vertex,p in enumerate(pose):
    height=(p[2]-floor)/unit
    if height>=1.25:continue
    old=np.zeros(len(names))
    for j,w in zip(old_indices[vertex],old_weights[vertex]):old[j]+=w
    support=np.zeros(len(names));waist=smooth_range(.53,1.10,height)
    support[ids['Waist']]=waist
    thigh=smooth_range(.24,.65,height);foot=1-smooth_range(.08,.32,height);calf=max(0,1-thigh-foot)
    left=smooth_range(-.14,.14,p[0]/unit)
    for side,weight in [('L',left),('R',1-left)]:
        for bone,w in [('Thigh',thigh),('Calf',calf),('Foot',foot)]:support[ids[bone+'_'+side]]+=(1-waist)*weight*w
    leg_weight=sum(w for j,w in enumerate(old) if any(tag in names[j].split('/')[-1] for tag in ['Thigh','Calf','Foot','Toe']))
    blend=(1-smooth_range(1.0,1.25,height))*smooth_range(.03,.40,leg_weight);weights=old*(1-blend)+support*blend
    order=np.argsort(-weights)[:K];weights=weights[order];weights/=weights.sum();new_indices[vertex]=order;new_weights[vertex]=weights;edited+=1
binding.GetJointIndicesPrimvar().Set(Vt.IntArray(new_indices.ravel().tolist()));binding.GetJointWeightsPrimvar().Set(Vt.FloatArray(new_weights.ravel().tolist()))
# Rebind the changed support vertices to retain the exact APPROVED visible neutral pose.
zero=np.zeros_like(rest);new_origin=evaluated(zero,0);columns=[]
for axis in range(3):
    v=zero.copy();v[:,axis]=1;columns.append(evaluated(v,0)-new_origin)
new_inverse=np.linalg.inv(np.stack(columns,axis=2));rest=np.einsum('nij,nj->ni',new_inverse,original_pose-new_origin)
body.GetPointsAttr().Set(Vt.Vec3fArray(rest.tolist()));pose=evaluated(rest,0)
assert np.max(np.linalg.norm(pose-original_pose,axis=1))/unit<1e-5,'Weight cleanup changed neutral silhouette'
faces=[];triangle_corners=[];cursor=0;raw=list(body.GetFaceVertexIndicesAttr().Get())
for n in body.GetFaceVertexCountsAttr().Get():
    for i in range(1,n-1):
        corners=[cursor,cursor+i,cursor+i+1];faces.append([raw[j] for j in corners]);triangle_corners.extend(corners)
    cursor+=n
faces=np.array(faces);uv=np.array(UsdGeom.PrimvarsAPI(body).GetPrimvar('st').ComputeFlattened())[triangle_corners]
# Mesh-local shape offsets are obtained by inverting the actual neutral LBS map.
zero=np.zeros_like(rest);origin=evaluated(zero,0);columns=[]
for axis in range(3):
    v=zero.copy();v[:,axis]=1;columns.append(evaluated(v,0)-origin)
inv=np.linalg.inv(np.stack(columns,axis=2))
z=(pose[:,2]-floor)/unit; mask=np.clip((z-.55)/.45,0,1);mask=mask*mask*(3-2*mask)
pivot=np.array([0,0,floor+.70*unit])
def normals(points):
    tri=points[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n=np.zeros_like(points)
    for i in range(3):np.add.at(n,faces[:,i],cross)
    return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
base_normals=normals(rest);body.GetNormalsAttr().Set(Vt.Vec3fArray(base_normals.tolist()));body.SetNormalsInterpolation(UsdGeom.Tokens.vertex); offsets=[];shape_names=['WalkSquash','WalkStretch'];targets=[]
for name,stretch in zip(shape_names,[1-PARAM['torso_deformation_fraction'],1+PARAM['torso_deformation_fraction']]):
    delta=(pose-pivot)*(np.array([1/math.sqrt(stretch),1/math.sqrt(stretch),stretch])-1)*mask[:,None]
    off=np.einsum('nij,nj->ni',inv,delta); offsets.append(off)
    path=body.GetPath().GetParentPath().AppendChild(name);shape=UsdSkel.BlendShape.Define(stage,path)
    shape.CreateOffsetsAttr(Vt.Vec3fArray(off.tolist()));shape.CreateNormalOffsetsAttr(Vt.Vec3fArray((normals(rest+off)-base_normals).tolist()));targets.append(path)
arm_offsets,arm_info=make_arm_shapes(pose,faces,old_indices,old_weights,names,{key:neutral[index,:3,3] for key,index in ids.items()},unit,floor,PARAM['arm_extension_fraction'],PARAM['arm_return_compression_fraction'])
for name,delta in zip(['WalkArmExtend_L','WalkArmRound_L','WalkArmExtend_R','WalkArmRound_R'],arm_offsets):
    off=np.einsum('nij,nj->ni',inv,delta);offsets.append(off);shape_names.append(name)
    path=body.GetPath().GetParentPath().AppendChild(name);shape=UsdSkel.BlendShape.Define(stage,path);shape.CreateOffsetsAttr(Vt.Vec3fArray(off.tolist()));shape.CreateNormalOffsetsAttr(Vt.Vec3fArray((normals(rest+off)-base_normals).tolist()));targets.append(path)
(REPO/'Assets/Handoff/FibuWalk/arm-regions.json').write_text(json.dumps(arm_info,indent=2)+'\n')
binding=UsdSkel.BindingAPI.Apply(body.GetPrim());binding.CreateBlendShapesAttr(shape_names);binding.CreateBlendShapeTargetsRel().SetTargets(targets)
anim.GetTranslationsAttr().Clear();anim.GetRotationsAttr().Clear();anim.GetScalesAttr().Clear();anim.GetJointsAttr().Set(names);anim.CreateBlendShapesAttr(shape_names);anim.CreateBlendShapeWeightsAttr()
baseT,baseR,baseS=UsdSkel.DecomposeTransforms(base_local);anim.GetTranslationsAttr().Set(baseT);anim.GetRotationsAttr().Set(baseR);anim.GetScalesAttr().Set(baseS);anim.GetBlendShapeWeightsAttr().Set(Vt.FloatArray([0]*len(shape_names)));anim.GetPrim().SetDisplayName('Walk');anim.GetPrim().SetCustomDataByKey('fibuClipName','Walk')
FPS=PARAM['fps'];FRAMES=round(FPS*PARAM['cycle_seconds']);DURATION=FRAMES/FPS;STANCE=PARAM['stance_fraction'];STRIDE=PARAM['stride_stance_distance'];SPEED=STRIDE/(STANCE*DURATION)
stage.SetFramesPerSecond(FPS);stage.SetTimeCodesPerSecond(FPS);stage.SetStartTimeCode(0);stage.SetEndTimeCode(FRAMES)
def affine(rotation=None,translation=None):
    m=np.eye(4)
    if rotation is not None:m[:3,:3]=rotation
    if translation is not None:m[:3,3]=translation
    return m
def rx(a):return Rotation.from_rotvec([a,0,0]).as_matrix()
def ry(a):return Rotation.from_rotvec([0,a,0]).as_matrix()
def rz(a):return Rotation.from_rotvec([0,0,a]).as_matrix()
def align(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);c=np.clip(np.dot(a,b),-1,1);axis=np.cross(a,b);length=np.linalg.norm(axis)
    if length<1e-9:return np.eye(3)
    return Rotation.from_rotvec(axis/length*math.acos(c)).as_matrix()
def descendants(j):return [k for k,n in enumerate(names) if k==j or n.startswith(names[j]+'/')]
def turn(g,j,rotation):
    pivot=g[j,:3,3].copy();t=affine(translation=pivot)@affine(rotation)@affine(translation=-pivot)
    for k in descendants(j):g[k]=t@g[k]
def foot_curve(p):
    if p<STANCE:return STRIDE*(-.5+p/STANCE),0,0,True
    u=(p-STANCE)/(1-STANCE);d=(1-STANCE)/STANCE
    # Quintic matches stance velocity and zero acceleration at both ends.
    y=.5+d*u+(-10-10*d)*u**3+(15+15*d)*u**4+(-6-6*d)*u**5
    return STRIDE*y,(2.7*PARAM['foot_lift_height_fraction'])*math.sin(math.pi*u)**2,math.radians(5)*math.sin(2*math.pi*u),False
legdata={}
for side in ['L','R']:
    a,b,c=[ids[n+'_'+side] for n in ['Thigh','Calf','Foot']]
    legdata[side]=(a,b,c,np.linalg.norm(neutral[b,:3,3]-neutral[a,:3,3]),np.linalg.norm(neutral[c,:3,3]-neutral[b,:3,3]))
def solve_leg(g,side,target,pitch):
    a,b,c,l1,l2=legdata[side];hip=g[a,:3,3].copy();v=target-hip;dist=np.linalg.norm(v)
    # Fibu has soft stumps rather than Mario's separated trouser/shoe joints.
    # Compress/stretch the continuous leg along its length, without a hard knee fold.
    ratio=dist/(l1+l2);assert .50<ratio<1.15,('unsafe leg stretch',side,ratio)
    knee=hip+v*(l1/(l1+l2));width=min(1.08,1/math.sqrt(ratio))
    for j,end,newhead,newend in [(a,b,hip,knee),(b,c,knee,target)]:
        rot=align(neutral[end,:3,3]-neutral[j,:3,3],newend-newhead)
        g[j,:3,:3]=rot@neutral[j,:3,:3]@np.diag([width,ratio,width]);g[j,:3,3]=newhead
    footrot=rx(pitch)
    for j in descendants(c):
        g[j,:3,:3]=footrot@neutral[j,:3,:3];g[j,:3,3]=target+footrot@(neutral[j,:3,3]-neutral[c,:3,3])
def set_sample(g,frame,weights):
    local=[]
    for j in range(len(g)):
        m=g[j] if parents[j]<0 else np.linalg.inv(g[parents[j]])@g[j]
        local.append(Gf.Matrix4d(*m.T.ravel().tolist()))
    t,r,s=UsdSkel.DecomposeTransforms(Vt.Matrix4dArray(local))
    anim.GetTranslationsAttr().Set(t,frame);anim.GetRotationsAttr().Set(r,frame);anim.GetScalesAttr().Set(s,frame);anim.GetBlendShapeWeightsAttr().Set(Vt.FloatArray(weights),frame)
rows=[];previews=[]
for frame in range(FRAMES+1):
    p=frame/FRAMES;angle=2*math.pi*p
    shift=np.array([PARAM['body_lateral_shift']*math.sin(angle)*unit,0,-(.055+2.7*PARAM['body_bob_height_fraction']/2*math.cos(2*angle-.4))*unit])
    bodyrot=ry(-math.radians(PARAM['body_lateral_tilt_degrees'])*math.sin(angle))@rz(math.radians(2)*math.sin(angle))@rx(math.radians(2.0))
    hipcenter=neutral[ids['Waist'],:3,3]
    transform=affine(translation=hipcenter+shift)@affine(bodyrot)@affine(translation=-hipcenter)
    g=np.array([transform@m for m in neutral])
    for side,phase in [('L',0),('R',.5)]:
        a=2*math.pi*(p+phase)
        lagged=a-PARAM['arm_lag_radians'];extension=.5-.5*math.cos(lagged)
        turn(g,ids['Bicep_'+side],ry((-1 if side=='L' else 1)*math.radians(PARAM['arm_outward_arc_degrees'])*extension)@rx(math.radians(PARAM['arm_swing_degrees'])*math.cos(lagged)))
        turn(g,ids['Forearm_'+side],rx(math.radians(5)*math.sin(a-.5)))
    footmeta={}
    for side,phase in [('L',0),('R',.5)]:
        fp=(p+phase)%1;y,lift,pitch,stance=foot_curve(fp);target=neutral[ids['Foot_'+side],:3,3].copy();target+=np.array([0,y*unit,lift*unit])
        solve_leg(g,side,target,pitch);footmeta[side]={'stance':stance,'phase':fp,'target':target.tolist(),'lift':lift}
    pulse=math.cos(2*angle-.4);weights=[max(0,pulse),max(0,-pulse)]
    for phase in [0,.5]:
        extension=.5-.5*math.cos(2*math.pi*(p+phase)-PARAM['arm_lag_radians']);weights.extend([extension,1-extension])
    set_sample(g,frame,weights)
    deformed=rest+sum((off*w for off,w in zip(offsets,weights)),np.zeros_like(rest));points=evaluated(deformed,frame)
    for iteration in range(3):
        for side in ['L','R']:
            maskfoot=((original_pose[:,0]>0) if side=='L' else (original_pose[:,0]<0)) & (((original_pose[:,2]-floor)/unit)<.23)
            desired=floor+footmeta[side]['lift']*unit
            correction=desired-points[maskfoot,2].min()
            target=np.array(footmeta[side]['target']);target[2]+=correction;footmeta[side]['target']=target.tolist()
            pitch=foot_curve(footmeta[side]['phase'])[2];solve_leg(g,side,target,pitch)
        set_sample(g,frame,weights);points=evaluated(deformed,frame)

    rows.append({'frame':frame,'time':frame/FPS,'phase':p,'feet':footmeta,'weights':dict(zip(shape_names,weights))})
    previews.append({'frame':frame,'points':points.tolist()})
layer=SOURCE/'Fibu.Walk.usdc';package=REPO/'Assets/Models/FibuWalk/Fibu.Walk.usdz';package.parent.mkdir(parents=True,exist_ok=True)
stage.GetRootLayer().Export(str(layer));package.unlink(missing_ok=True);assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(layer)),str(package))
(OUT/'preview-data.json').write_text(json.dumps({'fps':FPS,'duration':DURATION,'floor':floor,'unit':unit,'faces':faces.tolist(),'uv':uv.tolist(),'neutral':original_pose.tolist(),'frames':previews}))
metadata={'parameters':PARAM,'schemaVersion':1,'clip':'Walk','fps':FPS,'duration':DURATION,'loop':True,'samples':FRAMES+1,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'packageSHA256':hashlib.sha256(package.read_bytes()).hexdigest(),'strideDistanceAtHeight2_7':SPEED*DURATION,'recommendedSpeedAtHeight2_7':SPEED,'canonicalHeight':2.7,'stanceFraction':STANCE,'forwardSkeletonAxis':[0,-1,0],'skeletonUnitsPerCanonicalUnit':unit,'morphCalculationMode':'additive','bodyMorphs':shape_names,'weightCleanupVertices':edited,'rootMotion':'in-place; game translates actor at recommendedSpeed scaled by displayedHeight / 2.7','samplesTimeline':rows}
(REPO/'Assets/Handoff/FibuWalk/timeline.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('Built',package,'unit',unit,'speed',SPEED,flush=True)
