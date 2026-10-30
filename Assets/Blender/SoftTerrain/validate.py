"""Verify packaged assets against actual generator output, including texture bytes and winding."""
from pathlib import Path
import json,hashlib,zipfile,struct
import numpy as np
from PIL import Image
from pxr import Usd,UsdGeom,UsdShade,UsdUtils
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];GEN=ROOT/'generated';DEST=REPO/'Assets/Models/SoftTerrain';manifest=json.loads((DEST/'manifest.json').read_text());checks=[];modules=[]
def check(label,value):
 checks.append({'check':label,'pass':bool(value)})
 if not value:print('FAIL',label)
for item in manifest['modules']:
 id=item['id'];path=REPO/item['file'];source=json.loads((GEN/(id+'.json')).read_text());stage=Usd.Stage.Open(str(path));meshes=[UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)];check(id+' dependencies resolved',not UsdUtils.ComputeAllDependencies(str(path))[2]);check(id+' packaged hash',hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']);triangles=0
 check(id+' material surfaces match',len(meshes)==len(source['surfaces']))
 for mesh,surface in zip(meshes,source['surfaces']):
  points=np.array(mesh.GetPointsAttr().Get());normals=np.array(mesh.GetNormalsAttr().Get());indices=np.array(mesh.GetFaceVertexIndicesAttr().Get()).reshape(-1,3);triangles+=len(indices)
  check(id+' source geometry exact',np.allclose(points,surface['points'],atol=1e-6));check(id+' finite unit normals',np.isfinite(normals).all() and np.max(np.abs(np.linalg.norm(normals,axis=1)-1))<1e-4);check(id+' UV coverage',len(UsdGeom.PrimvarsAPI(mesh).GetPrimvar('st').Get())==len(points))
  tri=points[indices];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1);average=normals[indices].mean(axis=1);check(id+' nondegenerate outward winding',np.all(area>1e-9) and np.all(np.sum(cross*average,axis=1)>0))
 check(id+' triangle budget',triangles==item['triangles'] and (triangles<=1000 if id.endswith('_single') else True))
 glb=DEST/(id+'.glb');raw=glb.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);json_size,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+json_size]);gtris=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);check(id+' GLB paired triangle count',magic==b'glTF' and version==2 and gtris==triangles)
 check(id+' GLB embedded images',all('bufferView' in image for image in doc['images']))
 with zipfile.ZipFile(path) as package:
  for surface in source['surfaces']:
   matches=[n for n in package.namelist() if n.endswith('/'+surface['texture']) or n==surface['texture']];check(id+' packaged texture unchanged',len(matches)==1 and package.read(matches[0])==(REPO/'Tools/HabitatEditor/assets/textures'/surface['texture']).read_bytes())
 item['glb']=str(glb.relative_to(REPO));item['glbSHA256']=hashlib.sha256(raw).hexdigest();modules.append({'id':id,'triangles':triangles,'visualSurfaceCount':len(meshes)})
for theme in ['forest','lime','meadow']:
 for face in ['top','side']:
  image=np.array(Image.open(ROOT/'textures'/f'{theme}_{face}.png'));check(theme+' '+face+' horizontal texture seam',np.max(np.abs(image[:,0].astype(int)-image[:,-1].astype(int)))<5)
  if face=='top':check(theme+' top vertical texture seam',np.max(np.abs(image[0].astype(int)-image[-1].astype(int)))<5)
  check(theme+' '+face+' 1024 texture',image.shape[:2]==(1024,1024))
report={'generator':'fibu-soft-turf-v2','checksPassed':sum(c['pass'] for c in checks),'checksFailed':sum(not c['pass'] for c in checks),'modules':modules,'checks':checks,'nativeStatus':'SceneKit appearance/collision and both Xcode scheme builds pending local integration; original app unchanged.'};(REPO/'Assets/Handoff/SoftTerrain/validation.json').write_text(json.dumps(report,indent=2)+'\n');(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Asset checks:',report['checksPassed'],'passed;',report['checksFailed'],'failed');assert not report['checksFailed']
