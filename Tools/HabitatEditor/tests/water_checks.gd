extends RefCounted

static func cells(coords: Array) -> Dictionary:
	var data=HabitatDocument.fresh()
	for coord in coords: data.terrain.append({"cell":coord,"asset":HabitatWater.ID})
	return data

static func run(editor, registry, check: Callable):
	var water=HabitatWater.new()
	var data=cells([[0,0,0]])
	var node=water.build(data)
	check.call(water.report.faces==6 and water.report.top_faces==1 and water.report.foam_edges==4,"single water volume and perimeter")
	var count=water.rebuild_count; node.free(); node=water.build(data)
	check.call(water.rebuild_count==count,"unchanged water geometry cached")
	node.free()
	data=cells([[0,0,0],[1,0,0],[0,0,1],[1,0,1]])
	node=water.build(data)
	check.call(water.report.faces==16 and water.report.top_faces==4 and water.report.foam_edges==8,"2x2 water has no internal faces or foam grid")
	node.free()
	data=cells([[0,0,0],[0,1,0],[0,2,0]])
	node=water.build(data)
	check.call(water.report.faces==14 and water.report.top_faces==1 and water.report.foam_edges==4,"stack has one upper surface and continuous sides")
	var mesh=node.get_child(0).get_child(0).mesh; var depth_ok=true; var winding_ok=true
	for i in range(mesh.get_surface_count()):
		var arrays=mesh.surface_get_arrays(i)
		for uv in arrays[Mesh.ARRAY_TEX_UV2]:
			if not is_equal_approx(uv.x,3): depth_ok=false
		var p=arrays[Mesh.ARRAY_VERTEX]; var ids=arrays[Mesh.ARRAY_INDEX]; var n=arrays[Mesh.ARRAY_NORMAL]
		for j in range(0,ids.size(),3):
			if (p[ids[j+1]]-p[ids[j]]).cross(p[ids[j+2]]-p[ids[j]]).dot(n[ids[j]])>=0: winding_ok=false
	check.call(depth_ok,"depth tint uses contiguous column thickness")
	check.call(winding_ok,"water exterior winding consistent with normals")
	check.call(node.get_child(0).get_child(2).collision_layer==8,"water pick layer excludes solid physics")
	node.free()
	data=cells([[0,-100,0],[0,-99,0],[0,-98,0]])
	node=water.build(data); mesh=node.get_child(0).get_child(0).mesh
	depth_ok=true
	for i in range(mesh.get_surface_count()):
		for uv in mesh.surface_get_arrays(i)[Mesh.ARRAY_TEX_UV2]:
			if not is_equal_approx(uv.x,3): depth_ok=false
	check.call(depth_ok,"water depth independent of global Y")
	node.free()
	data=cells([[0,0,0],[1,0,0],[0,0,1]])
	node=water.build(data)
	check.call(water.report.faces==14 and water.report.foam_edges==8,"L shaped shoreline")
	node.free()
	data=cells([[0,0,0],[5,0,5]])
	node=water.build(data)
	check.call(water.report.bodies==2 and water.report.foam_edges==8,"separate water bodies")
	count=water.rebuild_count; node.free()
	data.terrain.append({"cell":[1,0,0],"asset":HabitatWater.ID})
	node=water.build(data)
	check.call(water.rebuild_count==count+1,"only changed water component regenerates")
	node.free()
	data=cells([[0,0,0]])
	data.terrain.append({"cell":[1,0,0],"asset":"terrain_cobble"}); data.terrain.append({"cell":[1,1,0],"asset":"terrain_cobble"})
	node=water.build(data)
	check.call(water.report.faces==5 and water.report.shore_edges==1 and water.report.wall_edges==1,"terrain boundary culling and wall foam")
	node.free()
	data.terrain.append({"cell":[0,1,0],"asset":"terrain_cobble"})
	node=water.build(data)
	check.call(water.report.top_faces==0 and water.report.foam_edges==0,"covered water has no false surface/foam")
	node.free()
	var terrain=HabitatTerrain.new().build(cells([[0,0,0]]),registry)
	check.call(terrain.get_surface_count()==0,"water not rendered as ordinary solid terrain")
	var doc=HabitatDocument.new(); doc.data=cells([[0,0,0]])
	check.call(doc.validate(doc.data,registry.assets).is_empty(),"water cells validate in layout")
	check.call(not doc.can_place(registry.assets.water_teal,Vector3.ZERO,0,Vector3.ONE).is_empty(),"water occupancy prevents overlap")
	check.call(doc.can_place(registry.assets.water_teal,Vector3(0,-1,0),0,Vector3.ONE).is_empty(),"water below ground allowed")
	check.call(not doc.can_place(registry.assets.water_teal,Vector3(-1,0,0),0,Vector3.ONE).is_empty(),"water respects horizontal bounds")
	doc.data.water_styles={"bad":{"opacity":2}}
	check.call(not doc.validate(doc.data,registry.assets).is_empty(),"invalid water opacity rejected")
	# Use actual editor commands and picking path.
	editor.new_document(); editor.active_asset=HabitatWater.ID; editor.set_tool("Place"); editor.make_ghost()
	editor.document.data.terrain=[{"cell":[3,0,3],"asset":"terrain_limestone"}]
	editor.ghost_cell=[3,1,3]; editor.ghost_position=Vector3(3,1,-3); editor.ghost_valid=true; editor.painted.clear()
	var before=editor.document.data.duplicate(true); editor.place_at_cursor(); editor.commit(before)
	check.call(editor.water_renderer.report.cells==1,"editor places water volume")
	editor.undo(); check.call(editor.document.data.terrain.size()==1,"water placement undo")
	editor.redo(); check.call(editor.water_renderer.report.cells==1,"water placement redo")
	editor.selected=["t:3,1,3"]; editor.duplicate_selection()
	check.call(editor.water_renderer.report.cells==2 and editor.water_renderer.report.foam_edges==6,"water duplicate connects")
	editor.move_selection(Vector3.UP)
	check.call(editor.document.terrain_map().has("4,2,3"),"move water vertically")
	var first=editor.document.terrain_map()["3,1,3"]
	editor.edit_water(first,"opacity",.5)
	check.call(is_equal_approx(HabitatWater.style_for(editor.document.data,[first]).opacity,.5),"water body inspector edits saved appearance")
	check.call(is_equal_approx(HabitatWater.style_for(editor.document.data,[editor.document.terrain_map()["4,2,3"]]).opacity,HabitatWater.defaults().opacity),"disconnected body retains independent appearance")
	editor.choose_sky(HabitatAtmosphere.preset("starry_night"))
	check.call(editor.water_renderer.lighting_energy<1,"water foam follows night lighting")
	editor.choose_sky(HabitatAtmosphere.preset("sunny_highlands"))
	check.call(editor.water_renderer.lighting_energy==1,"water foam follows daylight")
	check.call(editor.document.save_file("user://water-roundtrip.json",registry.assets),"water saves")
	var restored=HabitatDocument.new()
	check.call(restored.load_file("user://water-roundtrip.json",registry.assets) and restored.data==JSON.parse_string(JSON.stringify(editor.document.data)),"water cells and styles roundtrip")
	editor.selected=["t:4,2,3"]; editor.delete_selection()
	check.call(editor.water_renderer.report.cells==1 and editor.water_renderer.report.foam_edges==4,"deletion rebuilds exposed water boundary")
	editor.water_visible=false; editor.rebuild()
	check.call(editor.water_root==null,"water visibility toggle removes rendering/picking, retains cells")
	editor.water_visible=true; editor.rebuild()
	editor.target=Vector3(3,1,-3); editor.yaw=.65; editor.pitch=.65; editor.distance=7; editor.update_camera()
	await editor.get_tree().process_frame
	await editor.get_tree().physics_frame
	var point=editor.camera.unproject_position(Vector3(3,2,-3))
	check.call(editor.pick(point)=="t:3,1,3","transparent water selectable")
	editor.water_visible=false; editor.rebuild()
	await editor.get_tree().process_frame
	await editor.get_tree().physics_frame
	point=editor.camera.unproject_position(Vector3(3,1,-3))
	check.call(editor.pick(point)=="t:3,0,3","hidden water allows underwater terrain selection")
	editor.toggle_preview()
	check.call(editor.water_root!=null and editor.proxy.collision_mask==1,"preview renders water without making it solid")
	editor.toggle_preview(); editor.water_visible=true
