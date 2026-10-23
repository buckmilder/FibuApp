"""Read the approved model's neutral skeleton and evaluated mesh without edits."""
from pathlib import Path
import json,hashlib
import numpy as np
from pxr import Usd,UsdGeom,UsdSkel
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=ROOT/'generated';OUT.mkdir(exist_ok=True)
source=REPO/'Assets/Models/Fibu.Proportions.usdz';s=Usd.Stage.Open(str(source));sk=next(UsdSkel.Skeleton(p) for p in s.Traverse() if p.IsA(UsdSkel.Skeleton));body=next(UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh));cache=UsdSkel.Cache()
for p in s.Traverse():
 if p.IsA(UsdSkel.Root):cache.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
q=cache.GetSkelQuery(sk);sq=cache.GetSkinningQuery(body.GetPrim());v=body.GetPointsAttr().Get();assert sq.ComputeSkinnedPoints(q.ComputeSkinningTransforms(0),v,0);points=np.array(v);unit=float(np.ptp(points[:,2])/2.7);floor=float(points[:,2].min());names=list(sk.GetJointsAttr().Get());parents=list(UsdSkel.Topology(names).GetParentIndices());heads=np.array([m.ExtractTranslation() for m in q.ComputeJointSkelTransforms(0)])
def norm(p):return [float(p[0]/unit),float(p[1]/unit),float((p[2]-floor)/unit)]
raw=list(body.GetFaceVertexIndicesAttr().Get());faces=[];cursor=0
for count in body.GetFaceVertexCountsAttr().Get():faces.append(raw[cursor:cursor+count]);cursor+=count
payload={'source':str(source.relative_to(REPO)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'pose':'original neutral animation sample 0, not the rejected walk','points':[norm(p) for p in points],'faces':faces,'joints':[{'path':n,'name':n.split('/')[-1],'parent':parents[i],'position':norm(heads[i])} for i,n in enumerate(names)]}
(OUT/'rig.json').write_text(json.dumps(payload));print('Extracted',len(names),'joints from approved model')
