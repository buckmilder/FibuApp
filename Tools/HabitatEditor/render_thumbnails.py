"""Blender thumbnail generator; editor does not require Blender at runtime."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
HERE=Path(__file__).resolve().parent
catalog=json.loads((HERE/'assets/catalog.json').read_text())
for asset in catalog['assets']:
    if asset['kind']=='water':continue # Rendered by Godot tests/render_water.gd
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if asset['kind']=='prop':bpy.ops.import_scene.gltf(filepath=str(HERE/asset['godot'].replace('res://','')))
    else:
        bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.5));o=bpy.context.object
        bevel=o.modifiers.new('Soft edges','BEVEL');bevel.width=.085;bevel.segments=4;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
        for face in ['side','top']:
            m=bpy.data.materials.new(face);m.use_nodes=True;tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(HERE/'assets/textures'/f"{asset['theme']}_{face}.png"));m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color']);o.data.materials.append(m)
        uv=o.data.uv_layers.active or o.data.uv_layers.new()
        for p in o.data.polygons:
            p.material_index=1 if p.normal.z>.55 else 0
            for li in p.loop_indices:
                v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.y) if p.normal.z>.55 else (v.x+v.y,v.z)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));target=(hi+lo)/2;size=max(hi-lo)
    bpy.ops.object.light_add(type='AREA',location=target+Vector((-3,-4,6))*size);bpy.context.object.data.energy=900*size*size;bpy.context.object.data.size=5*size
    bpy.ops.object.camera_add(location=target+Vector((3,-5,3.5))*size);cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.65
    scene=bpy.context.scene;scene.camera=cam;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.use_denoising=False;scene.render.film_transparent=True;scene.render.resolution_x=128;scene.render.resolution_y=128;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(HERE/'assets/thumbnails'/f"{asset['id']}.png");bpy.ops.render.render(write_still=True)
