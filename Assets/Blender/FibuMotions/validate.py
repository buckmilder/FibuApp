from pathlib import Path
import json,hashlib,numpy as np
from pxr import Usd,UsdGeom,UsdSkel,UsdUtils,Vt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';manifest=json.loads((OUT/'manifest.json').read_text())
base=Usd.Stage.Open(str(ROOT.parents[2]/'Assets/Models/Fibu.Refined.usdz'))
bm=next(UsdGeom.Mesh(p) for p in base.Traverse() if p.IsA(UsdGeom.Mesh));bs=next(UsdSkel.Skeleton(p) for p in base.Traverse() if p.IsA(UsdSkel.Skeleton))
report=[]
for clip in manifest['clips']:
    path=OUT/clip['file'];stage=Usd.Stage.Open(str(path));assert stage and not UsdUtils.ComputeAllDependencies(str(path))[2]
    m=next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh));sk=next(UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton))
    for attr in ['points','faceVertexCounts','faceVertexIndices','primvars:st','primvars:skel:jointIndices','primvars:skel:jointWeights']:
        assert str(m.GetPrim().GetAttribute(attr).Get())==str(bm.GetPrim().GetAttribute(attr).Get()),(clip['name'],attr)
    for attr in ['joints','bindTransforms','restTransforms']:
        assert str(sk.GetPrim().GetAttribute(attr).Get())==str(bs.GetPrim().GetAttribute(attr).Get())
    cache=UsdSkel.Cache()
    for p in stage.Traverse():
        if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    q=cache.GetSkelQuery(sk);skin=cache.GetSkinningQuery(m.GetPrim());anim=next(UsdSkel.Animation(p) for p in stage.Traverse() if p.IsA(UsdSkel.Animation))
    times=anim.GetRotationsAttr().GetTimeSamples();poses=[]
    for t in times:
        p=Vt.Vec3fArray(m.GetPointsAttr().Get());assert skin.ComputeSkinnedPoints(q.ComputeSkinningTransforms(t),p,t)
        v=np.array(p);assert np.isfinite(v).all();poses.append(v)
    assert len(times)==clip['frames_validated']
    assert max(np.linalg.norm(v-poses[0],axis=1).max() for v in poses)>.001,'Static clip'
    if clip['loop']:assert np.max(np.linalg.norm(poses[0]-poses[-1],axis=1))<.002,'Loop seam'
    row=dict(clip);row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();row['checks']='same candidate geometry/UV/weights/binds; all exported frames finite and nonstatic; loop seam checked where applicable';report.append(row)
(OUT/'validated-manifest.json').write_text(json.dumps({'clips':report,'frames_checked':sum(c['frames_validated'] for c in report),'base_candidate_sha256':hashlib.sha256((ROOT.parents[2]/'Assets/Models/Fibu.Refined.usdz').read_bytes()).hexdigest()},indent=2)+'\n')
print('PASS:',len(report),'clips;',sum(c['frames_validated'] for c in report),'exported samples; matching candidate mesh and skeleton')
