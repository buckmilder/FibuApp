from pathlib import Path
import json
from pxr import Usd,UsdSkel,UsdGeom,Vt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';result={'clips':{}}
for name in ['Jump','Sit']:
    stage=Usd.Stage.Open(str(OUT/('Fibu.Anim.'+name+'.usdz')));cache=UsdSkel.Cache()
    for p in stage.Traverse():
        if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    sk=next(UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton));m=next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh));query=cache.GetSkelQuery(sk);skin=cache.GetSkinningQuery(m.GetPrim())
    frames=[]
    for i in range(13):
        t=stage.GetEndTimeCode()*i/12;points=Vt.Vec3fArray(m.GetPointsAttr().Get());assert skin.ComputeSkinnedPoints(query.ComputeSkinningTransforms(t),points,t);frames.append([list(p) for p in points])
    result['clips'][name]=frames
base=json.loads((OUT/'previews.json').read_text());first=next(iter(base['poses'].values()))
result.update({'floor':base['floor'],'height':base['height'],'faces':first['faces'],'uv':first['uv']})
(OUT/'gif-data.json').write_text(json.dumps(result))
