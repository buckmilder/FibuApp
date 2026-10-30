extends SceneTree
func _initialize(): call_deferred("export_assets")
func arrays(mesh: ArrayMesh, registry: HabitatRegistry) -> Array:
	var result=[]
	for surface in range(mesh.get_surface_count()):
		var a=mesh.surface_get_arrays(surface); var mat=mesh.surface_get_material(surface); var file=mat.albedo_texture.resource_path.get_file()
		var points=[]; var normals=[]; var uv=[]
		for p in a[Mesh.ARRAY_VERTEX]: points.append([p.x,p.y,p.z])
		for p in a[Mesh.ARRAY_NORMAL]: normals.append([p.x,p.y,p.z])
		for p in a[Mesh.ARRAY_TEX_UV]: uv.append([p.x,p.y])
		result.append({"texture":file,"points":points,"normals":normals,"uv":uv,"indices":Array(a[Mesh.ARRAY_INDEX])})
	return result
func export_assets():
	var registry=HabitatRegistry.new();var out=ProjectSettings.globalize_path("res://../../Assets/Blender/SoftTerrain/generated")
	DirAccess.make_dir_recursive_absolute(out)
	var studies=[]
	for asset in registry.assets.values():
		if asset.kind=="terrain":studies.append([asset.theme+"_single",[{"cell":[0,0,0],"asset":asset.id}]])
	var patch=[]
	for x in range(3):
		for row in range(3):patch.append({"cell":[x,0,row],"asset":"terrain_meadow"})
	studies.append(["meadow_patch",patch.duplicate(true)])
	for x in [1,2]:
		for row in [1,2]:patch.append({"cell":[x,1,row],"asset":"terrain_meadow"})
	patch.append({"cell":[2,2,2],"asset":"terrain_meadow"});studies.append(["meadow_terrace",patch])
	var outputs=[]
	for study in studies:
		var terrain=HabitatTerrain.new();var data=HabitatDocument.fresh();data.terrain=study[1]
		var mesh=terrain.build(data,registry)
		var record={"id":study[0],"cells":study[1],"surfaces":arrays(mesh,registry),"collision":arrays(terrain.collision_mesh,registry),"triangles":terrain.triangle_count,"exposedSolidFaces":terrain.exposed_faces,"grassTopTiles":terrain.grass_top_tiles,"grassRimEdges":terrain.grass_rim_edges}
		FileAccess.open(out+"/"+study[0]+".json",FileAccess.WRITE).store_string(JSON.stringify(record))
		outputs.append({"id":study[0],"triangles":terrain.triangle_count,"exposedSolidFaces":terrain.exposed_faces,"grassRimEdges":terrain.grass_rim_edges})
	FileAccess.open(out+"/study-manifest.json",FileAccess.WRITE).store_string(JSON.stringify(outputs,"  "))
	print("Exported ",studies.size()," actual builder meshes");quit()
