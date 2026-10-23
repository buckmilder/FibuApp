from pathlib import Path
import json,hashlib,numpy as np,zipfile
from pxr import Usd,UsdGeom,UsdSkel,UsdUtils,Vt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';repo=ROOT.parents[2]
old=Usd.Stage.Open(str(OUT/'original'/json.loads((OUT/'original.json').read_text())['rootname']))
new=Usd.Stage.Open(str(OUT/'Fibu.Refined.usdz'))
def mesh(s):return next(UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh))
a,b=mesh(old),mesh(new)
assert not UsdUtils.ComputeAllDependencies(str(OUT/'Fibu.Refined.usdz'))[2]
assert a.GetPath()==b.GetPath()
for p in old.Traverse():
    if p.IsA(UsdSkel.Skeleton) or p.IsA(UsdSkel.Animation):
        other=new.GetPrimAtPath(p.GetPath());assert other
        for attr in p.GetAttributes():
            value=other.GetAttribute(attr.GetName());assert value
            assert str(attr.Get())==str(value.Get()),attr.GetPath()
            assert attr.GetTimeSamples()==value.GetTimeSamples()
            for t in attr.GetTimeSamples():assert str(attr.Get(t))==str(value.Get(t)),(attr.GetPath(),t)
binding=UsdSkel.BindingAPI(b);K=binding.GetJointWeightsPrimvar().GetElementSize();N=len(b.GetPointsAttr().Get())
weights=np.array(binding.GetJointWeightsPrimvar().Get()).reshape(N,K);ids=np.array(binding.GetJointIndicesPrimvar().Get()).reshape(N,K)
assert K==10 and np.allclose(weights.sum(axis=1),1,atol=1e-5)
assert weights.min()>=0 and ids.min()>=0 and ids.max()<32
assert len(b.GetNormalsAttr().Get())==len(b.GetFaceVertexIndicesAttr().Get())
normals=np.array(b.GetNormalsAttr().Get());assert np.allclose(np.linalg.norm(normals,axis=1),1,atol=.002)
def uv_area(m):
    uv=np.array(UsdGeom.PrimvarsAPI(m).GetPrimvar('st').ComputeFlattened());offset=0;area=0
    for n in m.GetFaceVertexCountsAttr().Get():
        poly=uv[offset:offset+n]
        for i in range(1,n-1):
            u,v=poly[i]-poly[0],poly[i+1]-poly[0];area+=abs(u[0]*v[1]-u[1]*v[0])/2
        offset+=n
    assert offset==len(uv)
    return area
area_old,area_new=uv_area(a),uv_area(b);assert abs(area_old-area_new)<1e-5,(area_old,area_new)
area_old,area_new=float(area_old),float(area_new)

def evaluator(s):
    s.SetEditTarget(s.GetSessionLayer())
    for p in s.Traverse():
        if p.IsA(UsdGeom.Mesh) or p.IsA(UsdSkel.Skeleton):UsdSkel.BindingAPI.Apply(p)
    cache=UsdSkel.Cache()
    for p in s.Traverse():
        if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    sk=next(UsdSkel.Skeleton(p) for p in s.Traverse() if p.IsA(UsdSkel.Skeleton))
    q=cache.GetSkelQuery(sk);m=mesh(s);query=cache.GetSkinningQuery(m.GetPrim())
    def compute(t):
        points=Vt.Vec3fArray(m.GetPointsAttr().Get());assert query.ComputeSkinnedPoints(q.ComputeSkinningTransforms(t),points,t)
        pts=np.array(points);assert np.isfinite(pts).all();return pts
    return compute
before,after=evaluator(old),evaluator(new)
anim=next(UsdSkel.Animation(p) for p in old.Traverse() if p.IsA(UsdSkel.Animation))
times=anim.GetRotationsAttr().GetTimeSamples()
for t in times:
    aa,bb=before(t),after(t);dims_a=np.ptp(aa,axis=0);dims_b=np.ptp(bb,axis=0)
    assert np.all(dims_b/dims_a>.7) and np.all(dims_b/dims_a<1.3),(t,dims_a,dims_b)
with zipfile.ZipFile(OUT/'Fibu.Refined.usdz') as z:
    assert z.testzip() is None
    texture=next(n for n in z.namelist() if n.endswith('.png'))
    assert hashlib.sha256(z.read(texture)).hexdigest()==hashlib.sha256((OUT/'original/0/Feeb_skin.png').read_bytes()).hexdigest()
d=json.loads((OUT/'refined.json').read_text())
report={'original_vertices':len(a.GetPointsAttr().Get()),'candidate_vertices':N,'original_triangles':sum(n-2 for n in a.GetFaceVertexCountsAttr().Get()),
 'candidate_triangles':d['triangles'],'joint_count':32,'max_influences':K,'max_trimmed_weight':d['max_discarded_weight'],
 'uv_area_before':area_old,'uv_area_after':area_new,'wave_samples_evaluated':len(times),
 'skeleton_and_animation_attributes_unchanged':True,'original_texture_bytes_unchanged':True,
 'candidate_sha256':hashlib.sha256((OUT/'Fibu.Refined.usdz').read_bytes()).hexdigest(),
 'limitations':['UV coordinates are interpolated onto a denser topology, not identical arrays.','Skin appearance needs SceneKit review.','No Xcode or on-device tests performed.','Watch asset unchanged.']}
(OUT/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
