extends RefCounted

static func object(id: String, asset: Dictionary, position: Array, yaw: float = 0) -> Dictionary:
	return {"id":id,"asset":asset.id,"position":position,"rotation":[0,yaw,0],"scale":[1,1,1],"solid":asset.solid,"dimensions":asset.dimensions.duplicate()}

static func run(editor, registry, check: Callable):
	var tree=registry.assets.foliage_round_tree; var bush=registry.assets.foliage_shrub; var bench=registry.assets.bench
	check.call(int(tree.footprint[0])==1 and int(tree.footprint[1])==1 and tree.blocks_movement,"tree occupies and blocks one tile")
	check.call(int(bush.footprint[0])==1 and int(bush.footprint[1])==1 and not bush.blocks_movement,"bush occupies one tile but remains traversable")
	check.call(int(bench.footprint[0])==2 and int(bench.footprint[1])==1 and bench.blocks_movement,"bench reserves two tiles")
	var center=HabitatDocument.snap_prop(bench,Vector3(4.1,1,-3.1),0)
	check.call(center==Vector3(4.5,1,-3),"two-wide bench snaps between X cell centers")
	var turned=HabitatDocument.snap_prop(bench,Vector3(4.1,1,-3.1),90)
	check.call(turned==Vector3(4,1,-3.5),"rotated bench snaps between row centers")
	var doc=HabitatDocument.new()
	check.call(not doc.can_place(bench,Vector3(8.5,1,-3),0,Vector3.ONE).is_empty(),"bench footprint cannot extend beyond boundary")
	doc.data.objects=[object("tree",tree,[2,1,-2]),object("bush",bush,[3,1,-2]),object("bench",bench,[4.5,1,-4])]
	check.call(doc.blocked_cells().has([2,1,2]) and not doc.blocked_cells().has([3,1,2]),"navigation blocks tree but not bush")
	check.call(doc.blocked_cells().has([4,1,4]) and doc.blocked_cells().has([5,1,4]),"bench blocks both occupied tiles")
	check.call(not doc.can_place(bush,Vector3(2,1,-2),0,Vector3.ONE).is_empty(),"passable prop cannot overlap reserved tree footprint")
	check.call(doc.can_place(tree,Vector3(1,1,-2),0,Vector3.ONE).is_empty(),"adjacent tree canopies may overhang without occupying extra tiles")
	doc.data.objects[2].rotation[1]=90; doc.data.objects[2].position=[4,1,-4.5]
	check.call(doc.blocked_cells().has([4,1,4]) and doc.blocked_cells().has([4,1,5]),"rotated bench blocks correct rows")
	editor.document.data=doc.data; editor.selected=[]; editor.rebuild()
	await editor.get_tree().physics_frame
	await editor.get_tree().physics_frame
	var space=editor.viewport.find_world_3d().direct_space_state
	var tree_hit=space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(.8,1.4,-2),Vector3(2.2,1.4,-2),1))
	var bush_hit=space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(2.6,1.4,-2),Vector3(3.4,1.4,-2),1))
	check.call(not tree_hit.is_empty(),"actual preview physics blocks tree")
	check.call(bush_hit.is_empty(),"actual preview physics passes through bush")
	editor.set_tool("Select"); editor.selected=["bench"]; editor.rotate_selection()
	var rotated=editor.find_object("bench")
	check.call(rotated.rotation[1]==180 and fposmod(rotated.position[0],1)==.5 and is_zero_approx(fposmod(rotated.position[2],1)),"editor rotation keeps bench on whole tiles")
	editor.undo(); check.call(editor.find_object("bench").rotation[1]==90,"tile rotation is undoable")

	var legacy=editor.find_object("bench"); legacy.position=[4.2,1.2,-4.2]; legacy.rotation=[0,13,0]; legacy.scale=[.7,.7,.7]
	var saved=JSON.stringify(editor.document.data)
	editor.selected=["bench"]; editor.align_props()
	check.call(editor.find_object("bench").position==[4.5,1.0,-4.0] and editor.find_object("bench").scale==[1,1,1],"explicit alignment normalizes legacy prop")
	editor.undo(); check.call(JSON.stringify(editor.document.data)==saved,"alignment undo preserves legacy data exactly")
	editor.find_object("bush").position=[2.1,1,-2.1]; editor.selected=["bush"]; saved=JSON.stringify(editor.document.data)
	editor.align_props(); check.call(JSON.stringify(editor.document.data)==saved,"conflicting alignment preserves original habitat")

	editor.document.data=HabitatDocument.fresh()
	editor.document.data.objects=[object("a",tree,[5,1,-4]),object("b",bench,[4.5,1,-4])]
	editor.selected=["a","b"]; saved=JSON.stringify(editor.document.data); editor.rotate_selection()
	check.call(JSON.stringify(editor.document.data)==saved,"group rotation cannot overlap its own selected footprints")
	var sample=ProjectSettings.globalize_path("res://../../Assets/Habitats/tile-footprints-study.json")
	check.call(doc.load_file(sample,registry.assets),"footprint study layout loads")
