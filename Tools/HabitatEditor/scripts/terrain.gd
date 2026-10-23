class_name HabitatTerrain
extends RefCounted

# Boundary subdivision + two uniform Laplacian passes. Shared vertex keys ensure
# connected surfaces, including across materials. Interior faces never exist.
# This is the portable fibu-rounded-boundary-v1 algorithm (not Blender's bevel).
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

func build(data: Dictionary, registry: HabitatRegistry) -> ArrayMesh:
	var occupied = {}
	for item in data.terrain:
		if HabitatWater.is_water(item): continue
		occupied[Vector3i(item.cell[0],item.cell[1],-item.cell[2])] = item.asset
	var positions: Array[Vector3] = []
	var lookup = {}
	var adjacent: Array = []
	var quads: Array = []
	exposed_faces = 0
	for cell in occupied:
		for d in range(6):
			if occupied.has(cell+DIRECTIONS[d]): continue
			exposed_faces += 1
			var face = FACES[d]
			for i in range(SUBDIV):
				for j in range(SUBDIV):
					var ids = []
					for offset in [Vector2i(0,0),Vector2i(1,0),Vector2i(1,1),Vector2i(0,1)]:
						var key = cell*SUBDIV+face[0]+face[1]/SUBDIV*(i+offset.x)+face[2]/SUBDIV*(j+offset.y)
						if not lookup.has(key):
							lookup[key] = positions.size()
							positions.append(Vector3(key)/SUBDIV+Vector3(-.5,0,-.5))
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
	triangle_count = quads.size()*2
	for st in surfaces.values():
		st.index(); st.commit(mesh)
	return mesh
