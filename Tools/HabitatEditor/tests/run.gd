extends SceneTree
var failures = 0
var checks = 0
var registry: HabitatRegistry

func check(condition: bool, message: String):
	checks+=1
	if not condition:
		failures+=1; push_error("FAIL: "+message)

func _initialize():
	call_deferred("run")

func run():
	registry=HabitatRegistry.new()
	var doc=HabitatDocument.new()
	check(registry.assets.size()==23,"all nine terrain and fourteen props registered")
	for asset in registry.assets.values():
		if asset.kind=="prop": check(registry.scenes[asset.id]!=null,"GLB loads: "+asset.id)
	check(doc.validate(doc.data,registry.assets).is_empty(),"fresh document valid")
	doc.data.terrain=[{"cell":[0,-30,0],"asset":"terrain_meadow"},{"cell":[8,1000,8],"asset":"terrain_forest"}]
	check(doc.validate(doc.data,registry.assets).is_empty(),"deep and tall cells accepted")
	var bad=doc.data.duplicate(true); bad.terrain[0].cell[0]=-1
	check(not doc.validate(bad,registry.assets).is_empty(),"negative horizontal cell rejected")
	bad=doc.data.duplicate(true); bad.terrain[0].cell[2]=9
	check(not doc.validate(bad,registry.assets).is_empty(),"outside row rejected")
	bad=doc.data.duplicate(true); bad.terrain.append(bad.terrain[0].duplicate(true))
	check(not doc.validate(bad,registry.assets).is_empty(),"duplicate cells rejected")
	bad=doc.data.duplicate(true); bad.version=99
	check(not doc.validate(bad,registry.assets).is_empty(),"future version rejected")
	bad=doc.data.duplicate(true); bad.spawn=[INF,0,0]
	check(not doc.validate(bad,registry.assets).is_empty(),"non-finite transform rejected")
	bad=doc.data.duplicate(true); bad.grid.cell_size=2
	check(not doc.validate(bad,registry.assets).is_empty(),"unimplemented scale conversion explicit")
	doc.data.custom_future={"preserve":[1,2,3]}
	doc.data.objects=[{"id":"unknown-instance","asset":"not-installed","position":[1,-5,1],"rotation":[0,0,0],"scale":[1,1,1],"future_object_field":{"x":true}}]
	check(doc.save_file("user://roundtrip.json",registry.assets),"atomic save")
	var original=JSON.parse_string(JSON.stringify(doc.data))
	check(doc.load_file("user://roundtrip.json",registry.assets),"reload")
	check(doc.data==original,"roundtrip retains all fields")
	check(doc.missing_assets(registry.assets)==["not-installed"],"missing ID retained")
	var f=FileAccess.open("user://bad.json",FileAccess.WRITE); f.store_string("{"); f.close()
	check(not doc.load_file("user://bad.json",registry.assets),"malformed file rejected")
	check(doc.data==original,"failed load preserves document")
	doc.data=HabitatDocument.fresh()
	var cube=registry.assets.terrain_meadow
	check(doc.can_place(cube,Vector3.ZERO,0,Vector3.ONE).is_empty(),"first cell fits")
	check(not doc.can_place(cube,Vector3(-1,0,0),0,Vector3.ONE).is_empty(),"left boundary")
	check(not doc.can_place(cube,Vector3(9,0,0),0,Vector3.ONE).is_empty(),"right boundary")
	check(not doc.can_place(cube,Vector3(8,0,0),0,Vector3(2,1,1)).is_empty(),"multicell boundary")
	var multicell=cube.duplicate(true); multicell.rotations=[0,90,180,270]
	check(doc.can_place(multicell,Vector3(8,0,-1),90,Vector3(2,1,1)).is_empty(),"rotated multicell footprint")
	check(not doc.can_place(cube,Vector3.ZERO,90,Vector3.ONE).is_empty(),"asset rotation restrictions")
	doc.data.terrain=[{"cell":[0,0,0],"asset":"terrain_meadow"}]
	check(not doc.can_place(cube,Vector3.ZERO,0,Vector3.ONE).is_empty(),"occupied terrain rejected")
	check(doc.can_place(cube,Vector3(0,1,0),0,Vector3.ONE).is_empty(),"vertical stacking")
	check(doc.can_place(cube,Vector3(0,-1,0),0,Vector3.ONE).is_empty(),"negative layer")
	check(doc.can_place(registry.assets.foliage_round_tree,Vector3.ZERO,0,Vector3.ONE).is_empty(),"decorative overlap allowed")
	var terrain=HabitatTerrain.new(); var mesh=terrain.build(doc.data,registry)
	check(terrain.exposed_faces==6,"single voxel six faces")
	check(terrain.triangle_count==192,"single voxel subdivision count")
	check(mesh.get_surface_count()==2,"top and side materials")
	var bounds=mesh.get_aabb()
	check(bounds.position.is_equal_approx(Vector3(-.5,0,-.5)),"face centers retain cell extent")
	doc.data.terrain.append({"cell":[1,0,0],"asset":"terrain_forest"})
	mesh=terrain.build(doc.data,registry)
	check(terrain.exposed_faces==10,"mixed material internal faces removed")
	check(terrain.triangle_count==320,"no hidden triangles")
	for surface in range(mesh.get_surface_count()):
		var arrays=mesh.surface_get_arrays(surface)
		for normal in arrays[Mesh.ARRAY_NORMAL]:
			if not is_equal_approx(normal.length(),1): check(false,"unit normal"); break
		for vertex in arrays[Mesh.ARRAY_VERTEX]:
			if not vertex.is_finite(): check(false,"finite vertex"); break
	doc.data.terrain=[{"cell":[0,0,0],"asset":"terrain_meadow"},{"cell":[0,1,0],"asset":"terrain_meadow"}]
	terrain.build(doc.data,registry)
	check(terrain.exposed_faces==10,"vertical internal faces removed")
	var sample=ProjectSettings.globalize_path("res://../../Assets/Habitats/terrace-starter.json")
	check(doc.load_file(sample,registry.assets),"starter layout validates")
	# Exercise the actual scene commands and input callbacks, not a mock implementation.
	var editor=load("res://HabitatEditor.tscn").instantiate()
	root.add_child(editor)
	await process_frame
	editor.new_document()
	var empty=JSON.stringify(editor.document.data)
	editor.ghost_cell=[2,0,2]; editor.ghost_position=Vector3(2,0,-2); editor.ghost_valid=true
	var before=editor.document.data.duplicate(true); editor.painted.clear(); editor.place_at_cursor(); editor.commit(before)
	check(editor.document.data.terrain.size()==1,"editor places cell")
	editor.undo(); check(editor.document.data.terrain.is_empty(),"editor undo")
	editor.redo(); check(editor.document.data.terrain.size()==1,"editor redo")
	editor.selected=["t:2,0,2"]; editor.set_tool("Move")
	check(editor.selected==["t:2,0,2"],"Move tool retains selection")
	editor.move_selection(Vector3.UP)
	check(editor.document.data.terrain[0].cell==[2,1,2],"move snapped terrain")
	editor.duplicate_selection(); check(editor.document.data.terrain.size()==2,"duplicate terrain")
	editor.delete_selection(); check(editor.document.data.terrain.size()==1,"delete selection")
	editor.load_path(sample)
	await physics_frame
	var saved=JSON.stringify(editor.document.data); var camera_target=editor.target
	editor.toggle_preview()
	await physics_frame
	check(editor.previewing and editor.proxy!=null,"preview enters")
	editor.toggle_preview()
	check(JSON.stringify(editor.document.data)==saved,"preview preserves authored layout")
	check(editor.target==camera_target,"preview restores camera")
	# Four quarter-meter steps should be traversable without jumping.
	editor.toggle_preview(); editor.set_physics_process(false)
	editor.yaw=0; editor.pitch=.6; editor.update_camera()
	editor.proxy.position=Vector3(4,1.03,-4)
	for frame in range(85):
		await physics_frame
		editor.preview_step(1.0/60,Vector3(0,0,-1),false)
	check(editor.proxy.position.z < -5.6 and editor.proxy.position.y>1.8,"proxy climbs stair asset")
	editor.toggle_preview()
	var tab=InputEventKey.new(); tab.keycode=KEY_TAB; tab.pressed=true
	editor._input(tab)
	check(editor.previewing and editor.get_viewport().is_input_handled(),"Tab preview consumes default GUI focus traversal")
	check(editor.get_viewport().gui_get_focus_owner()==editor.view,"preview keyboard focus stays in viewport")
	editor.toggle_preview()
	# Surface ray hit confirms collision winding and negative-Z convention.
	await physics_frame
	var hit=editor.viewport.find_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(4,5,-2),Vector3(4,-2,-2),1))
	check(not hit.is_empty(),"terrain ray picks upward face")
	if not hit.is_empty(): check(hit.normal.y>.9 and abs(hit.position.y-1)<.01,"terrain surface is Y=1")
	# Brush plane stays fixed while painting; moving over the newly placed cell must not stack it.
	editor.new_document(); editor.set_physics_process(true)
	editor.document.data.terrain=[{"cell":[2,0,2],"asset":"terrain_meadow"}]; editor.set_tool("Place"); editor.rebuild()
	await process_frame
	await physics_frame
	var point=editor.camera.unproject_position(Vector3(2,1,-2))
	var press=InputEventMouseButton.new(); press.button_index=MOUSE_BUTTON_LEFT; press.pressed=true; press.position=point
	editor.view_input(press)
	await process_frame
	await physics_frame
	var motion=InputEventMouseMotion.new(); motion.position=point; motion.relative=Vector2(1,0)
	editor.view_input(motion)
	editor.end_pointer(point)
	check(editor.document.data.terrain.size()==2,"brush does not accidentally stack during same stroke")
	check(editor.document.data.terrain[1].cell==[2,1,2],"face placement snaps above ground")
	editor.undo(); check(editor.document.data.terrain.size()==1,"one undo removes whole brush stroke")
	await process_frame
	await physics_frame
	var routed=InputEventMouseButton.new(); routed.button_index=MOUSE_BUTTON_LEFT; routed.pressed=true; routed.position=point+editor.view.global_position
	editor._input(routed)
	routed.pressed=false; editor._input(routed)
	check(editor.document.data.terrain.size()==2,"window pointer routes to viewport placement")
	# Every face winding must match its assigned outward normal.
	var lone=HabitatDocument.fresh(); lone.terrain=[{"cell":[0,0,0],"asset":"terrain_meadow"}]
	var lone_mesh=HabitatTerrain.new().build(lone,registry)
	var winding_ok=true
	for surface in range(lone_mesh.get_surface_count()):
		var arrays=lone_mesh.surface_get_arrays(surface); var verts=arrays[Mesh.ARRAY_VERTEX]; var inds=arrays[Mesh.ARRAY_INDEX]; var norms=arrays[Mesh.ARRAY_NORMAL]
		for i in range(0,inds.size(),3):
			var cross=(verts[inds[i+1]]-verts[inds[i]]).cross(verts[inds[i+2]]-verts[inds[i]])
			if cross.dot(norms[inds[i]])>=0: winding_ok=false
	check(winding_ok,"all six exterior faces clockwise with outward normals")
	editor.queue_free()
	await process_frame
	print("Fibu editor: %d checks, %d failures" % [checks,failures])
	quit(1 if failures else 0)
