class_name HabitatTerrain
extends RefCounted

# Boundary subdivision + two uniform Laplacian passes. Shared vertex keys ensure
# connected surfaces, including across materials. Interior faces never exist.
# This solid/collision basis is fibu-rounded-boundary-v1 (not Blender's bevel).
# The visual soft cap/rim extension is fibu-soft-turf-v2; see SOFT_TERRAIN.md.
const SUBDIV = 4
const SMOOTH_WEIGHT = 0.35
const PASSES = 2
const DIRECTIONS = [Vector3i(1,0,0),Vector3i(-1,0,0),Vector3i(0,1,0),Vector3i(0,-1,0),Vector3i(0,0,1),Vector3i(0,0,-1)]
# Each face [origin,u,v]; cross(u,v) points out. Godot triangles use clockwise winding.
const FACES = [
	[Vector3i(4,0,0),Vector3i(0,4,0),Vector3i(0,0,4)],
	[Vector3i(0,0,4),Vector3i(0,4,0),Vector3i(0,0,-4)],
	[Vector3i(0,4,4),Vector3i(4,0,0),Vector3i(0,0,-4)],
	[Vector3i(0,0,0),Vector3i(4,0,0),Vector3i(0,0,4)],
	[Vector3i(0,0,4),Vector3i(4,0,0),Vector3i(0,4,0)],
	[Vector3i(4,0,0),Vector3i(-4,0,0),Vector3i(0,4,0)]
]
var exposed_faces = 0
var triangle_count = 0
var collision_mesh: ArrayMesh
var grass_top_tiles = 0
var grass_rim_edges = 0
const GRASS_THEMES = ["forest","lime","meadow"]
const GRASS_LIFT = .055
const GRASS_OVERHANG = .065

func grassy(id: String, registry: HabitatRegistry) -> bool:
	return registry.assets.get(id,{}).get("theme", "") in GRASS_THEMES

func build(data: Dictionary, registry: HabitatRegistry) -> ArrayMesh:
	var occupied = {}
	for item in data.terrain:
		if HabitatWater.is_water(item): continue
		occupied[Vector3i(item.cell[0],item.cell[1],-item.cell[2])] = item.asset
	var positions: Array[Vector3] = []
	var lookup = {}
	var vertex_keys: Array[Vector3i]=[]
	var adjacent: Array = []
	var quads: Array = []
	var top_cells = {}
	grass_top_tiles=0; grass_rim_edges=0
	exposed_faces = 0
	for cell in occupied:
		for d in range(6):
			if occupied.has(cell+DIRECTIONS[d]): continue
			exposed_faces += 1
			var face = FACES[d]
			if d==2 and grassy(occupied[cell],registry): top_cells[cell]=occupied[cell]
			for i in range(SUBDIV):
				for j in range(SUBDIV):
					var ids = []
					for offset in [Vector2i(0,0),Vector2i(1,0),Vector2i(1,1),Vector2i(0,1)]:
						var key = cell*SUBDIV+face[0]+face[1]/SUBDIV*(i+offset.x)+face[2]/SUBDIV*(j+offset.y)
						if not lookup.has(key):
							lookup[key] = positions.size()
							positions.append(Vector3(key)/SUBDIV+Vector3(-.5,0,-.5))
							vertex_keys.append(key)
							adjacent.append({})
						ids.append(lookup[key])
					for k in range(4):
						adjacent[ids[k]][ids[(k+1)%4]] = true
						adjacent[ids[(k+1)%4]][ids[k]] = true
					quads.append([ids,occupied[cell],"top" if d==2 else "side",d])
	for iteration in range(PASSES):
		var next: Array[Vector3] = []
		for i in range(positions.size()):
			var average = Vector3.ZERO
			for neighbor in adjacent[i]: average += positions[neighbor]
			average /= adjacent[i].size()
			next.append(positions[i].lerp(average,SMOOTH_WEIGHT))
		positions = next
	var normals: Array[Vector3] = []
	normals.resize(positions.size()); normals.fill(Vector3.ZERO)
	for quad in quads:
		var ids = quad[0]
		var n = (positions[ids[1]]-positions[ids[0]]).cross(positions[ids[2]]-positions[ids[0]])
		for id in ids: normals[id] += n
	# Keep the original connected solid boundary as collision/picking geometry.
	# The raised grass shell is decorative and never adds movement collision.
	collision_mesh = emit(positions,quads,normals,registry)
	var visual_quads=[]
	for quad in quads:
		if quad[3]==2 and grassy(quad[1],registry): continue
		visual_quads.append(quad)
	var cap_lookup={}; var cap_outward={}; var cap_flush={}; var rims=[]
	for cell in top_cells:
		grass_top_tiles+=1
		for d in [0,1,4,5]:
			# A neighboring solid of any material suppresses the overhang.
			var neighbor=cell+DIRECTIONS[d]
			var blocked=occupied.has(neighbor)
			if blocked and top_cells.has(neighbor): continue
			if not blocked: grass_rim_edges+=1
			var row=[]
			for step in range(SUBDIV+1):
				var offset: Vector3i
				match d:
					0: offset=Vector3i(4,4,step)
					1: offset=Vector3i(0,4,4-step)
					4: offset=Vector3i(4-step,4,4)
					_: offset=Vector3i(step,4,0)
				var key=cell*SUBDIV+offset
				row.append(key)
				if blocked: cap_flush[key]=true
				else: cap_outward[key]=cap_outward.get(key,Vector3.ZERO)+Vector3(DIRECTIONS[d])
			if not blocked: rims.append([row,top_cells[cell],d])
	# Shared cap keys eliminate grooves at tile joins, including material joins.
	for quad in quads:
		if quad[3]!=2 or not grassy(quad[1],registry): continue
		var cap_ids=[]
		for base_id in quad[0]:
			# Shared exact lattice key, including across material surfaces.
			var key: Vector3i = vertex_keys[base_id]
			if not cap_lookup.has(key):
				var p=positions[base_id]
				var outward: Vector3=cap_outward.get(key,Vector3.ZERO).normalized()
				p+=outward*GRASS_OVERHANG
				# Small world-space undulation; no dome or trough per tile.
				if not cap_flush.has(key): p.y+=GRASS_LIFT+.012*sin(p.x*2.1+p.z*1.7)*sin(p.z*1.3-p.x*.8)
				cap_lookup[key]=positions.size(); positions.append(p)
			cap_ids.append(cap_lookup[key])
		visual_quads.append([cap_ids,quad[1],"top",2])
	var middle_lookup={}; var lower_lookup={}
	for rim in rims:
		var top_ids=[]; var mid_ids=[]; var low_ids=[]
		for key in rim[0]:
			var top_id=cap_lookup[key]; top_ids.append(top_id)
			if not lower_lookup.has(key):
				var p=positions[top_id]
				var outward: Vector3=cap_outward.get(key,Vector3.ZERO).normalized()
				var scallop=.13+.035*cos(TAU*(p.x*1.7+p.z*1.7))+.012*sin(TAU*(p.x*.47-p.z*.91))
				# A bulged middle ring and tucked-under lower ring make a soft lip.
				middle_lookup[key]=positions.size();positions.append(p+outward*.012-Vector3(0,scallop*.5,0))
				lower_lookup[key]=positions.size();positions.append(p-outward*.025-Vector3(0,scallop,0))
			mid_ids.append(middle_lookup[key]);low_ids.append(lower_lookup[key])
		for i in range(SUBDIV):
			visual_quads.append([[top_ids[i],top_ids[i+1],mid_ids[i+1],mid_ids[i]],rim[1],"top",rim[2]])
			visual_quads.append([[mid_ids[i],mid_ids[i+1],low_ids[i+1],low_ids[i]],rim[1],"top",rim[2]])
	# Recompute shared normals after all cap/rim geometry exists.
	var visual_normals: Array[Vector3]=[]; visual_normals.resize(positions.size()); visual_normals.fill(Vector3.ZERO)
	for quad in visual_quads:
		var ids=quad[0]; var n=(positions[ids[1]]-positions[ids[0]]).cross(positions[ids[2]]-positions[ids[0]])
		for id in ids: visual_normals[id]+=n
	triangle_count=visual_quads.size()*2
	return emit(positions,visual_quads,visual_normals,registry)

func emit(positions: Array[Vector3], quads: Array, normals: Array[Vector3], registry: HabitatRegistry) -> ArrayMesh:
	var surfaces = {}
	for quad in quads:
		var key = quad[1]+":"+quad[2]
		if not surfaces.has(key):
			var st = SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
			st.set_material(registry.material_for(quad[1],quad[2])); surfaces[key] = st
		var st = surfaces[key]
		for corner in [0,2,1,0,3,2]:
			var id = quad[0][corner]
			var p = positions[id]
			st.set_normal(normals[id].normalized())
			if quad[3] == 2 or quad[3] == 3: st.set_uv(Vector2(p.x+.5,-p.z+.5))
			elif quad[3] < 2: st.set_uv(Vector2(-p.z+.5,p.y))
			else: st.set_uv(Vector2(p.x+.5,p.y))
			st.add_vertex(p)
	var mesh = ArrayMesh.new()
	for st in surfaces.values():
		st.index(); st.commit(mesh)
	return mesh
