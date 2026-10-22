"""Validate generated meshes and final runtime packages. Python + NumPy + usd-core."""
from pathlib import Path
from collections import Counter
import json,hashlib,zipfile,struct
import numpy as np
from pxr import Usd,UsdGeom,UsdShade,UsdUtils
ROOT=Path(__file__).resolve().parent
reports=[]
for source in sorted((ROOT/'generated').glob('*.json')):
    d=json.loads(source.read_text());v=np.array(d['vertices']);f=np.array(d['faces'])
    edges=Counter(tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for t in f for i in range(3))
    assert all(n==2 for n in edges.values()), source
    volume=np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6
    assert 0<volume<=len(d['cells'])+.01
    assert len(d['uv'])==len(f)*3==len(d['normals'])
    assert np.isfinite(np.array(d['uv'])).all()
    normals=np.array(d['normals']);assert np.allclose(np.linalg.norm(normals,axis=1),1,atol=.002)
    path=ROOT/'generated'/('terrain_'+d['name']+'.usdz')
    stage=Usd.Stage.Open(str(path));assert stage and stage.GetDefaultPrim()
    assert not UsdUtils.ComputeAllDependencies(str(path))[2]
    mesh=UsdGeom.Mesh(stage.GetPrimAtPath('/Terrain/Mesh'))
    assert len(mesh.GetFaceVertexCountsAttr().Get())==len(f)
    subsets=UsdShade.MaterialBindingAPI(mesh).GetMaterialBindSubsets()
    assert sum(len(s.GetIndicesAttr().Get()) for s in subsets)==len(f)
    assert all(UsdShade.MaterialBindingAPI(s).ComputeBoundMaterial()[0] for s in subsets)
    with zipfile.ZipFile(path) as z,open(path,'rb') as raw:
        assert len([n for n in z.namelist() if n.endswith('.png')])==2
        assert z.testzip() is None
        for item in z.infolist():
            assert item.compress_type==zipfile.ZIP_STORED
            raw.seek(item.header_offset+26);name_len,extra_len=struct.unpack('<HH',raw.read(4))
            assert (item.header_offset+30+name_len+extra_len)%64==0
    reports.append({'filename':path.name,'triangles':len(f),'vertices':len(v),'cells':d['cells'],
        'bounds_y_up_meters':[[float(v[:,0].min()),float(v[:,2].min()),float(-v[:,1].max())],
                               [float(v[:,0].max()),float(v[:,2].max()),float(-v[:,1].min())]],
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'checks':'closed manifold, outward volume, UVs, normals, materials, packaged textures, 64-byte USDZ alignment'})
(ROOT/'generated'/'validation-report.json').write_text(json.dumps(reports,indent=2)+'\n')
print('PASS:',len(reports),'textured terrain assets')
