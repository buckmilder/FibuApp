extends RefCounted
static func run(registry, check: Callable):
	var data=HabitatDocument.fresh();var generator=HabitatTerrain.new()
	data.terrain=[{"cell":[0,0,0],"asset":"terrain_meadow"}]
	var mesh=generator.build(data,registry)
	check.call(generator.grass_top_tiles==1 and generator.grass_rim_edges==4,"one grass tile has four exposed rim edges")
	check.call(mesh.get_aabb().end.y>1.03 and generator.collision_mesh.get_aabb().end.y<=1.00001,"raised grass is separate from solid support")
	check.call(mesh.get_aabb().size.x>1 and mesh.get_aabb().size.x<1.15,"grass overhang stays small")
	data.terrain.append({"cell":[1,0,0],"asset":"terrain_forest"});mesh=generator.build(data,registry)
	check.call(generator.grass_rim_edges==6,"mixed grass neighbors suppress shared rims")
	var seam_points=[]
	for surface in range(mesh.get_surface_count()):
		var arrays=mesh.surface_get_arrays(surface)
		for p in arrays[Mesh.ARRAY_VERTEX]:
			if is_equal_approx(p.x,.5) and is_equal_approx(p.z,0) and p.y>1:seam_points.append(p)
	check.call(seam_points.size()>=2,"both grass materials have a shared seam vertex")
	if seam_points.size()>=2:check.call(seam_points[0].is_equal_approx(seam_points[-1]),"mixed cap positions match exactly at shared seam")
	data.terrain[1].asset="terrain_cobble";mesh=generator.build(data,registry)
	var flush=true
	for surface in range(mesh.get_surface_count()):
		for p in mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
			if is_equal_approx(p.x,.5) and is_equal_approx(p.z,0) and p.y>.8:flush=flush and abs(p.y-1)<.0001
	check.call(flush and generator.grass_rim_edges==3,"grass tapers flush to adjacent paving without an overhang")
	data.terrain=[{"cell":[0,0,0],"asset":"terrain_meadow"},{"cell":[0,1,0],"asset":"terrain_meadow"}]
	generator.build(data,registry);check.call(generator.grass_top_tiles==1 and generator.grass_rim_edges==4,"buried grass blocks do not create hidden caps or rim bands")
	data.terrain=[]
	for x in range(3):
		for row in range(3):data.terrain.append({"cell":[x,0,row],"asset":"terrain_meadow"})
	mesh=generator.build(data,registry)
	check.call(generator.exposed_faces==30 and generator.grass_rim_edges==12,"three by three patch decorates only its perimeter")
	check.call(generator.triangle_count==1152,"three by three stays within a small repeated terrain budget")
	data.terrain=data.terrain.filter(func(t):return t.cell!=[1,0,1]);mesh=generator.build(data,registry)
	check.call(generator.grass_rim_edges==16,"hole boundaries receive their own exposed rim")
	data.terrain=[]
	for x in range(9):
		for row in range(9):data.terrain.append({"cell":[x,0,row],"asset":"terrain_meadow"})
	generator.build(data,registry);check.call(generator.triangle_count==6912 and generator.grass_rim_edges==36,"nine by nine has no per-tile interior rims")
	data.terrain=[{"cell":[0,-2,0],"asset":"terrain_meadow"},{"cell":[1,-1,0],"asset":"terrain_forest"},{"cell":[1,0,0],"asset":"terrain_lime"}]
	mesh=generator.build(data,registry)
	var valid=true
	for surface in range(mesh.get_surface_count()):
		var arrays=mesh.surface_get_arrays(surface)
		for p in arrays[Mesh.ARRAY_VERTEX]:valid=valid and p.is_finite()
		for n in arrays[Mesh.ARRAY_NORMAL]:valid=valid and n.is_finite() and abs(n.length()-1)<.001
	check.call(valid,"negative layers, steps and mixed grass have finite geometry and unit normals")
	for theme in ["golden","sand","limestone","cobble","timber","volcanic"]:
		data.terrain=[{"cell":[0,0,0],"asset":"terrain_"+theme}];generator.build(data,registry)
		check.call(generator.triangle_count==192 and generator.grass_rim_edges==0,theme+" keeps its existing solid appearance")
