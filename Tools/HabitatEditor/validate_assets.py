"""Optional asset integrity check; requires Python usd-core (not editor runtime)."""
from pathlib import Path
import json,hashlib,zipfile,struct,math
from pxr import Usd,UsdGeom,UsdUtils
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
catalog=json.loads((HERE/'assets/catalog.json').read_text())['assets']
manifest=json.loads((ROOT/'Assets/Models/EditorKit/manifest.json').read_text())
records={r['filename']:r for r in manifest}
for asset in catalog:
    assert (HERE/'assets/thumbnails'/f"{asset['id']}.png").is_file(),asset['id']
    if asset['kind']!='prop':continue
    path=ROOT/asset['ios'];record=records[path.name]
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
    assert hashlib.sha256((HERE/asset['godot'].replace('res://','')).read_bytes()).hexdigest()==record['godot_sha256']
    stage=Usd.Stage.Open(str(path));assert stage
    assert UsdGeom.GetStageUpAxis(stage)=='Y' and UsdGeom.GetStageMetersPerUnit(stage)==1
    assert not UsdUtils.ComputeAllDependencies(str(path))[2]
    points=[]
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            mesh=UsdGeom.Mesh(prim);ps=mesh.GetPointsAttr().Get();points.extend(ps)
            assert all(math.isfinite(c) for p in ps for c in p)
            assert all(0<=i<len(ps) for i in mesh.GetFaceVertexIndicesAttr().Get())
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    assert abs(lo[1])<1e-4,(asset['id'],lo)
    assert all(abs(hi[i]-lo[i]-asset['dimensions'][i])<1e-4 for i in range(3)),asset['id']
    with zipfile.ZipFile(path) as z:
        assert all(not n.startswith('/') and '..' not in n.split('/') for n in z.namelist())
        with path.open('rb') as f:
            for info in z.infolist():
                f.seek(info.header_offset);header=f.read(30);name_len,extra_len=struct.unpack_from('<HH',header,26)
                assert (info.header_offset+30+name_len+extra_len)%64==0
print(f'{len(catalog)} thumbnails and {len(records)} paired GLB/USDZ props: hashes, dimensions, grounding, geometry, dependencies and archive alignment passed. Procedural water is generated from its layout contract, not a static USDZ.')
