from pathlib import Path
import json,hashlib,zipfile,struct
import numpy as np
from pxr import Usd,UsdGeom,UsdShade,UsdUtils
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';reports=json.loads((OUT/'manifest.json').read_text())
assert len(reports)==48
for item in reports:
    p=OUT/item['filename'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
    stage=Usd.Stage.Open(str(p));assert stage and stage.GetDefaultPrim();assert not UsdUtils.ComputeAllDependencies(str(p))[2]
    meshes=[UsdGeom.Mesh(q) for q in stage.Traverse() if q.IsA(UsdGeom.Mesh)]
    assert len(meshes)==item['meshes']
    for m in meshes:
        pts=np.array(m.GetPointsAttr().Get());idx=np.array(m.GetFaceVertexIndicesAttr().Get());n=sum(m.GetFaceVertexCountsAttr().Get())
        assert np.isfinite(pts).all() and idx.min()>=0 and idx.max()<len(pts) and len(idx)==n
        normal=np.array(m.GetNormalsAttr().Get());assert len(normal)==n and np.allclose(np.linalg.norm(normal,axis=1),1,atol=.003)
        uv=np.array(UsdGeom.PrimvarsAPI(m).GetPrimvar('st').Get());assert len(uv)==n and np.isfinite(uv).all()
        if item['filename'].startswith('terrain_'):assert np.all(np.ptp(uv,axis=0)>.01) and uv.min()>-.001 and uv.max()<6,'Invalid terrain UVs'
        subsets=UsdShade.MaterialBindingAPI(m).GetMaterialBindSubsets();assert sum(len(s.GetIndicesAttr().Get()) for s in subsets)==len(m.GetFaceVertexCountsAttr().Get())
        assert all(UsdShade.MaterialBindingAPI(s).ComputeBoundMaterial()[0] for s in subsets)
    if item['filename'].startswith('habitat_'):
        v=np.array(meshes[0].GetPointsAttr().Get());assert np.allclose(np.ptp(v,axis=0)[[0,2]],[9,9],atol=.001)
    with zipfile.ZipFile(p) as z,open(p,'rb') as raw:
        assert z.testzip() is None
        png=[s for s in z.namelist() if s.endswith('.png')]
        assert len(png)>=6
        for info in z.infolist():
            assert info.compress_type==zipfile.ZIP_STORED
            raw.seek(info.header_offset+26);a,b=struct.unpack('<HH',raw.read(4));assert (info.header_offset+30+a+b)%64==0
    item['validation']='finite indexed geometry; unit normals; UV/material coverage; textures resolved; aligned USDZ; 9×9 base where applicable'
(OUT/'validated-manifest.json').write_text(json.dumps(reports,indent=2)+'\n')
print('PASS: all 45 painted modules and three 9×9 habitats')
