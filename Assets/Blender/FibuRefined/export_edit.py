"""Run on Fibu.Refined.blend to capture rest-mesh edits for export.py.
Do not apply the editing rig: the runtime USD retains its original bind transforms.
"""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated';OUT.mkdir(exist_ok=True)
body=bpy.data.objects['Fibu.Refined'];mesh=body.data;mesh.calc_loop_triangles();offset=body['raw_height_offset']
indices=[];weights=[];maxdrop=0
for vertex in mesh.vertices:
    row=sorted([(g.group,g.weight) for g in vertex.groups if g.weight>1e-8],key=lambda g:-g[1])
    maxdrop=max(maxdrop,sum(w for j,w in row[10:]));row=row[:10];total=sum(w for j,w in row);assert total>0
    row=[(j,w/total) for j,w in row]+[(0,0)]*(10-len(row))
    indices.extend(j for j,w in row);weights.extend(w for j,w in row)
uv=mesh.uv_layers.active.data
data={'points':[[offset-v.co.z,v.co.y,v.co.x] for v in mesh.vertices],
      'faces':[list(p.vertices) for p in mesh.polygons],
      'uv':[list(uv[i].uv) for p in mesh.polygons for i in p.loop_indices],
      'normals':[[-mesh.corner_normals[i].vector.z,mesh.corner_normals[i].vector.y,mesh.corner_normals[i].vector.x] for p in mesh.polygons for i in p.loop_indices],
      'indices':indices,'weights':weights,'max_discarded_weight':maxdrop,'triangles':len(mesh.loop_triangles)}
(OUT/'refined.json').write_text(json.dumps(data))
print('Captured editable rest surface:',len(mesh.vertices),'vertices')
