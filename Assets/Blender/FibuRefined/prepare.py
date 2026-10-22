"""Read the authoritative runtime asset without modifying the original files."""
from pathlib import Path
import json,zipfile
from pxr import Usd,UsdGeom,UsdSkel,Gf
ROOT=Path(__file__).resolve().parent;repo=ROOT.parents[2];out=ROOT/'generated';out.mkdir(exist_ok=True)
with zipfile.ZipFile(repo/'Assets/Models/Fibu.Soft.usdz') as z:
    for info in z.infolist():
        target=out/'original'/info.filename
        assert target.resolve().is_relative_to((out/'original').resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
    rootname=z.namelist()[0]
stage=Usd.Stage.Open(str(out/'original'/rootname))
mesh=next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh))
sk=next(UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton))
binding=UsdSkel.BindingAPI(mesh)
points=[list(v) for v in mesh.GetPointsAttr().Get()]
idx=list(mesh.GetFaceVertexIndicesAttr().Get());faces=[];offset=0
for n in mesh.GetFaceVertexCountsAttr().Get():faces.append(idx[offset:offset+n]);offset+=n
uv=[list(v) for v in UsdGeom.PrimvarsAPI(mesh).GetPrimvar('st').ComputeFlattened()]
jointnames=list(sk.GetJointsAttr().Get());inverse=binding.GetGeomBindTransformAttr().Get().GetInverse()
heads=[list(inverse.Transform(m.ExtractTranslation())) for m in sk.GetBindTransformsAttr().Get()]
data={'points':points,'faces':faces,'uv':uv,'joints':jointnames,'heads':heads,
      'indices':list(binding.GetJointIndicesPrimvar().Get()),'weights':list(binding.GetJointWeightsPrimvar().Get()),
      'influences':binding.GetJointIndicesPrimvar().GetElementSize(),'mesh_path':str(mesh.GetPath()),'rootname':rootname}
(out/'original.json').write_text(json.dumps(data))
print('Read',len(points),'vertices and',len(jointnames),'joints')
