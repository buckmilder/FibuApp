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
    check(mesh.GetPrim().GetName()+' two facial targets',list(bind.GetBlendShapesAttr().Get())==['CheekPuff','Swallow'])
    for path in bind.GetBlendShapeTargetsRel().GetTargets():
        shape=UsdSkel.BlendShape(s.GetPrimAtPath(path));offsets=np.array(shape.GetOffsetsAttr().Get());check(str(path)+' offsets',offsets.shape==normals.shape and np.isfinite(offsets).all() and len(shape.GetNormalOffsetsAttr().Get())==len(normals))
for record in json.loads((OUT/'skins.json').read_text())['skins']:
    source=OUT/'source/0/Feeb_skin.png' if record['id']=='Original' else REPO/record['source']
    a=np.array(Image.open(source).convert('RGB'));b=np.array(Image.open(OUT/'source'/record['file']).convert('RGB'));mask=np.array(Image.open(OUT/'source'/record['mask']))>0
    check(record['id']+' artist source hash',hashlib.sha256(source.read_bytes()).hexdigest()==record['source_sha256'])
    check(record['id']+' outside repair mask unchanged',np.array_equal(a[~mask],b[~mask]))
    if record['id']!='013':check(record['id']+' no remaining dark painted mouth',not ((b[:,:,0]<100)&(b[:,:,1]<100)&(b[:,:,2]<100)&mask).any())
report=json.loads((OUT/'validation.json').read_text());check('grounded through animation',report['floorMaxError']<.003);check('mouth follows surface within 0.004 normalized units',report['maxFaceFitError']<.004)
report['exportChecksPassed']=len(checks);report['approvedModelSHA256']=hashlib.sha256((REPO/'Assets/Models/Fibu.Proportions.usdz').read_bytes()).hexdigest();report['packageSHA256']=hashlib.sha256((OUT/'Fibu.Eat.usdz').read_bytes()).hexdigest();(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(f'PASS: {len(checks)} exported asset checks; skeleton, body proportions, skinning, expressions, morphs, package and timing.')
