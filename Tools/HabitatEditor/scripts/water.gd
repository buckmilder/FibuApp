class_name HabitatWater
extends RefCounted

const ID = "water_teal"
const DIRS = [Vector3i(1,0,0),Vector3i(-1,0,0),Vector3i(0,1,0),Vector3i(0,-1,0),Vector3i(0,0,1),Vector3i(0,0,-1)]
# Same outward face frames and clockwise front winding as terrain.
const FACES = [
	[Vector3(1,0,0),Vector3(0,1,0),Vector3(0,0,1)],
	[Vector3(0,0,1),Vector3(0,1,0),Vector3(0,0,-1)],
	[Vector3(0,1,1),Vector3(1,0,0),Vector3(0,0,-1)],
	[Vector3(0,0,0),Vector3(1,0,0),Vector3(0,0,1)],
	[Vector3(0,0,1),Vector3(1,0,0),Vector3(0,1,0)],
	[Vector3(1,0,0),Vector3(-1,0,0),Vector3(0,1,0)]
]
var cache = {}
var material_cache = {}
var report = {}
var rebuild_count = 0
var lighting_color=Color.WHITE
var lighting_energy=1.0

static func defaults() -> Dictionary:
	return {"version":1,"shallow_color":"279baf","deep_color":"174c70","opacity":.40,"side_opacity":.40,"depth_strength":.32,"roughness":.48,"highlight_strength":.12,"ripple_speed":.3,"ripple_strength":.025,"ripple_scale":2.1,"animation_enabled":true,"foam_enabled":true,"foam_color":"edfff8","foam_width":.20,"foam_coverage":.70,"foam_speed":.16,"foam_irregularity":.65}

static func validate_style(raw) -> String:
	if not raw is Dictionary: return "Water style must be an object."
	if raw.get("version",1)!=1: return "Unsupported water style version."
	for key in ["shallow_color","deep_color","foam_color"]:
		if raw.has(key) and (not raw[key] is String or not Color.html_is_valid(raw[key])): return "Invalid water color: "+key
	var ranges={"opacity":[.02,.8],"side_opacity":[.02,.8],"depth_strength":[0,2],"roughness":[0,1],"highlight_strength":[0,.5],"ripple_speed":[0,2],"ripple_strength":[0,.1],"ripple_scale":[.1,10],"foam_width":[.02,.3],"foam_coverage":[0,1],"foam_speed":[0,1],"foam_irregularity":[0,1]}
	for key in ranges:
		if raw.has(key) and (not HabitatDocument.finite_number(raw[key]) or raw[key]<ranges[key][0] or raw[key]>ranges[key][1]): return "Invalid water setting: "+key
	for key in ["animation_enabled","foam_enabled"]:
		if raw.has(key) and not raw[key] is bool: return "Invalid water flag: "+key
	return ""

static func is_water(item: Dictionary) -> bool:
	return item.get("asset","")==ID

static func lattice(item: Dictionary) -> Vector3i:
	return Vector3i(item.cell[0],item.cell[1],-item.cell[2])

static func components(data: Dictionary) -> Array:
	var cells={}
	for item in data.terrain:
		if is_water(item): cells[lattice(item)]=item
	var result=[]
	var visited={}
	for start in cells:
		if visited.has(start): continue
		var queue=[start]; var component=[]; visited[start]=true; var cursor=0
		while cursor<queue.size():
			var cell=queue[cursor]; cursor+=1; component.append(cells[cell])
			for dir in DIRS:
				var neighbor=cell+dir
				if cells.has(neighbor) and not visited.has(neighbor): visited[neighbor]=true; queue.append(neighbor)
		component.sort_custom(func(a,b): return HabitatDocument.key(a.cell)<HabitatDocument.key(b.cell))
		result.append(component)
	return result

static func style_for(data: Dictionary, component: Array) -> Dictionary:
	var style=defaults()
	var id=component[0].get("water_style","default")
	style.merge(data.get("water_styles",{}).get(id,{}),true)
	return style

func materials(style: Dictionary) -> Array:
	var key=JSON.stringify(style)
	if material_cache.has(key): return material_cache[key]
	var volume=ShaderMaterial.new(); volume.shader=load("res://assets/water/volume.gdshader")
	for property in ["opacity","side_opacity","depth_strength","highlight_strength","ripple_speed","ripple_strength","ripple_scale","animation_enabled"]: volume.set_shader_parameter(property,style[property])
	volume.set_shader_parameter("roughness_value",style.roughness)
	for property in ["shallow_color","deep_color"]: volume.set_shader_parameter(property,Color(style[property]))
	var foam=ShaderMaterial.new(); foam.shader=load("res://assets/water/foam.gdshader"); foam.render_priority=3
	for property in ["foam_coverage","foam_speed","foam_irregularity","animation_enabled"]: foam.set_shader_parameter(property,style[property])
	foam.set_shader_parameter("foam_color",Color(style.foam_color))
	foam.set_shader_parameter("lighting_color",lighting_color); foam.set_shader_parameter("lighting_energy",lighting_energy)
	material_cache[key]=[volume,foam]
	return material_cache[key]

func build(data: Dictionary) -> Node3D:
	var root=Node3D.new(); root.name="WaterVolumes"
	var solid={}
	for item in data.terrain:
		if not is_water(item): solid[lattice(item)]=true
	var active_cache={}; var active_materials={}
	report={"bodies":0,"faces":0,"top_faces":0,"foam_edges":0,"shore_edges":0,"wall_edges":0,"cells":0}
	for component in components(data):
		var style=style_for(data,component); var neighbors=[]
		for item in component:
			for dir in DIRS:
				var neighbor=lattice(item)+dir
				if solid.has(neighbor): neighbors.append([neighbor.x,neighbor.y,neighbor.z])
		var key=JSON.stringify([component,neighbors,style])
		if not cache.has(key): cache[key]=generate(component,solid,style); rebuild_count+=1
		var entry=cache[key]; active_cache[key]=entry; active_materials[JSON.stringify(style)]=materials(style)
		for property in ["faces","top_faces","foam_edges","shore_edges","wall_edges"]: report[property]+=entry[property]
		report.bodies+=1; report.cells+=component.size()
		var holder=Node3D.new(); holder.name="WaterBody"; root.add_child(holder)
		var instance=MeshInstance3D.new(); instance.mesh=entry.mesh; instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; holder.add_child(instance)
		if entry.foam.get_surface_count()>0:
			var foam=MeshInstance3D.new(); foam.mesh=entry.foam; foam.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; holder.add_child(foam)
		# Editor picking only. Layer 8 is absent from the proxy's collision mask.
		var pick=StaticBody3D.new(); pick.collision_layer=8; pick.collision_mask=0; holder.add_child(pick)
		if entry.mesh.get_surface_count()>0:
			var shape=CollisionShape3D.new(); shape.shape=entry.pick_shape; pick.add_child(shape)
	cache=active_cache; material_cache=active_materials
	return root

func generate(component: Array, solid: Dictionary, style: Dictionary) -> Dictionary:
	var water={}
	for item in component: water[lattice(item)]=true
	var columns={}
	for cell in water:
		var top=cell.y+1; var bottom=cell.y
		while water.has(Vector3i(cell.x,top,cell.z)): top+=1
		while water.has(Vector3i(cell.x,bottom-1,cell.z)): bottom-=1
		columns[cell]=Vector2(top,bottom)
	var entry={"faces":0,"top_faces":0,"foam_edges":0,"shore_edges":0,"wall_edges":0}
	var surfaces=[]; var counts=[0,0,0,0,0,0]; var mats=materials(style)
	for i in range(6):
		var st=SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var mat=mats[0].duplicate(); mat.render_priority=2 if i==2 else (0 if i==3 else 1)
		st.set_material(mat); surfaces.append(st)
	var foam=SurfaceTool.new(); foam.begin(Mesh.PRIMITIVE_TRIANGLES); foam.set_material(mats[1])
	for cell in water:
		for face in range(6):
			if water.has(cell+DIRS[face]) or solid.has(cell+DIRS[face]): continue
			entry.faces+=1; counts[face]+=1
			if face==2: entry.top_faces+=1
			var frame=FACES[face]
			for corner in [Vector2(0,0),Vector2(1,1),Vector2(1,0),Vector2(0,0),Vector2(0,1),Vector2(1,1)]:
				var p=Vector3(cell)+frame[0]+frame[1]*corner.x+frame[2]*corner.y+Vector3(-.5,0,-.5)
				# Average neighboring columns with the same top elevation to avoid tint grids.
				var top=columns[cell].x; var depth=0.0; var count=0
				for dx in [-.001,.001]:
					for dz in [-.001,.001]:
						var neighbor=Vector3i(floori(p.x+.5+dx),cell.y,floori(p.z+.5+dz))
						if columns.has(neighbor) and columns[neighbor].x==top:
							depth+=columns[neighbor].x-columns[neighbor].y; count+=1
				surfaces[face].set_normal(Vector3(DIRS[face])); surfaces[face].set_uv(Vector2(p.x,p.z)); surfaces[face].set_uv2(Vector2(depth/max(count,1),max(0,top-p.y))); surfaces[face].add_vertex(p)
		if water.has(cell+Vector3i.UP) or solid.has(cell+Vector3i.UP): continue
		for dir in [Vector3i.RIGHT,Vector3i.LEFT,Vector3i(0,0,1),Vector3i(0,0,-1)]:
			if water.has(cell+dir): continue
			entry.foam_edges+=1
			var shore=solid.has(cell+dir); var wall=shore and solid.has(cell+dir+Vector3i.UP)
			if shore: entry.shore_edges+=1
			if wall: entry.wall_edges+=1
			if not style.foam_enabled: continue
			var center=Vector3(cell)+Vector3(0,1.006,0)+Vector3(dir)*.49
			var tangent=Vector3(-dir.z,0,dir.x)
			var width=style.foam_width*(.75 if wall else (1.0 if shore else .9))
			add_foam(foam,center-tangent*.5,center+tangent*.5,-Vector3(dir)*width,.9 if shore else 1.0)
			# A small broken ribbon folds over exposed water side edges.
			if not shore: add_foam(foam,center-tangent*.5,center+tangent*.5,Vector3(0,-width*.6,0),.38)
	var mesh=ArrayMesh.new()
	for i in range(surfaces.size()):
		if counts[i]>0: surfaces[i].index(); surfaces[i].commit(mesh)
	var foam_mesh=ArrayMesh.new()
	if style.foam_enabled and entry.foam_edges>0: foam.index(); foam.commit(foam_mesh)
	entry.mesh=mesh; entry.foam=foam_mesh; entry.pick_shape=mesh.create_trimesh_shape() if mesh.get_surface_count()>0 else null
	return entry

func add_foam(st: SurfaceTool, a: Vector3, b: Vector3, inward: Vector3, opacity: float):
	for uv in [Vector2(0,0),Vector2(1,1),Vector2(1,0),Vector2(0,0),Vector2(0,1),Vector2(1,1)]:
		st.set_normal(Vector3.UP); st.set_color(Color(1,1,1,opacity)); st.set_uv(uv); st.add_vertex(a.lerp(b,uv.x)+inward*uv.y)


func set_lighting(settings: Dictionary):
	var sky=HabitatAtmosphere.resolved(settings)
	lighting_color=Color.WHITE.lerp(Color(sky.ambient_color).lerp(Color(sky.sun_color),.5),.3)
	lighting_energy=clamp(.25+sky.sun_energy+sky.ambient_energy,.25,1.0)
	for pair in material_cache.values():
		pair[1].set_shader_parameter("lighting_color",lighting_color)
		pair[1].set_shader_parameter("lighting_energy",lighting_energy)
