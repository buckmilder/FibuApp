"""Capture generated module data from the editable source, with fresh post-modifier UV handles."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated'
for theme in ['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']:
    for layout in ['single','pair','platform','corner','terrace']:
        o=bpy.data.objects[theme+'_'+layout];mesh=o.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active;tris=list(mesh.loop_triangles)
        data={'name':o.name,'vertices':[list(v.co) for v in mesh.vertices],
              'faces':[list(t.vertices) for t in tris],
              'normals':[list(mesh.corner_normals[li].vector) for t in tris for li in t.loops],
              'uv':[list(uv.data[li].uv) for t in tris for li in t.loops],
              'material_indices':[t.material_index for t in tris],
              'textures':[theme+'_side.png',theme+'_top.png']}
        (OUT/(o.name+'.json')).write_text(json.dumps(data))
print('Captured fresh UV data for all 45 modules')
