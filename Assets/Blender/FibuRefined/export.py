"""Replace surface data only; retain original hierarchy, binds, joint names, materials, and wave."""
from pathlib import Path
import json,shutil
from pxr import Usd,UsdGeom,UsdSkel,UsdUtils,Sdf,Gf,Vt
ROOT=Path(__file__).resolve().parent;out=ROOT/'generated';base=json.loads((out/'original.json').read_text());data=json.loads((out/'refined.json').read_text())
stage=Usd.Stage.Open(str(out/'original'/base['rootname']))
mesh=UsdGeom.Mesh(stage.GetPrimAtPath(base['mesh_path']));binding=UsdSkel.BindingAPI.Apply(mesh.GetPrim())
mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in data['points']]))
mesh.GetFaceVertexCountsAttr().Set([len(f) for f in data['faces']]);mesh.GetFaceVertexIndicesAttr().Set([i for f in data['faces'] for i in f])
mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
uv=UsdGeom.PrimvarsAPI(mesh).GetPrimvar('st');uv.GetIndicesAttr().Clear();uv.Set(Vt.Vec2fArray([Gf.Vec2f(*p) for p in data['uv']]))
uv.SetInterpolation(UsdGeom.Tokens.faceVarying)
oldnorm=UsdGeom.PrimvarsAPI(mesh).GetPrimvar('normals')
if oldnorm:mesh.GetPrim().RemoveProperty('primvars:normals');mesh.GetPrim().RemoveProperty('primvars:normals:indices')
mesh.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(*n) for n in data['normals']]));mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
binding.GetJointIndicesPrimvar().Set(Vt.IntArray(data['indices']));binding.GetJointWeightsPrimvar().Set(Vt.FloatArray(data['weights']))
binding.GetJointIndicesPrimvar().SetElementSize(10);binding.GetJointWeightsPrimvar().SetElementSize(10)
for p in stage.Traverse():
    if p.IsA(UsdSkel.Skeleton):UsdSkel.BindingAPI.Apply(p)
points=mesh.GetPointsAttr().Get();mesh.GetExtentAttr().Set(UsdGeom.PointBased.ComputeExtent(points))
(out/'0').mkdir(exist_ok=True);shutil.copy2(out/'original/0/Feeb_skin.png',out/'0/Feeb_skin.png')
stage.GetRootLayer().Export(str(out/'Fibu.Refined.usdc'))
stage=None
target=out/'Fibu.Refined.usdz'
assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(out/'Fibu.Refined.usdc')),str(target))

def posed(path):
    s=Usd.Stage.Open(str(path));s.SetEditTarget(s.GetSessionLayer())
    for p in s.Traverse():
        if p.IsA(UsdGeom.Mesh) or p.IsA(UsdSkel.Skeleton):UsdSkel.BindingAPI.Apply(p)
    cache=UsdSkel.Cache()
    for p in s.Traverse():
        if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    sk=next(UsdSkel.Skeleton(p) for p in s.Traverse() if p.IsA(UsdSkel.Skeleton))
    m=next(UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh))
    sq=cache.GetSkelQuery(sk);query=cache.GetSkinningQuery(m.GetPrim())
    pts=Vt.Vec3fArray(m.GetPointsAttr().Get());assert query.ComputeSkinnedPoints(sq.ComputeSkinningTransforms(0),pts,0)
    idx=list(m.GetFaceVertexIndicesAttr().Get());faces=[];cursor=0
    for n in m.GetFaceVertexCountsAttr().Get():faces.append(idx[cursor:cursor+n]);cursor+=n
    return {'points':[list(p) for p in pts],'faces':faces,'uv':[list(p) for p in UsdGeom.PrimvarsAPI(m).GetPrimvar('st').ComputeFlattened()]}
(out/'posed.json').write_text(json.dumps({'before':posed(out/'original'/base['rootname']),'after':posed(target)}))
print('Packaged candidate; original first wave frame evaluated on both meshes.')
