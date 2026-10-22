"""Render existing original + eleven supplied skins on the candidate UVs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'preview.py').read_text().split('for label,angle in')[0]
exec(compile(code,str(ROOT/'preview.py'),'exec'))
for o in objects:o.hide_render=True
for o in scene.objects:
    if o.type=='MESH' and o.name not in ['before','after']:o.hide_render=True
paths=[OUT/'original/0/Feeb_skin.png']+sorted((ROOT.parents[2]/'Assets/Skins/Source').glob('*.texture.png'))
for i,path in enumerate(paths):
    o=objects[1].copy();o.data=objects[1].data.copy();scene.collection.objects.link(o);o.hide_render=False
    o.location=((i%4-1.5)*2.15,0,(2-i//4)*3.05)
    m=mat.copy();m.name=path.stem
    node=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE');node.image=bpy.data.images.load(str(path))
    o.data.materials.clear();o.data.materials.append(m)
cam.location=(0,-20,4.4);cam.rotation_euler=(Vector((0,0,4.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=10.4
for light in (o for o in scene.objects if o.type=='LIGHT'):
    light.location=(0,-12,5);light.rotation_euler=(Vector((0,0,4.4))-light.location).to_track_quat('-Z','Y').to_euler()
    light.data.energy=2400;light.data.size=10
world.node_tree.nodes['Background'].inputs[1].default_value=.7
scene.render.resolution_x=1800;scene.render.resolution_y=1800;scene.cycles.samples=24
scene.render.filepath=str(OUT/'skins.png');bpy.ops.render.render(write_still=True)
(OUT/'skin-order.json').write_text(json.dumps([p.name for p in paths],indent=2))
