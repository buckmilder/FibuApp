"""Independent runtime-package evaluation; fails on grounding, drift, loop or source changes."""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np
from scipy.spatial import ConvexHull
from pxr import Usd,UsdGeom,UsdSkel,UsdUtils,Vt,Gf
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];metadata=json.loads((REPO/'Assets/Handoff/FibuWalk/timeline.json').read_text());package=REPO/'Assets/Models/FibuWalk/Fibu.Walk.usdz';source=REPO/'Assets/Models/Fibu.Proportions.usdz';checks=[];last_frame=metadata['samples']-1
def check(label,value):
    checks.append({'check':label,'pass':bool(value)})
    if not value:print('FAIL:',label)
s=Usd.Stage.Open(str(package));original=Usd.Stage.Open(str(source))
body=next(UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh));sk=next(UsdSkel.Skeleton(p) for p in s.Traverse() if p.IsA(UsdSkel.Skeleton));anim=next(UsdSkel.Animation(p) for p in s.Traverse() if p.IsA(UsdSkel.Animation));ob=next(UsdGeom.Mesh(p) for p in original.Traverse() if p.IsA(UsdGeom.Mesh));osk=next(UsdSkel.Skeleton(p) for p in original.Traverse() if p.IsA(UsdSkel.Skeleton))
check('approved input hash',hashlib.sha256(source.read_bytes()).hexdigest()==metadata['sourceSHA256']);check('package hash',hashlib.sha256(package.read_bytes()).hexdigest()==metadata['packageSHA256']);check('resolved dependencies',not UsdUtils.ComputeAllDependencies(str(package))[2])
for attr in ['faceVertexCounts','faceVertexIndices','primvars:st','primvars:skel:geomBindTransform']:
    check('unchanged '+attr,body.GetPrim().GetAttribute(attr).Get()==ob.GetPrim().GetAttribute(attr).Get())
for attr in ['joints','bindTransforms','restTransforms']:
    check('unchanged skeleton '+attr,sk.GetPrim().GetAttribute(attr).Get()==osk.GetPrim().GetAttribute(attr).Get())
with zipfile.ZipFile(source) as a,zipfile.ZipFile(package) as b:
    textures=[n for n in a.namelist() if n.lower().endswith('.png')]
    check('embedded artist texture bytes unchanged',all(n in b.namelist() and a.read(n)==b.read(n) for n in textures))
cache=UsdSkel.Cache()
for p in s.Traverse():
    if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
q=cache.GetSkelQuery(sk);sq=cache.GetSkinningQuery(body.GetPrim());rest=np.array(body.GetPointsAttr().Get());bind=UsdSkel.BindingAPI(body);offsets=[np.array(UsdSkel.BlendShape(s.GetPrimAtPath(p)).GetOffsetsAttr().Get()) for p in bind.GetBlendShapeTargetsRel().GetTargets()];names=list(sk.GetJointsAttr().Get());ids={n.split('/')[-1]:i for i,n in enumerate(names)}
check('all 32 joint channels',len(names)==32 and list(anim.GetJointsAttr().Get())==names)
check('complete samples',anim.GetTranslationsAttr().GetNumTimeSamples()==metadata['samples'] and anim.GetRotationsAttr().GetNumTimeSamples()==metadata['samples'])
for p in bind.GetBlendShapeTargetsRel().GetTargets():
    shape=UsdSkel.BlendShape(s.GetPrimAtPath(p));check(str(p)+' finite offsets and normals',np.isfinite(shape.GetOffsetsAttr().Get()).all() and len(shape.GetNormalOffsetsAttr().Get())==len(rest))
def points(frame):
    v=rest+sum((off*w for off,w in zip(offsets,anim.GetBlendShapeWeightsAttr().Get(frame))),np.zeros_like(rest));v=Vt.Vec3fArray(v.tolist());assert sq.ComputeSkinnedPoints(q.ComputeSkinningTransforms(frame),v,frame);return np.array(v)
# Original neutral foot vertex masks are independent of the animated sample minima.
oc=UsdSkel.Cache()
for p in original.Traverse():
    if p.IsA(UsdSkel.Root):oc.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
oq=oc.GetSkelQuery(osk);osq=oc.GetSkinningQuery(ob.GetPrim());v=ob.GetPointsAttr().Get();osq.ComputeSkinnedPoints(oq.ComputeSkinningTransforms(0),v,0);neutral=np.array(v);unit=metadata['skeletonUnitsPerCanonicalUnit'];floor=neutral[:,2].min();
# The new support weights deliberately rebind lower-body vertices, retaining the approved neutral silhouette.
nv=body.GetPointsAttr().Get();sq.ComputeSkinnedPoints(oq.ComputeSkinningTransforms(0),nv,0);check('approved neutral silhouette after rebind',np.max(np.linalg.norm(np.array(nv)-neutral,axis=1))/unit<1e-5)
K=bind.GetJointWeightsPrimvar().GetElementSize();weights=np.array(bind.GetJointWeightsPrimvar().Get()).reshape(-1,K);check('normalized nonnegative support weights',np.all(weights>=0) and np.allclose(weights.sum(axis=1),1,atol=1e-5))
indices=np.array(bind.GetJointIndicesPrimvar().Get()).reshape(-1,K);oldbind=UsdSkel.BindingAPI(ob);oldindices=np.array(oldbind.GetJointIndicesPrimvar().Get()).reshape(-1,K);oldweights=np.array(oldbind.GetJointWeightsPrimvar().Get()).reshape(-1,K);upper=(neutral[:,2]-floor)/unit>=1.25
check('upper-body weights unchanged',np.array_equal(indices[upper],oldindices[upper]) and np.array_equal(weights[upper],oldweights[upper]))
foot_masks={'L':(neutral[:,0]>0)&(neutral[:,2]<floor+.24*unit),'R':(neutral[:,0]<0)&(neutral[:,2]<floor+.24*unit)}
frames=[points(f/2) for f in range(last_frame*2+1)];allpoints=np.array(frames);check('all samples and half samples finite',np.isfinite(allpoints).all());check('closed mesh loop',np.max(np.abs(frames[0]-frames[-1]))/unit<1e-5)
for attr in [anim.GetTranslationsAttr(),anim.GetRotationsAttr(),anim.GetScalesAttr(),anim.GetBlendShapeWeightsAttr()]:check('closed '+attr.GetName(),np.allclose(np.array(attr.Get(0)),np.array(attr.Get(last_frame)),atol=1e-5) if attr!=anim.GetRotationsAttr() else all(abs(abs(Gf.Dot(a,b))-1)<1e-5 for a,b in zip(attr.Get(0),attr.Get(last_frame))))
minfloor=float((allpoints[:,:,2].min()-floor)/unit);print('min floor',minfloor)
stance_errors=[];drift=[]
for side in ['L','R']:
    for row in metadata['samplesTimeline']:
        if not row['feet'][side]['stance']:continue
        p=frames[row['frame']*2];stance_errors.append(abs(float(p[foot_masks[side],2].min()-floor))/unit)
    for a,b in zip(metadata['samplesTimeline'],metadata['samplesTimeline'][1:]):
        fa,fb=a['feet'][side],b['feet'][side]
        if fa['stance'] and fb['stance'] and fb['phase']>fa['phase']:
            ga=q.ComputeJointSkelTransforms(a['frame'])[ids['Foot_'+side]].ExtractTranslation();gb=q.ComputeJointSkelTransforms(b['frame'])[ids['Foot_'+side]].ExtractTranslation();dy=(gb[1]-ga[1])/unit-metadata['recommendedSpeedAtHeight2_7']/metadata['fps'];drift.append(abs(dy))
print('max stance ground error',max(stance_errors),'ankle slide error',max(drift))
check('no deep ground penetration',minfloor>-.002);check('stance soles remain near floor',max(stance_errors)<.002);check('planted foot cancels actor travel',max(drift)<.001)
check('swing feet visibly clear ground',max(row['feet']['L']['lift'] for row in metadata['samplesTimeline'])>.98*2.7*metadata['parameters']['foot_lift_height_fraction'])
# Edge stretch rejects unstable spikes; deliberate localized soft deformation is allowed.
raw=list(body.GetFaceVertexIndicesAttr().Get());edges=set();cursor=0
for n in body.GetFaceVertexCountsAttr().Get():
    f=raw[cursor:cursor+n];cursor+=n
    for a,b in zip(f,f[1:]+f[:1]):edges.add(tuple(sorted([a,b])))
e=np.array(sorted(edges));base=np.linalg.norm(neutral[e[:,0]]-neutral[e[:,1]],axis=1);lengths=np.linalg.norm(allpoints[:,e[:,0]]-allpoints[:,e[:,1]],axis=2);ratios=lengths/np.maximum(base,1e-8);print('max edge ratio',ratios.max())
check('bounded deformation',ratios.max()<2.5 and np.ptp(allpoints[:,:,2],axis=1).max()/unit<2.9)
regions=json.loads((REPO/'Assets/Handoff/FibuWalk/arm-regions.json').read_text())
for side in ['L','R']:
    allowed=np.zeros(len(rest),bool);allowed[regions[side]['regionVertexIds']]=True
    for name,off in zip(anim.GetBlendShapesAttr().Get(),offsets):
        if name.endswith('_'+side):check(name+' isolated and pinned',np.max(np.linalg.norm(off[~allowed],axis=1))<1e-6 and regions[side]['pinnedBoundaryVertices']>0)
torso_mask=(neutral[:,2]-floor)/unit>.9
for region in regions.values():torso_mask[region['regionVertexIds']]=False
neutral_hull=ConvexHull(neutral[torso_mask]).volume;torso_ratios=[ConvexHull(p[torso_mask]).volume/neutral_hull for p in frames]
check('torso convex hull volume stays within five percent of neutral',min(torso_ratios)>.95 and max(torso_ratios)<1.05)
check('restrained torso shape targets',metadata['parameters']['torso_deformation_fraction']<=.02)
check('exact requested cycle',abs(metadata['duration']-metadata['parameters']['cycle_seconds'])<=.5/metadata['fps'])
check('bounded arm swing and extension configured',0<=metadata['parameters']['arm_swing_degrees']<=30 and 0<=metadata['parameters']['arm_extension_fraction']<=.15)

report={'checksPassed':sum(c['pass'] for c in checks),'checksFailed':sum(not c['pass'] for c in checks),'minGroundOffset':minfloor,'maxStanceGroundError':max(stance_errors),'maxAnkleSlideError':max(drift),'maxEdgeStretchRatio':float(ratios.max()),'torsoConvexHullVolumeRatio':[min(torso_ratios),max(torso_ratios)],'packageSHA256':metadata['packageSHA256'],'checks':checks}
(REPO/'Assets/Handoff/FibuWalk/validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS' if not report['checksFailed'] else 'FAIL',report['checksPassed'],'checks,',report['checksFailed'],'failures');assert not report['checksFailed']
