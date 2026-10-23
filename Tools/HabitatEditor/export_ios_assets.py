"""Run after prepare_assets.py with usd-core installed; no Swift files changed."""
from pathlib import Path
import json,shutil,hashlib,os,tempfile
os.environ.setdefault('TMPDIR',tempfile.gettempdir())
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=ROOT/'Assets/Blender/HabitatWorlds'
namespace={'__file__':str(source/'export.py')}
# Reuse the established textured USD writer without executing its batch export.
exec((source/'export.py').read_text().split('reports=[]')[0],namespace)
namespace['OUT']=HERE/'assets/conversion'
records=[]
output=ROOT/'Assets/Models/EditorKit';output.mkdir(exist_ok=True)
assets=json.loads((HERE/'assets/catalog.json').read_text())['assets']
for asset in assets:
    if asset['kind']!='prop':continue
    ident=asset['id'];path=namespace['OUT']/(ident+'.json')
    for suffix in ['.usdc','.usdz']:(namespace['OUT']/(ident+suffix)).unlink(missing_ok=True)
    report=namespace['export'](ident,json.loads(path.read_text()))
    shutil.copy2(namespace['OUT']/report['filename'],output/report['filename'])
    report['godot_sha256']=hashlib.sha256((HERE/'assets/models'/(ident+'.glb')).read_bytes()).hexdigest();records.append(report)
(output/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
print('Exported and reopened',len(records),'iOS counterparts')
