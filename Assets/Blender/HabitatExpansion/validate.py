"""Validate terrain plus closed foliage components, runtime packaging, and exact export hashes."""
from pathlib import Path
from collections import Counter
import json,hashlib,struct,zipfile
import numpy as np
from pxr import Usd,UsdGeom,UsdShade,UsdUtils
ROOT=Path(__file__).resolve().parent
report=[]
for source in sorted((ROOT/'generated').glob('*.json')):
    if source.name=='validation-report.json':continue
    d=json.loads(source.read_text());v=np.array(d['vertices']);f=np.array(d['faces'])
    assert np.isfinite(v).all() and f.min()>=0 and f.max()<len(v)
    edges=Counter(tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for t in f for i in range(3))
    assert all(n==2 for n in edges.values()),(source,'nonmanifold')
    normals=np.array(d['normals']);assert len(normals)==len(f)*3
    assert np.allclose(np.linalg.norm(normals,axis=1),1,atol=.002)
    # Check every disconnected component: foliage is several overlapping closed solids.
    neighbors=[set() for _ in v]
    for t in f:
        for i in range(3):neighbors[t[i]].add(t[(i+1)%3]);neighbors[t[(i+1)%3]].add(t[i])
    remaining=set(range(len(v)));components=[]
    while remaining:
        seed=next(iter(remaining));group={seed};remaining.remove(seed);queue=[seed]
        while queue:
            for j in neighbors[queue.pop()]:
                if j in remaining:remaining.remove(j);group.add(j);queue.append(j)
        components.append(group)
    for group in components:
        ff=np.array([t for t in f if t[0] in group]);center=v[list(group)].mean(axis=0);vv=v-center
        vol=np.einsum('ij,ij->i',vv[ff[:,0]],np.cross(vv[ff[:,1]],vv[ff[:,2]])).sum()/6
        assert vol>1e-9,(source,'inward component',vol)
    terrain='textures' in d;name=('terrain_' if terrain else '')+d['name'];path=ROOT/'generated'/(name+'.usdz')
    stage=Usd.Stage.Open(str(path));assert stage and not UsdUtils.ComputeAllDependencies(str(path))[2]
    prim='/Terrain/Mesh' if terrain else '/Foliage/Mesh';mesh=UsdGeom.Mesh(stage.GetPrimAtPath(prim))
    assert len(mesh.GetPointsAttr().Get())==len(v)
    subsets=UsdShade.MaterialBindingAPI(mesh).GetMaterialBindSubsets()
    assert sum(len(s.GetIndicesAttr().Get()) for s in subsets)==len(f)
    assert all(UsdShade.MaterialBindingAPI(s).ComputeBoundMaterial()[0] for s in subsets)
    with zipfile.ZipFile(path) as z,open(path,'rb') as raw:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.endswith('.png')])==(2 if terrain else 0)
        for item in z.infolist():
            assert item.compress_type==zipfile.ZIP_STORED
            raw.seek(item.header_offset+26);a,b=struct.unpack('<HH',raw.read(4));assert (item.header_offset+30+a+b)%64==0
    report.append({'filename':path.name,'triangles':len(f),'components':len(components),'cells':d.get('cells'),
        'bounds_y_up_meters':[[float(v[:,0].min()),float(v[:,2].min()),float(-v[:,1].max())],[float(v[:,0].max()),float(v[:,2].max()),float(-v[:,1].min())]],
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'generated'/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(report),'assets; every closed component points outward; all packaged resources resolve.')
