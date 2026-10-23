"""Author stand-alone clips on the candidate's original runtime skeleton, 24 fps."""
from pathlib import Path
import json,math,zipfile,shutil
import numpy as np
from pxr import Usd,UsdGeom,UsdSkel,UsdUtils,Gf,Vt,Sdf
ROOT=Path(__file__).resolve().parent;repo=ROOT.parents[2];OUT=ROOT/'generated';OUT.mkdir(exist_ok=True)
original=OUT/'source';original.mkdir(exist_ok=True)
with zipfile.ZipFile(repo/'Assets/Models/Fibu.Refined.usdz') as z:
    for info in z.infolist():
        p=original/info.filename;assert p.resolve().is_relative_to(original.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
    rootname=z.namelist()[0]
base=Usd.Stage.Open(str(original/rootname));sk=next(UsdSkel.Skeleton(p) for p in base.Traverse() if p.IsA(UsdSkel.Skeleton));mesh=next(UsdGeom.Mesh(p) for p in base.Traverse() if p.IsA(UsdGeom.Mesh))
cache=UsdSkel.Cache()
for p in base.Traverse():
    if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
query=cache.GetSkelQuery(sk);local=query.ComputeJointLocalTransforms(0);globalm=query.ComputeJointSkelTransforms(0)
T,R,S=UsdSkel.DecomposeTransforms(local);names=list(sk.GetJointsAttr().Get());ids={n.split('/')[-1]:i for i,n in enumerate(names)}
parents=list(UsdSkel.Topology(sk.GetJointsAttr().Get()).GetParentIndices())
skin=cache.GetSkinningQuery(mesh.GetPrim());pts=Vt.Vec3fArray(mesh.GetPointsAttr().Get());assert skin.ComputeSkinnedPoints(query.ComputeSkinningTransforms(0),pts,0)
floor=min(p[2] for p in pts);height=max(p[2] for p in pts)-floor
face_indices=list(mesh.GetFaceVertexIndicesAttr().Get());faces=[];cursor=0
for count in mesh.GetFaceVertexCountsAttr().Get():faces.append(face_indices[cursor:cursor+count]);cursor+=count
def surface_uv(target):
    uv=list(UsdGeom.PrimvarsAPI(mesh).GetPrimvar('st').ComputeFlattened());indices=list(mesh.GetFaceVertexIndicesAttr().Get());offset=0
    for n in mesh.GetFaceVertexCountsAttr().Get():
        for j in range(1,n-1):
            corners=[offset,offset+j,offset+j+1];q=np.array([uv[k] for k in corners]);A=np.stack((q[1]-q[0],q[2]-q[0]),axis=1)
            if abs(np.linalg.det(A))<1e-10:continue
            b=np.linalg.solve(A,np.array(target)-q[0]);w=np.array([1-b.sum(),*b])
            if w.min()>=-1e-5:return sum((Gf.Vec3d(pts[indices[k]])*float(v) for k,v in zip(corners,w)),Gf.Vec3d())
        offset+=n
    raise RuntimeError('Mouth UV not found')
mouth=surface_uv((.620,.623))
def solve_hand(target):
    rot=Vt.QuatfArray(R);topology=UsdSkel.Topology(names)
    for _ in range(24):
        for joint in ['Hand_R','Forearm_R','Bicep_R','Shoulder_R']:
            locals=UsdSkel.MakeTransforms(T,rot,S);g=[]
            for i,m in enumerate(locals):g.append(m if parents[i]<0 else m*g[parents[i]])
            i=ids[joint];origin=g[i].ExtractTranslation();end=g[ids['Hand_R_end']].ExtractTranslation()
            a=np.array(end-origin);b=np.array(target-origin)
            if np.linalg.norm(a)<1e-6 or np.linalg.norm(b)<1e-6:continue
            a/=np.linalg.norm(a);b/=np.linalg.norm(b);axis=np.cross(a,b);length=np.linalg.norm(axis)
            if length<1e-7:continue
            axis/=length;angle=min(24,math.degrees(math.acos(float(np.clip(np.dot(a,b),-1,1)))))
            parent=parents[i];P=Gf.Matrix4d(1).SetRotate(g[parent].ExtractRotation()) if parent>=0 else Gf.Matrix4d(1)
            L=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Quatd(rot[i])));D=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Vec3d(*axis),angle))
            q=(L*P*D*P.GetInverse()).ExtractRotationQuat();q.Normalize();rot[i]=Gf.Quatf(q)
    return rot
handpose=solve_hand(mouth+Gf.Vec3d(-.1,-.35,-.10))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def rotate(rot,joint,axis,deg):
    i=ids[joint];parent=parents[i];P=Gf.Matrix4d(1)
    if parent>=0:P.SetRotate(globalm[parent].ExtractRotation())
    L=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Quatd(rot[i])))
    D=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Vec3d(*axis),deg))
    q=(L*P*D*P.GetInverse()).ExtractRotationQuat();q.Normalize();rot[i]=Gf.Quatf(q)
specs=[('IdleBreath',4,True,2),('Sit',3,False,2.6),('Whistle',4,True,2),('LayDown',4,False,3.5),('Hungry',4,True,2),('Eat',3,False,.75),('Jump',1.5,False,.65)]
manifest=[];previews={}
for name,duration,loop,preview_time in specs:
    stage=Usd.Stage.Open(str(original/rootname));anim=next(UsdSkel.Animation(p) for p in stage.Traverse() if p.IsA(UsdSkel.Animation))
    anim.GetJointsAttr().Set(names)
    for attr in [anim.GetTranslationsAttr(),anim.GetRotationsAttr(),anim.GetScalesAttr()]:attr.Clear()
    stage.SetTimeCodesPerSecond(24);stage.SetFramesPerSecond(24);stage.SetStartTimeCode(0);stage.SetEndTimeCode(round(duration*24))
    frames=[]
    for frame in range(round(duration*24)+1):
        t=frame/24;s=t/duration;phase=math.tau*s;rot=Vt.QuatfArray(R);trans=Vt.Vec3fArray(T);scales=Vt.Vec3hArray(S)
        env=math.sin(math.pi*s)**2;lift=0
        if name=='IdleBreath':
            breathe=math.sin(phase);rotate(rot,'Stomach',(1,0,0),breathe*.7);rotate(rot,'Neck',(0,1,0),math.sin(phase)*1.5)
            scales[ids['Stomach']]=Gf.Vec3h(1+breathe*.012,1+breathe*.007,1+breathe*.012)
        elif name=='Sit':
            e=smooth(t/1.1)
            for side in ['L','R']:
                rotate(rot,'Thigh_'+side,(1,0,0),-80*e);rotate(rot,'Calf_'+side,(1,0,0),15*e)
            rotate(rot,'Waist',(1,0,0),2*e);rotate(rot,'Chest',(1,0,0),-2*e)
        elif name=='Whistle':
            rotate(rot,'Neck',(0,1,0),7*math.sin(phase)*env)
            for joint in ['Shoulder_R','Bicep_R','Forearm_R','Hand_R']:
                i=ids[joint];rot[i]=Gf.Slerp(env,R[i],handpose[i])
            rotate(rot,'Waist',(0,1,0),2.5*math.sin(phase))
        elif name=='LayDown':
            e=smooth(t/1.5);rotate(rot,'RigBone',(1,0,0),-88*e)
            for side,sign in [('L',-1),('R',1)]:rotate(rot,'Shoulder_'+side,(0,1,0),sign*22*e)
            rotate(rot,'Neck',(0,0,1),8*e)
        elif name=='Hungry':
            rotate(rot,'Waist',(1,0,0),5*env);rotate(rot,'Neck',(1,0,0),-2*env)
            rotate(rot,'Shoulder_R',(0,0,1),-14*env);rotate(rot,'Bicep_R',(1,0,0),18*env)
            rotate(rot,'Hand_R',(0,1,0),math.sin(phase*3)*14*env)
        elif name=='Eat':
            bite=math.sin(phase)**2
            for joint in ['Shoulder_R','Bicep_R','Forearm_R','Hand_R']:
                i=ids[joint];rot[i]=Gf.Slerp(bite,R[i],handpose[i])
            rotate(rot,'Neck',(1,0,0),-2*bite);rotate(rot,'Hand_R',(1,0,0),18*bite)
        else:
            crouch=math.sin(math.pi*min(1,t/.3)) if t<.3 else (math.sin(math.pi*min(1,(t-1.05)/.35)) if t>1.05 else 0)
            for side in ['L','R']:
                rotate(rot,'Thigh_'+side,(1,0,0),-18*crouch);rotate(rot,'Calf_'+side,(1,0,0),30*crouch)
            if .3<t<1.05:lift=height*.22*math.sin(math.pi*(t-.3)/.75)
            arms=math.sin(math.pi*s)
            rotate(rot,'Shoulder_L',(0,1,0),-30*arms);rotate(rot,'Shoulder_R',(0,1,0),30*arms)
        anim.GetTranslationsAttr().Set(trans,frame);anim.GetRotationsAttr().Set(rot,frame);anim.GetScalesAttr().Set(scales,frame);frames.append((frame,lift))
    def getqueries():
        c=UsdSkel.Cache()
        for p in stage.Traverse():
            if p.IsA(UsdSkel.Root):c.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
        ss=UsdSkel.Skeleton(stage.GetPrimAtPath(sk.GetPath()));return c,c.GetSkelQuery(ss),c.GetSkinningQuery(stage.GetPrimAtPath(mesh.GetPath()))
    c,q,skinquery=getqueries()
    # Ground the deformed surface at every sample; only Jump has an airborne offset.
    for frame,lift in frames:
        p=Vt.Vec3fArray(mesh.GetPointsAttr().Get());assert skinquery.ComputeSkinnedPoints(q.ComputeSkinningTransforms(frame),p,frame)
        dz=floor-min(v[2] for v in p)+lift;tr=Vt.Vec3fArray(anim.GetTranslationsAttr().Get(frame));tr[ids['RigBone']]+=Gf.Vec3f(0,0,dz);anim.GetTranslationsAttr().Set(tr,frame)
    c,q,skinquery=getqueries();bounds=[]
    for frame,lift in frames:
        p=Vt.Vec3fArray(mesh.GetPointsAttr().Get());assert skinquery.ComputeSkinnedPoints(q.ComputeSkinningTransforms(frame),p,frame)
        arr=np.array(p);assert np.isfinite(arr).all();assert abs(arr[:,2].min()-floor-lift)<.002
        assert np.ptp(arr,axis=0).max()<height*2
        bounds.append(float(arr[:,2].min()))
        if frame==round(preview_time*24):previews[name]={'points':[list(v) for v in p],'faces':faces,'uv':[list(v) for v in UsdGeom.PrimvarsAPI(UsdGeom.Mesh(stage.GetPrimAtPath(mesh.GetPath()))).GetPrimvar('st').ComputeFlattened()]}
    if loop:
        assert np.allclose(np.array(anim.GetTranslationsAttr().Get(0)),np.array(anim.GetTranslationsAttr().Get(round(duration*24))),atol=.001)
    filename='Fibu.Anim.'+name
    # Export next to the extracted textures so relative references remain valid.
    layer=original/(filename+'.usdc');stage.GetRootLayer().Export(str(layer))
    target=OUT/(filename+'.usdz');assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(layer)),str(target))
    assert Usd.Stage.Open(str(target)) and not UsdUtils.ComputeAllDependencies(str(target))[2]
    manifest.append({'name':name,'file':target.name,'duration_seconds':duration,'loop':loop,'frames_validated':len(frames),'root_motion':'grounded; jump includes vertical motion','preview_seconds':preview_time})
    print(name,'PASS',len(frames),'grounded samples')
(OUT/'manifest.json').write_text(json.dumps({'fps':24,'clips':manifest,'wave':'Use the preserved wave in Assets/Models/Fibu.Refined.usdz','notes':['Whistle is a body/hand gesture: no audio or facial blend shapes.','Eat is a mimed gesture; local app attaches food.','Sit and LayDown enter a held pose; do not loop the transition.']},indent=2)+'\n')
(OUT/'previews.json').write_text(json.dumps({'floor':floor,'height':height,'poses':previews}))
