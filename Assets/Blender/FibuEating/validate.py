"""Validate the exported eating candidate against the approved proportions model."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from pxr import Usd,UsdGeom,UsdSkel,UsdShade,UsdUtils,Vt,Gf
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=ROOT/'generated'
s=Usd.Stage.Open(str(OUT/'Fibu.Eat.usdz'));baseline=Usd.Stage.Open(str(REPO/'Assets/Models/Fibu.Proportions.usdz'));timeline=json.loads((OUT/'timeline.json').read_text());checks=[]
def check(label,condition):
    assert condition,label
    checks.append(label)
def first(stage,kind):return next(kind(p) for p in stage.Traverse() if p.IsA(kind))
sk=first(s,UsdSkel.Skeleton);oldsk=first(baseline,UsdSkel.Skeleton);body=UsdGeom.Mesh(next(p for p in s.Traverse() if p.GetName()=='Fibu_body'));oldbody=first(baseline,UsdGeom.Mesh);anim=first(s,UsdSkel.Animation)
for attr in ['joints','bindTransforms','restTransforms']:
    check('original skeleton '+attr,sk.GetPrim().GetAttribute(attr).Get()==oldsk.GetPrim().GetAttribute(attr).Get())
for attr in ['points','faceVertexCounts','faceVertexIndices']:
    check('approved body '+attr,body.GetPrim().GetAttribute(attr).Get()==oldbody.GetPrim().GetAttribute(attr).Get())
check('approved body UVs',UsdGeom.PrimvarsAPI(body).GetPrimvar('st').ComputeFlattened()==UsdGeom.PrimvarsAPI(oldbody).GetPrimvar('st').ComputeFlattened())
for prop in ['primvars:skel:jointIndices','primvars:skel:jointWeights','primvars:skel:geomBindTransform']:
    check('approved body '+prop,body.GetPrim().GetAttribute(prop).Get()==oldbody.GetPrim().GetAttribute(prop).Get())
check('resolved package dependencies',not UsdUtils.ComputeAllDependencies(str(OUT/'Fibu.Eat.usdz'))[2])
check('full 85 sample clip',len(anim.GetRotationsAttr().GetTimeSamples())==85)
check('no leg or body bone scaling',len(set(str(anim.GetScalesAttr().Get(i)) for i in range(85)))==1)
check('one bite event',sum(row['biteEvent'] for row in timeline['samples'])==1)
check('returns to neutral joint rotations',np.allclose(np.array(anim.GetRotationsAttr().Get(0)),np.array(anim.GetRotationsAttr().Get(84)),atol=1e-5))
meshes=[UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh) and p.GetName().startswith('Face_')]
check('six separate expressions',len(meshes)==6)
check('neutral default expression', [m.GetPrim().GetName() for m in meshes if m.GetVisibilityAttr().Get()=='inherited']==['Face_smile'])
for row in timeline['samples']:
    frame=row['frame'];visible=[m.GetPrim().GetName() for m in meshes if m.GetVisibilityAttr().Get(frame)=='inherited'];check(f'exclusive expression at {frame}',visible==['Face_'+row['expression']])
    check(f'finite bounded facial weights at {frame}',all(0<=float(w)<=1 for w in anim.GetBlendShapeWeightsAttr().Get(frame)))
for mesh in [body]+meshes:
    bind=UsdSkel.BindingAPI(mesh);K=bind.GetJointWeightsPrimvar().GetElementSize();weights=np.array(bind.GetJointWeightsPrimvar().Get()).reshape(-1,K);indices=np.array(bind.GetJointIndicesPrimvar().Get())
    check(mesh.GetPrim().GetName()+' normalized skin weights',np.allclose(weights.sum(axis=1),1,atol=1e-5) and weights.min()>=-1e-6 and indices.min()>=0 and indices.max()<32)
    normals=np.array(mesh.GetNormalsAttr().Get());check(mesh.GetPrim().GetName()+' smooth normals',len(normals)==len(mesh.GetPointsAttr().Get()) and np.allclose(np.linalg.norm(normals,axis=1),1,atol=1e-4))
    expected=['CheekPuff','Swallow','ArmPrepare','ArmBite'] if mesh.GetPath()==body.GetPath() else ['CheekPuff','Swallow']
    check(mesh.GetPrim().GetName()+' deformation targets',list(bind.GetBlendShapesAttr().Get())==expected)
    for path in bind.GetBlendShapeTargetsRel().GetTargets():
        shape=UsdSkel.BlendShape(s.GetPrimAtPath(path));offsets=np.array(shape.GetOffsetsAttr().Get());check(str(path)+' offsets',offsets.shape==normals.shape and np.isfinite(offsets).all() and len(shape.GetNormalOffsetsAttr().Get())==len(normals))
for record in json.loads((OUT/'skins.json').read_text())['skins']:
    source=OUT/'source/0/Feeb_skin.png' if record['id']=='Original' else REPO/record['source']
    a=np.array(Image.open(source).convert('RGB'));b=np.array(Image.open(OUT/'source'/record['file']).convert('RGB'));mask=np.array(Image.open(OUT/'source'/record['mask']))>0
    check(record['id']+' artist source hash',hashlib.sha256(source.read_bytes()).hexdigest()==record['source_sha256'])
    check(record['id']+' outside repair mask unchanged',np.array_equal(a[~mask],b[~mask]))
    if record['id']!='013':check(record['id']+' no remaining dark painted mouth',not ((b[:,:,0]<100)&(b[:,:,1]<100)&(b[:,:,2]<100)&mask).any())
check('versioned socket timeline',timeline['schemaVersion']==2 and timeline['foodSocket']=='FoodSocket')
check('additive morph calculation',timeline['morphCalculationMode']=='additive')
check('explicit body morph fields',set(timeline['bodyMorphFields'])=={'CheekPuff','Swallow','ArmPrepare','ArmBite'})
check('explicit face morph fields',set(timeline['faceMorphFields'])=={'CheekPuff','Swallow'})
check('no food geometry',[p.GetName() for p in s.Traverse() if p.IsA(UsdGeom.Mesh)]==['Fibu_body','Face_smile','Face_open','Face_lick','Face_chew','Face_swallow','Face_happy'])
socket=UsdGeom.Xform(next(p for p in s.Traverse() if p.GetName()=='FoodSocket'))
check('empty food socket',not list(socket.GetPrim().GetChildren()))
cache=UsdSkel.Cache()
for prim in s.Traverse():
    if prim.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(prim),Usd.PrimDefaultPredicate)
query=cache.GetSkelQuery(sk);skin=cache.GetSkinningQuery(body.GetPrim());rest=np.array(body.GetPointsAttr().Get());binding=UsdSkel.BindingAPI(body);offsets=[np.array(UsdSkel.BlendShape(s.GetPrimAtPath(path)).GetOffsetsAttr().Get()) for path in binding.GetBlendShapeTargetsRel().GetTargets()]
def evaluated(frame):
    values=anim.GetBlendShapeWeightsAttr().Get(frame);vertices=rest+sum((a*w for a,w in zip(offsets,values)),np.zeros_like(rest));points=Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in vertices]);assert skin.ComputeSkinnedPoints(query.ComputeSkinningTransforms(frame),points,frame);return np.array(points)
neutral=evaluated(0);unit=np.ptp(neutral[:,2])/2.7;floor=neutral[:,2].min();z=(neutral[:,2]-floor)/unit
region=json.loads((OUT/'arm-region.json').read_text());arm=np.zeros(len(rest),bool);arm[region['vertexIds']]=True
check('arm isolated to right side',np.all(neutral[arm,0]/unit<-.40))
fixed=(~arm)&(z<1.52);max_torso=0;grip_error=0
triangles=[];cursor=0;raw=list(body.GetFaceVertexIndicesAttr().Get())
for count in body.GetFaceVertexCountsAttr().Get():
    for j in range(1,count-1):triangles.append([raw[cursor],raw[cursor+j],raw[cursor+j+1]])
    cursor+=count
triangles=np.array(triangles)
for row in timeline['samples']:
    frame=row['frame'];points=evaluated(frame);error=np.linalg.norm(points[fixed]-neutral[fixed],axis=1).max()/unit;max_torso=max(max_torso,float(error))
    check(f'fixed torso through sample {frame}',error<1e-5)
    check(f'fixed joint pose through sample {frame}',anim.GetRotationsAttr().Get(frame)==anim.GetRotationsAttr().Get(0) and anim.GetTranslationsAttr().Get(frame)==anim.GetTranslationsAttr().Get(0))
    check(f'socket follows authored hand sample {frame}',np.allclose(np.array(socket.GetLocalTransformation(frame).ExtractTranslation()),row['foodSocketPosition'],atol=1e-5))
    check(f'arm weights convex sample {frame}',row['armPrepare']+row['armBite']<=1+1e-6)
    a,b=row['gripVertexIds'];fraction=row['gripFraction'];tri=points[triangles];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals=np.zeros_like(points)
    for j in range(3):np.add.at(normals,triangles[:,j],cross)
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-10)
    palm=points[a]*(1-fraction)+points[b]*fraction;n=normals[a]*(1-fraction)+normals[b]*fraction;n/=np.linalg.norm(n);expected=palm+n*row['gripOffsetPreviewUnits']*unit
    error=np.linalg.norm(expected-row['foodSocketPosition'])/unit;grip_error=max(grip_error,float(error))
    check(f'socket maintains palm contact sample {frame}',arm[a] and arm[b] and 0<=fraction<=1 and error<1e-5)
check('elastic arm changes surface',np.linalg.norm(evaluated(28)-neutral,axis=1).max()/unit>.5)
check('neutral ending surface',np.allclose(evaluated(84),neutral,atol=1e-5))
report=json.loads((OUT/'validation.json').read_text());report['packagedTorsoMaxDisplacement']=max_torso;report['packagedFoodGripMaxError']=grip_error;check('grounded through animation',report['floorMaxError']<.003);check('mouth follows surface within 0.004 normalized units',report['maxFaceFitError']<.004)
report['exportChecksPassed']=len(checks);report['approvedModelSHA256']=hashlib.sha256((REPO/'Assets/Models/Fibu.Proportions.usdz').read_bytes()).hexdigest();report['packageSHA256']=hashlib.sha256((OUT/'Fibu.Eat.usdz').read_bytes()).hexdigest();(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(f'PASS: {len(checks)} exported asset checks; skeleton, body proportions, skinning, expressions, morphs, package and timing.')
