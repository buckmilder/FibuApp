extends Control

var registry = HabitatRegistry.new()
var document = HabitatDocument.new()
var undo_stack: Array = []
var redo_stack: Array = []
var selected: Array = []
var favorites: Array = ["terrain_meadow","foliage_round_tree","stairs","water_teal"]
var file_path = ""
var saved_signature = ""
var tool = "Place"
var tool_buttons = {}
var active_asset = "terrain_meadow"
var rotation_y = 0.0
var fine_snap = true
var layer = 0
var cutaway = false
var show_grid = true
var previewing = false
var drag_start = Vector2.ZERO
var selecting_box = false
var painting = false
var stroke_before: Dictionary = {}
var painted = {}
var stroke_plane = null
var ghost_position = Vector3.ZERO
var ghost_valid = false
var ghost_reason = ""
var ghost_cell = [0,0,0]
var ghost: Node3D
var target = Vector3(4,0,-4)
var yaw = .65
var pitch = .65
var distance = 17.0
var camera_drag = 0
var orbit_drag_distance = 0.0
var free_fly = false
var saved_camera: Array = []
var ui_lock = false
var inspect_fields = {}
var object_nodes = {}
var proxy: CharacterBody3D
var proxy_velocity = Vector3.ZERO
var viewport: SubViewport
var view: SubViewportContainer
var world: Node3D
var terrain_root: Node3D
var water_root: Node3D
var water_renderer=HabitatWater.new()
var water_visible=true
var props_root: Node3D
var outlines: Node3D
var grid_root: Node3D
var camera: Camera3D
var palette: VBoxContainer
var favorite_bar: VBoxContainer
var inspector: VBoxContainer
var status: Label
var title_label: Label
var search: LineEdit
var category: OptionButton
var layer_control: SpinBox
var file_dialog: FileDialog
var confirm: ConfirmationDialog
var error_dialog: AcceptDialog
var pending_action: Callable
var preview_button: Button
var overlay: Control
var box_rect = Rect2()
var recent_hover = Vector2.ZERO
var selection_list: OptionButton
var spawn_marker: Node3D
var content_root_override = ""
var atmosphere: HabitatAtmosphere
var sky_window: Window
var sky_fields: VBoxContainer
var sky_preset_list: OptionButton
var sky_preset_paths: Array = []
var sky_revert = {}
var sky_name: LineEdit
var panorama_dialog: FileDialog

func _ready():
	get_tree().auto_accept_quit = false
	load_preferences()
	build_ui()
	build_world()
	saved_signature = signature()
	rebuild()
	set_status("Choose a block, then click or drag to build. R rotates • Esc selects • H shows controls")
	if not "--blank" in OS.get_cmdline_user_args() and FileAccess.file_exists(content_directory()+"/terrace-starter.json"):
		load_path(content_directory()+"/terrace-starter.json")

func signature() -> String:
	return JSON.stringify(document.data)

func dirty() -> bool:
	return signature() != saved_signature

func button(text: String, action: Callable, parent: Node) -> Button:
	var b = Button.new(); b.text = text; b.pressed.connect(action); parent.add_child(b)
	b.focus_mode = Control.FOCUS_NONE
	return b

func section(text: String, parent: Node):
	var l = Label.new(); l.text = text; l.add_theme_color_override("font_color",Color("e9c76b")); parent.add_child(l)

func build_ui():
	var theme_resource = Theme.new()
	theme_resource.default_font_size = 15
	var panel_style = StyleBoxFlat.new()
	panel_style.bg_color = Color("263b3e")
	panel_style.set_content_margin_all(10)
	theme_resource.set_stylebox("panel","PanelContainer",panel_style)
	var normal = StyleBoxFlat.new(); normal.bg_color = Color("395052"); normal.set_corner_radius_all(7); normal.set_content_margin_all(8)
	var hover_style = normal.duplicate(); hover_style.bg_color = Color("526b65")
	theme_resource.set_stylebox("normal","Button",normal)
	theme_resource.set_stylebox("hover","Button",hover_style)
	var pressed = normal.duplicate(); pressed.bg_color = Color("8a6c30")
	theme_resource.set_stylebox("pressed","Button",pressed)
	theme = theme_resource
	var background = ColorRect.new(); background.color = Color("172b30"); background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(background)
	var layout = VBoxContainer.new(); layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(layout)
	var top = HFlowContainer.new(); layout.add_child(top)
	button("New",func(): guard_action(new_document),top)
	button("Open…",func(): guard_action(func(): open_dialog(FileDialog.FILE_MODE_OPEN_FILE)),top)
	button("Save",save,top)
	button("Save As…",func(): open_dialog(FileDialog.FILE_MODE_SAVE_FILE),top)
	button("Duplicate Habitat",duplicate_document,top)
	button("Undo",undo,top); button("Redo",redo,top)
	for name in ["Select","Place","Erase","Move"]:
		var b=button(name,func(): set_tool(name),top); b.toggle_mode=true; b.button_pressed=(name==tool); tool_buttons[name]=b
	button("Rotate ↻",rotate_selection,top)
	button("Duplicate",duplicate_selection,top); button("Delete",delete_selection,top)
	preview_button = button("Preview ▶",toggle_preview,top)
	button("Sky & Atmosphere",open_sky,top)
	button("Help",show_help,top)
	var row = HBoxContainer.new(); layout.add_child(row)
	title_label = Label.new(); title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL; row.add_child(title_label)
	var name_edit = LineEdit.new(); name_edit.placeholder_text = "Habitat name (Enter to apply)"; name_edit.custom_minimum_size.x = 230; row.add_child(name_edit)
	name_edit.text_submitted.connect(func(value):
		if previewing: return
		var before = document.data.duplicate(true); document.data.name = value; commit(before); name_edit.clear(); name_edit.release_focus())
	button("Set spawn at cursor",set_spawn,row)
	var middle = HBoxContainer.new(); middle.size_flags_vertical = Control.SIZE_EXPAND_FILL; layout.add_child(middle)
	var favorites_panel = PanelContainer.new(); middle.add_child(favorites_panel)
	favorite_bar = VBoxContainer.new(); favorite_bar.custom_minimum_size.x = 80; favorites_panel.add_child(favorite_bar)
	var central = VBoxContainer.new(); central.size_flags_horizontal = Control.SIZE_EXPAND_FILL; middle.add_child(central)
	var controls = HFlowContainer.new(); central.add_child(controls)
	button("Grid",func(): show_grid = not show_grid; grid_root.visible = show_grid and not previewing,controls)
	button("Show/Hide water",func(): water_visible=not water_visible; rebuild(); set_status("Water visible" if water_visible else "Water hidden for editing underneath; cells remain saved."),controls)
	button("Fine snap",func(): fine_snap = not fine_snap; set_status("Prop snapping: " + ("0.25m" if fine_snap else "free")),controls)
	var layer_label = Label.new(); layer_label.text = "Build layer"; controls.add_child(layer_label)
	layer_control = SpinBox.new(); layer_control.min_value = -100; layer_control.max_value = 100; layer_control.allow_greater = true; layer_control.allow_lesser = true; layer_control.step = 1; controls.add_child(layer_control)
	layer_control.value_changed.connect(func(v): layer = int(v); rebuild_grid(); if cutaway: rebuild())
	button("Cutaway",func(): cutaway = not cutaway; rebuild(); set_status("Cutaway hides geometry above build layer + 1; hidden objects cannot be picked." if cutaway else "All layers visible."),controls)
	button("Top",func(): pitch = 1.55; update_camera(),controls)
	button("Isometric",func(): pitch = .65; yaw = .65; update_camera(),controls)
	button("Frame",frame_all,controls); button("Focus",focus_selection,controls)
	button("Reset",func(): target=Vector3(4,0,-4); yaw=.65; pitch=.65; distance=17; update_camera(),controls)
	button("Fly",func(): free_fly = not free_fly; set_status("WASD always moves the camera. Fly toggles view-relative movement; Q/E moves vertically."),controls)
	view = SubViewportContainer.new(); view.size_flags_vertical = Control.SIZE_EXPAND_FILL; view.size_flags_horizontal = Control.SIZE_EXPAND_FILL; view.stretch = true; view.focus_mode=Control.FOCUS_ALL; central.add_child(view)
	viewport = SubViewport.new(); viewport.size = Vector2i(900,700); viewport.handle_input_locally = false; viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS; viewport.own_world_3d = true; view.add_child(viewport)

	overlay = Control.new(); overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE; overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); view.add_child(overlay)
	overlay.draw.connect(func():
		if selecting_box: overlay.draw_rect(box_rect,Color(1,.8,.3,.18),true); overlay.draw_rect(box_rect,Color(1,.85,.4),false,2))
	var right = PanelContainer.new(); right.custom_minimum_size.x = 285; middle.add_child(right)
	var right_layout = VBoxContainer.new(); right.add_child(right_layout)
	section("ASSETS",right_layout)
	search = LineEdit.new(); search.placeholder_text = "Search blocks and props…"; right_layout.add_child(search); search.text_changed.connect(func(_s): refresh_palette())
	category = OptionButton.new(); category.add_item("All"); right_layout.add_child(category)
	var categories = []
	for asset in registry.assets.values():
		if not categories.has(asset.category): categories.append(asset.category)
	for cat in categories: category.add_item(cat)
	category.select(categories.find("Terrain")+1)
	category.item_selected.connect(func(_i): refresh_palette())
	var scroll = ScrollContainer.new(); scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL; right_layout.add_child(scroll)
	palette = VBoxContainer.new(); palette.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(palette)
	section("SELECTION",right_layout)
	selection_list = OptionButton.new(); right_layout.add_child(selection_list)
	selection_list.item_selected.connect(func(index):
		if index > 0 and not previewing: selected=[selection_list.get_item_metadata(index)]; refresh_selection())
	var inspector_scroll = ScrollContainer.new(); inspector_scroll.custom_minimum_size.y = 240; right_layout.add_child(inspector_scroll)
	inspector = VBoxContainer.new(); inspector.size_flags_horizontal = Control.SIZE_EXPAND_FILL; inspector_scroll.add_child(inspector)
	status = Label.new(); status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; status.custom_minimum_size.y = 42; layout.add_child(status)
	file_dialog = FileDialog.new(); file_dialog.access = FileDialog.ACCESS_FILESYSTEM; file_dialog.filters = PackedStringArray(["*.json ; Fibu habitat"]); file_dialog.size = Vector2i(900,600); add_child(file_dialog)
	file_dialog.file_selected.connect(func(path):
		if file_dialog.file_mode == FileDialog.FILE_MODE_OPEN_FILE: load_path(path)
		else: save_path(path))
	confirm = ConfirmationDialog.new(); confirm.title = "Unsaved habitat"; confirm.dialog_text = "Discard unsaved changes? Use Cancel and Save to keep them."; confirm.ok_button_text = "Discard"; add_child(confirm)
	confirm.confirmed.connect(func(): pending_action.call())
	error_dialog = AcceptDialog.new(); add_child(error_dialog)
	refresh_palette(); refresh_favorites()

func clear_children(node: Node):
	for child in node.get_children(): node.remove_child(child); child.queue_free()

func refresh_palette():
	clear_children(palette)
	for asset in registry.assets.values():
		if not search.text.is_empty() and not search.text.to_lower() in (asset.name+" "+asset.category+" "+asset.id).to_lower(): continue
		if category.selected > 0 and asset.category != category.get_item_text(category.selected): continue
		var row = HBoxContainer.new(); palette.add_child(row)
		var b = button(asset.name,func(): active_asset=asset.id; rotation_y=0; set_tool("Place"); refresh_palette(); make_ghost(),row)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL; b.alignment = HORIZONTAL_ALIGNMENT_LEFT; b.custom_minimum_size.y = 56
		var thumb = "res://assets/thumbnails/"+asset.id+".png"
		if ResourceLoader.exists(thumb): b.icon = load(thumb); b.expand_icon = true; b.add_theme_constant_override("icon_max_width",50)
		b.modulate = Color("ffdb83") if asset.id == active_asset else Color.WHITE
		button("★" if favorites.has(asset.id) else "☆",func():
			if favorites.has(asset.id): favorites.erase(asset.id)
			else: favorites.append(asset.id)
			save_preferences(); refresh_palette(); refresh_favorites(),row)

func refresh_favorites():
	clear_children(favorite_bar); section("FAVS",favorite_bar)
	for id in favorites:
		if not registry.assets.has(id): continue
		var b = button(registry.assets[id].name.replace(" ","\n"),func(): active_asset=id; set_tool("Place"); refresh_palette(); make_ghost(),favorite_bar)
		b.custom_minimum_size.y = 55

func load_preferences():
	var config = ConfigFile.new()
	if config.load("user://editor.cfg") == OK: favorites = config.get_value("palette","favorites",[])

func save_preferences():
	var config = ConfigFile.new(); config.set_value("palette","favorites",favorites); config.save("user://editor.cfg")

func build_world():
	world = Node3D.new(); viewport.add_child(world)
	atmosphere=HabitatAtmosphere.new(world,content_directory())
	atmosphere.settings_changed.connect(water_renderer.set_lighting)
	terrain_root = Node3D.new(); world.add_child(terrain_root)
	props_root = Node3D.new(); world.add_child(props_root)
	outlines = Node3D.new(); world.add_child(outlines)
	grid_root = Node3D.new(); world.add_child(grid_root)
	camera = Camera3D.new(); camera.fov=45; camera.far = 10000; camera.near = .05; camera.current = true; world.add_child(camera); update_camera()
	make_ghost()

func update_camera():
	if not camera: return
	camera.position = target + Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))*distance
	camera.look_at(target,Vector3.UP)

func wire_box(bounds: AABB, color: Color, parent: Node3D):
	var vertices = []
	for i in range(8): vertices.append(bounds.position + Vector3(bounds.size.x if i&1 else 0,bounds.size.y if i&2 else 0,bounds.size.z if i&4 else 0))
	var mesh = ImmediateMesh.new(); var mat = StandardMaterial3D.new(); mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mat.albedo_color = color; mat.no_depth_test = true
	mesh.surface_begin(Mesh.PRIMITIVE_LINES,mat)
	for edge in [[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]]:
		mesh.surface_add_vertex(vertices[edge[0]]); mesh.surface_add_vertex(vertices[edge[1]])
	mesh.surface_end()
	var instance = MeshInstance3D.new(); instance.mesh = mesh; parent.add_child(instance)

func rebuild_grid():
	clear_children(grid_root)
	var w = document.data.grid.width; var d = document.data.grid.depth
	var mesh = ImmediateMesh.new(); var mat = StandardMaterial3D.new(); mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mat.albedo_color = Color(.85,.94,.91,.5); mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mesh.surface_begin(Mesh.PRIMITIVE_LINES,mat)
	for x in range(w+1): mesh.surface_add_vertex(Vector3(x-.5,layer+.012,.5)); mesh.surface_add_vertex(Vector3(x-.5,layer+.012,-d+.5))
	for z in range(d+1): mesh.surface_add_vertex(Vector3(-.5,layer+.012,-z+.5)); mesh.surface_add_vertex(Vector3(w-.5,layer+.012,-z+.5))
	mesh.surface_end()
	var instance = MeshInstance3D.new(); instance.mesh = mesh; grid_root.add_child(instance)
	wire_box(AABB(Vector3(-.5,layer+.02,-d+.5),Vector3(w,.015,d)),Color("f7cc72"),grid_root)
	grid_root.visible = show_grid and not previewing

func rebuild():
	if not world: return
	clear_children(terrain_root); clear_children(props_root); object_nodes.clear()
	if water_root: world.remove_child(water_root); water_root.queue_free()
	water_root=null
	var visible_data = document.data.duplicate(true)
	if cutaway and not previewing:
		visible_data.terrain = visible_data.terrain.filter(func(t): return t.cell[1] <= layer)
	var generator = HabitatTerrain.new()
	var mesh = generator.build(visible_data,registry)
	if mesh.get_surface_count() > 0:
		var terrain_instance = MeshInstance3D.new(); terrain_instance.mesh = mesh; terrain_root.add_child(terrain_instance)
		var body = StaticBody3D.new(); body.collision_layer = 1; body.collision_mask = 0; terrain_instance.add_child(body)
		var shape = CollisionShape3D.new(); shape.shape = mesh.create_trimesh_shape(); body.add_child(shape)
	if water_visible or previewing:
		water_root=water_renderer.build(visible_data); world.add_child(water_root)
	for obj in document.data.objects:
		if cutaway and not previewing and obj.position[1] > layer+1: continue
		var root = Node3D.new(); props_root.add_child(root); root.position=as_vector(obj.position); root.rotation_degrees=as_vector(obj.rotation); root.scale=as_vector(obj.scale)
		var model = registry.instance(obj.asset); root.add_child(model)
		var asset = registry.assets.get(obj.asset,{"dimensions":[1,1,1],"solid":false})
		var dimensions = as_vector(asset.dimensions)
		var body = StaticBody3D.new(); body.collision_layer = 2; body.collision_mask = 0; body.set_meta("instance_id",obj.id); root.add_child(body)
		var shape = CollisionShape3D.new(); var box = BoxShape3D.new(); box.size=dimensions; shape.shape=box; shape.position.y=dimensions.y/2; body.add_child(shape)
		if asset.get("solid",false):
			for mesh_node in model.find_children("*","MeshInstance3D",true,false):
				var solid_body=StaticBody3D.new(); solid_body.collision_layer=1; solid_body.collision_mask=0; solid_body.set_meta("instance_id",obj.id); mesh_node.add_child(solid_body)
				var solid_shape=CollisionShape3D.new(); solid_shape.shape=mesh_node.mesh.create_trimesh_shape(); solid_body.add_child(solid_shape)
		object_nodes[obj.id] = root
	rebuild_grid(); refresh_selection(); update_title(); atmosphere.apply(document.data.get("environment",{}))
	selection_list.clear(); selection_list.add_item("Select object by name…")
	for obj in document.data.objects:
		selection_list.add_item(obj.get("name",registry.assets.get(obj.asset,{}).get("name",obj.asset))+" · "+obj.id.left(6))
		selection_list.set_item_metadata(selection_list.item_count-1,obj.id)
	if spawn_marker: world.remove_child(spawn_marker); spawn_marker.queue_free()
	spawn_marker=Node3D.new(); world.add_child(spawn_marker)
	wire_box(AABB(as_vector(document.data.spawn),Vector3(.35,.85,.35)),Color("a5e5ff"),spawn_marker)
	spawn_marker.visible=not previewing

func as_vector(values: Array) -> Vector3:
	return Vector3(values[0],values[1],values[2])

func vector_array(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

func make_ghost():
	if not world: return
	if ghost: world.remove_child(ghost); ghost.queue_free()
	ghost = Node3D.new(); world.add_child(ghost)
	var asset = registry.assets[active_asset]
	if asset.kind in ["terrain","water"]:
		var m = MeshInstance3D.new(); var cube = BoxMesh.new(); cube.size=Vector3.ONE; m.mesh=cube; m.position.y=.5; ghost.add_child(m)
	else: ghost.add_child(registry.instance(active_asset))
	set_ghost_color(false)
	ghost.visible = false

func set_ghost_color(valid: bool):
	var mat = StandardMaterial3D.new(); mat.albedo_color = Color(.3,1,.65,.45) if valid else Color(1,.25,.25,.45)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for node in ghost.find_children("*","MeshInstance3D",true,false): node.material_override=mat

func ray_at(point: Vector2, mask: int = 3) -> Dictionary:
	var origin = camera.project_ray_origin(point); var direction = camera.project_ray_normal(point)
	var pick_mask=mask|8 if water_visible and mask in [1,3] else mask
	# A nearby segment avoids float precision loss at tiny shared triangle edges;
	# retain the long query for tall/deep construction and distant camera positions.
	for reach in [64.0,10000.0]:
		var query=PhysicsRayQueryParameters3D.create(origin,origin+direction*reach,pick_mask)
		var hit=viewport.find_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty(): return hit
	return {}

func plane_at(point: Vector2):
	var plane = Plane(Vector3.UP,float(layer))
	return plane.intersects_ray(camera.project_ray_origin(point),camera.project_ray_normal(point))

func update_ghost(point: Vector2):
	if previewing or not tool in ["Place","Erase","Move"]: ghost.visible=false; return
	var hit = ray_at(point,1)
	var position = plane_at(point)
	# Holding Alt forces the construction plane, including below existing floors.
	if not Input.is_key_pressed(KEY_ALT) and not hit.is_empty(): position = hit.position
	if position == null: ghost.visible=false; ghost_valid=false; return
	var asset = registry.assets[active_asset]
	if painting and stroke_plane != null and (asset.kind in ["terrain","water"] or tool=="Erase"):
		position=stroke_plane.intersects_ray(camera.project_ray_origin(point),camera.project_ray_normal(point))
		if position==null: ghost.visible=false; ghost_valid=false; return
		hit={}
	if tool == "Erase":
		if hit.is_empty() and not painting: ghost.visible=false; ghost_valid=false; return
		if not hit.is_empty(): position = hit.position-hit.normal*.08
		ghost_cell = [roundi(position.x),floori(position.y),roundi(-position.z)]
		ghost_position = Vector3(ghost_cell[0],ghost_cell[1],-ghost_cell[2])
		ghost_valid = document.terrain_map().has(HabitatDocument.key(ghost_cell))
	elif asset.kind in ["terrain","water"]:
		if not Input.is_key_pressed(KEY_ALT) and not hit.is_empty(): position += hit.normal*.08
		ghost_cell = [roundi(position.x),floori(position.y+.001),roundi(-position.z)]
		ghost_position = Vector3(ghost_cell[0],ghost_cell[1],-ghost_cell[2])
		ghost_reason = document.can_place(asset,ghost_position,0,Vector3.ONE)
		ghost_valid = ghost_reason.is_empty()
	else:
		ghost_position = position
		if asset.get("solid",false) and not hit.is_empty() and abs(hit.normal.y)<.6:
			var d=as_vector(asset.dimensions)
			if posmod(roundi(rotation_y/90),2): d=Vector3(d.z,d.y,d.x)
			ghost_position+=hit.normal*Vector3(d.x/2,d.y/2,d.z/2)-Vector3(0,d.y/2,0)
			position=ghost_position
		if asset.get("solid",false): ghost_position=Vector3(round(position.x),round(position.y*4)/4,round(position.z))
		elif fine_snap: ghost_position=position.snapped(Vector3(.25,.01,.25))
		ghost_reason = document.can_place(asset,ghost_position,rotation_y,as_vector(asset.dimensions))
		ghost_valid = ghost_reason.is_empty()
	ghost.position=ghost_position; ghost.rotation_degrees.y=rotation_y; ghost.visible=true
	set_ghost_color(ghost_valid)

func place_at_cursor():
	if previewing: return
	if not ghost_valid:
		if not ghost_reason.is_empty(): set_status(ghost_reason)
		return
	var k = HabitatDocument.key(ghost_cell) if registry.assets[active_asset].kind in ["terrain","water"] or tool=="Erase" else str(ghost_position)
	if painted.has(k): return
	painted[k] = true
	if tool == "Erase":
		document.data.terrain = document.data.terrain.filter(func(t): return HabitatDocument.key(t.cell)!=k)
	elif tool == "Place":
		var asset = registry.assets[active_asset]
		if asset.kind in ["terrain","water"]: document.data.terrain.append({"cell":ghost_cell.duplicate(),"asset":active_asset})
		else:
			document.data.objects.append({"id":HabitatDocument.new_id(),"asset":active_asset,"position":vector_array(ghost_position),"rotation":[0,rotation_y,0],"scale":[1,1,1],"solid":asset.get("solid",false),"dimensions":asset.dimensions.duplicate(),"properties":{}})
	rebuild()

func pick(point: Vector2) -> String:
	var hit = ray_at(point)
	if hit.is_empty(): return ""
	var collider=hit.collider
	while collider and not collider.has_meta("instance_id"):
		collider=collider.get_parent()
	if collider: return collider.get_meta("instance_id")
	var p = hit.position-hit.normal*.08
	return "t:"+HabitatDocument.key([roundi(p.x),floori(p.y),roundi(-p.z)])

func view_input(event: InputEvent):
	if event is InputEventMouseButton:
		recent_hover=event.position
		if event.button_index==MOUSE_BUTTON_LEFT and ((event.pressed and event.shift_pressed) or camera_drag==MOUSE_BUTTON_LEFT):
			if event.pressed:
				view.grab_focus(); camera_drag=MOUSE_BUTTON_LEFT; orbit_drag_distance=0.0; ghost.visible=false
			else:
				camera_drag=0
				# Preserve Shift-click multiselect; only a drag navigates.
				if orbit_drag_distance<4 and not previewing and tool=="Select":
					var id=pick(event.position)
					if not id.is_empty():
						if selected.has(id): selected.erase(id)
						else: selected.append(id)
					refresh_selection()
			return
		if event.button_index in [MOUSE_BUTTON_RIGHT,MOUSE_BUTTON_MIDDLE]:
			camera_drag = event.button_index if event.pressed else 0; return
		if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
			distance=clamp(distance*(.9 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1.1),.5,5000); update_camera(); return
		if event.button_index == MOUSE_BUTTON_LEFT and not previewing:
			if event.pressed:
				view.grab_focus(); drag_start=event.position
				if tool in ["Select","Move"]:
					var id=pick(event.position)
					if tool=="Move" and not selected.is_empty(): move_to_cursor(); return
					if event.shift_pressed:
						if not id.is_empty():
							if selected.has(id): selected.erase(id)
							else: selected.append(id)
					else: selected=[] if id.is_empty() else [id]
					selecting_box=id.is_empty(); refresh_selection()
				elif tool=="Erase" and event.ctrl_pressed:
					var id=pick(event.position)
					if not id.is_empty(): selected=[id]; delete_selection()
				else:
					painted.clear(); stroke_before=document.data.duplicate(true); update_ghost(event.position)
					var hit=ray_at(event.position,1)
					var normal=Vector3.UP
					if not hit.is_empty() and not event.alt_pressed:
						var n=hit.normal.abs(); normal=Vector3(sign(hit.normal.x),0,0) if n.x>n.y and n.x>n.z else (Vector3(0,0,sign(hit.normal.z)) if n.z>n.y else Vector3(0,sign(hit.normal.y),0))
						stroke_plane=Plane(normal,hit.position+normal*(-.08 if tool=="Erase" else .08))
					else: stroke_plane=Plane(Vector3.UP,float(layer)+.001)
					painting=true; place_at_cursor()
			else: end_pointer(event.position)
	elif event is InputEventMouseMotion:
		recent_hover=event.position
		if camera_drag:
			if camera_drag==MOUSE_BUTTON_MIDDLE:
				target+=(-camera.global_basis.x*event.relative.x+camera.global_basis.y*event.relative.y)*distance*.0018
			else:
				orbit_drag_distance+=event.relative.length()
				yaw-=event.relative.x*.008; pitch=clamp(pitch+event.relative.y*.008,-1.565,1.565)
			update_camera()
		elif selecting_box:
			box_rect=Rect2(drag_start,event.position-drag_start).abs(); overlay.queue_redraw()
		else:
			update_ghost(event.position)
			if painting and (registry.assets[active_asset].kind in ["terrain","water"] or tool=="Erase"): place_at_cursor()

func end_pointer(point: Vector2):
	if painting:
		painting=false; commit(stroke_before)
	if selecting_box:
		selecting_box=false; overlay.queue_redraw()
		if point.distance_to(drag_start)>6:
			selected.clear()
			var rect=Rect2(drag_start,point-drag_start).abs()
			for t in document.data.terrain:
				if not water_visible and HabitatWater.is_water(t): continue
				if cutaway and t.cell[1]>layer: continue
				var p=Vector3(t.cell[0],t.cell[1]+.5,-t.cell[2])
				if not camera.is_position_behind(p) and rect.has_point(camera.unproject_position(p)): selected.append("t:"+HabitatDocument.key(t.cell))
			for id in object_nodes:
				var p=object_nodes[id].position
				if not camera.is_position_behind(p) and rect.has_point(camera.unproject_position(p)): selected.append(id)
			refresh_selection()

func _input(event):
	# Handle viewport pointer events before SubViewportContainer forwards them to
	# its child world. gui_input alone misses buttons consumed by the container.
	if (event is InputEventMouseButton or event is InputEventMouseMotion) and view and not file_dialog.visible and not confirm.visible and not error_dialog.visible and not (sky_window and sky_window.visible):
		var local_point=event.position-view.global_position
		if Rect2(Vector2.ZERO,view.size).has_point(local_point) or camera_drag!=0 or selecting_box:
			var local_event=event.duplicate()
			local_event.position=local_point
			view_input(local_event)
			get_viewport().set_input_as_handled()
			return
	# Commit a stroke even when released outside the viewport.
	if event is InputEventMouseButton and not event.pressed and event.button_index==MOUSE_BUTTON_LEFT and painting:
		painting=false; commit(stroke_before)
	if not event is InputEventKey or not event.pressed or event.echo: return
	if get_viewport().gui_get_focus_owner() is LineEdit or file_dialog.visible or confirm.visible or error_dialog.visible or (sky_window and sky_window.visible) or (panorama_dialog and panorama_dialog.visible): return
	var command = event.ctrl_pressed or event.meta_pressed
	if command:
		match event.keycode:
			KEY_S: save()
			KEY_O: guard_action(func(): open_dialog(FileDialog.FILE_MODE_OPEN_FILE))
			KEY_N: guard_action(new_document)
			KEY_Z:
				if event.shift_pressed: redo()
				else: undo()
			KEY_Y: redo()
			KEY_D: duplicate_selection()
			_: return
		get_viewport().set_input_as_handled()
		return
	match event.keycode:
		KEY_ESCAPE:
			if previewing: toggle_preview()
			else: set_tool("Select")
		KEY_R: rotate_selection()
		KEY_DELETE,KEY_BACKSPACE: delete_selection()
		KEY_F: focus_selection()
		KEY_H: show_help()
		KEY_G: set_tool("Move")
		KEY_B: set_tool("Place")
		KEY_1: set_tool("Select")
		KEY_3: set_tool("Erase")
		KEY_BRACKETLEFT: layer_control.value-=1
		KEY_BRACKETRIGHT: layer_control.value+=1
		KEY_TAB: toggle_preview()
		KEY_W,KEY_A,KEY_S,KEY_D,KEY_Z,KEY_X,KEY_C,KEY_V,KEY_Q,KEY_E: pass
		_: return
	get_viewport().set_input_as_handled()

func commit(before: Dictionary):
	if JSON.stringify(before)==signature(): return
	undo_stack.append(before.duplicate(true)); redo_stack.clear()
	if undo_stack.size()>100: undo_stack.pop_front()
	update_title()

func undo():
	if previewing or undo_stack.is_empty(): return
	redo_stack.append(document.data.duplicate(true)); document.data=undo_stack.pop_back(); selected.clear(); rebuild()

func redo():
	if previewing or redo_stack.is_empty(): return
	undo_stack.append(document.data.duplicate(true)); document.data=redo_stack.pop_back(); selected.clear(); rebuild()

func set_tool(value: String):
	if previewing: return
	tool=value
	for name in tool_buttons: tool_buttons[name].button_pressed=(name==tool)
	if value in ["Place","Erase"]: selected.clear()
	refresh_selection()
	if ghost: ghost.visible=false
	set_status("%s • %s • R rotates • Alt uses build layer %d • Ctrl-click with Erase deletes props" % [tool,registry.assets[active_asset].name,layer]); update_title()

func find_object(id: String) -> Dictionary:
	for obj in document.data.objects:
		if obj.id==id: return obj
	return {}

func selection_center() -> Vector3:
	var result=Vector3.ZERO; var count=0
	for id in selected:
		if id.begins_with("t:"):
			var t=document.terrain_map().get(id.substr(2),{})
			if not t.is_empty(): result+=Vector3(t.cell[0],t.cell[1]+.5,-t.cell[2]); count+=1
		else:
			var obj=find_object(id)
			if not obj.is_empty(): result+=as_vector(obj.position); count+=1
	return result/max(count,1)

func refresh_selection():
	if not outlines: return
	clear_children(outlines); clear_children(inspector)
	section("%d selected" % selected.size(),inspector)
	for id in selected:
		if id.begins_with("t:"):
			var t=document.terrain_map().get(id.substr(2),{})
			if t.is_empty(): continue
			wire_box(AABB(Vector3(t.cell[0]-.5,t.cell[1],-t.cell[2]-.5),Vector3.ONE),Color("ffdf80"),outlines)
		elif object_nodes.has(id):
			var obj=find_object(id); var asset=registry.assets.get(obj.asset,{"dimensions":[1,1,1]})
			var holder=Node3D.new(); outlines.add_child(holder); holder.transform=object_nodes[id].transform
			var d=as_vector(asset.dimensions); wire_box(AABB(Vector3(-d.x/2,0,-d.z/2),d),Color("ffdf80"),holder)
	if selected.size()!=1: return
	var id=selected[0]
	if id.begins_with("t:"):
		var t=document.terrain_map().get(id.substr(2),{})
		if not t.is_empty():
			var label=Label.new(); label.text="%s\nCell: %s" % [t.asset,str(t.cell)]; inspector.add_child(label)
			if HabitatWater.is_water(t): water_inspector(t)
		return
	var obj=find_object(id)
	if obj.is_empty(): return
	var label=Label.new(); label.text=obj.asset; inspector.add_child(label)
	var name_edit=LineEdit.new(); name_edit.text=obj.get("name",""); name_edit.placeholder_text="Object name"; inspector.add_child(name_edit)
	name_edit.text_submitted.connect(func(value):
		if previewing: return
		var before=document.data.duplicate(true); obj.name=value; commit(before); name_edit.release_focus())
	var asset=registry.assets.get(obj.asset,{})
	for property in ["position","rotation","scale"]:
		var row=HBoxContainer.new(); inspector.add_child(row)
		var l=Label.new(); l.text=property.left(3); row.add_child(l)
		for axis in range(3):
			var spin=SpinBox.new(); spin.allow_greater=true; spin.allow_lesser=true; spin.min_value=-100; spin.max_value=100; spin.step=.25 if property=="position" else 1.0; spin.value=obj[property][axis]; spin.custom_minimum_size.x=67; row.add_child(spin)
			if property=="scale": spin.min_value=asset.get("scale_range",[.25,3])[0]; spin.max_value=asset.get("scale_range",[.25,3])[1]; spin.allow_lesser=false; spin.allow_greater=false; spin.step=.25
			if asset.get("solid",false) and (property=="scale" or (property=="rotation" and axis!=1)): spin.editable=false
			if property=="rotation" and asset.get("solid",false): spin.step=90
			spin.value_changed.connect(func(value): edit_property(id,property,axis,value))

func edit_property(id: String, property: String, axis: int, value: float):
	if previewing: return
	var obj=find_object(id)
	var before=document.data.duplicate(true)
	obj[property][axis]=value
	var asset=registry.assets.get(obj.asset,{"solid":false,"dimensions":[1,1,1]})
	var reason=document.can_place(asset,as_vector(obj.position),obj.rotation[1],as_vector(asset.dimensions)*as_vector(obj.scale),[id])
	if not reason.is_empty(): document.data=before; set_status(reason)
	else: commit(before)
	# Defer rebuilding inspector until the current spinbox callback returns.
	call_deferred("rebuild")

func delete_selection():
	if previewing or selected.is_empty(): return
	var before=document.data.duplicate(true)
	document.data.terrain=document.data.terrain.filter(func(t): return not selected.has("t:"+HabitatDocument.key(t.cell)))
	document.data.objects=document.data.objects.filter(func(o): return not selected.has(o.id))
	selected.clear(); commit(before); rebuild()

func move_selection(delta: Vector3, duplicate: bool = false):
	if previewing or selected.is_empty(): return
	var before=document.data.duplicate(true)
	var next_selection=[]
	var terrain_ids=selected.filter(func(id): return id.begins_with("t:"))
	# Remove moved terrain from occupancy while checking the entire proposed group.
	if not duplicate:
		document.data.terrain=document.data.terrain.filter(func(t): return not selected.has("t:"+HabitatDocument.key(t.cell)))
	for id in terrain_ids:
		var old={}
		for t in before.terrain:
			if "t:"+HabitatDocument.key(t.cell)==id: old=t
		if old.is_empty(): continue
		var t=old.duplicate(true); t.cell=[old.cell[0]+roundi(delta.x),old.cell[1]+roundi(delta.y),old.cell[2]-roundi(delta.z)]
		var asset=registry.assets.get(t.asset,{"solid":true})
		var p=Vector3(t.cell[0],t.cell[1],-t.cell[2])
		var reason=document.can_place(asset,p,0,Vector3.ONE,[] if duplicate else selected)
		if not reason.is_empty(): document.data=before; set_status(reason); return
		document.data.terrain.append(t); next_selection.append("t:"+HabitatDocument.key(t.cell))
	var original_objects=before.objects
	if not duplicate: document.data.objects=document.data.objects.filter(func(o): return not selected.has(o.id))
	for id in selected:
		if id.begins_with("t:"): continue
		var old={}
		for existing in original_objects:
			if existing.id==id: old=existing
		if old.is_empty(): continue
		var obj=old.duplicate(true); obj.position=vector_array(as_vector(old.position)+delta)
		if duplicate: obj.id=HabitatDocument.new_id()
		var asset=registry.assets.get(obj.asset,{"solid":false,"dimensions":[1,1,1]})
		var reason=document.can_place(asset,as_vector(obj.position),obj.rotation[1],as_vector(asset.dimensions)*as_vector(obj.scale),[] if duplicate else selected)
		if not reason.is_empty(): document.data=before; set_status(reason); return
		next_selection.append(obj.id); document.data.objects.append(obj)
	selected=next_selection; commit(before); rebuild()

func move_to_cursor():
	var p=plane_at(recent_hover)
	if p==null: return
	var hit=ray_at(recent_hover,1)
	if not Input.is_key_pressed(KEY_ALT) and not hit.is_empty(): p=hit.position
	var center=selection_center()
	if not selected.is_empty():
		if selected[0].begins_with("t:"):
			var t=document.terrain_map().get(selected[0].substr(2),{})
			if not t.is_empty(): center=Vector3(t.cell[0],t.cell[1],-t.cell[2])
		else:
			var obj=find_object(selected[0])
			if not obj.is_empty(): center=as_vector(obj.position)
	var delta=(p-center).snapped(Vector3.ONE)
	move_selection(delta)

func duplicate_selection():
	move_selection(Vector3.RIGHT,true)

func rotate_selection():
	if previewing: return
	if tool=="Place":
		var rotations=registry.assets[active_asset].get("rotations",[])
		rotation_y=rotations[(rotations.find(rotation_y)+1)%rotations.size()] if not rotations.is_empty() else fposmod(rotation_y+90,360)
		update_ghost(recent_hover); return
	var before=document.data.duplicate(true)
	for id in selected:
		if id.begins_with("t:"): continue
		var obj=find_object(id)
		if obj.is_empty(): continue
		obj.rotation[1]=fposmod(obj.rotation[1]+90,360)
		var asset=registry.assets.get(obj.asset,{"solid":false,"dimensions":[1,1,1]})
		var reason=document.can_place(asset,as_vector(obj.position),obj.rotation[1],as_vector(asset.dimensions)*as_vector(obj.scale),selected)
		if not reason.is_empty(): document.data=before; set_status(reason); rebuild(); return
	commit(before); rebuild()

func focus_selection():
	if not selected.is_empty(): target=selection_center(); distance=7; update_camera()

func frame_all():
	var low=0.0; var high=1.0
	for t in document.data.terrain: low=min(low,t.cell[1]); high=max(high,t.cell[1]+1)
	for obj in document.data.objects: low=min(low,obj.position[1]); high=max(high,obj.position[1]+registry.assets.get(obj.asset,{"dimensions":[1,1,1]}).dimensions[1]*obj.scale[1])
	target=Vector3((document.data.grid.width-1)/2.0,(low+high)/2,-(document.data.grid.depth-1)/2.0)
	distance=max(document.data.grid.width,document.data.grid.depth,high-low)*1.9; update_camera()

func set_spawn():
	if previewing: return
	var before=document.data.duplicate(true)
	document.data.spawn=vector_array(ghost_position+Vector3(0,1.03 if registry.assets[active_asset].kind in ["terrain","water"] else .03,0)); commit(before); rebuild()
	set_status("Spawn set above last placement cursor. Preview to check ground contact.")

func content_directory() -> String:
	if not content_root_override.is_empty(): return content_root_override
	var root=ProjectSettings.globalize_path("res://").path_join("../../Assets/Habitats").simplify_path()
	if DirAccess.dir_exists_absolute(root): return root
	return OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)

func open_dialog(mode: int):
	if previewing: return
	file_dialog.file_mode=mode; file_dialog.current_dir=content_directory()
	if mode==FileDialog.FILE_MODE_SAVE_FILE: file_dialog.current_file=document.data.name.to_snake_case()+".json"
	file_dialog.popup_centered_ratio(.8)

func save():
	if previewing: return
	if file_path.is_empty(): open_dialog(FileDialog.FILE_MODE_SAVE_FILE)
	else: save_path(file_path)

func save_path(path: String):
	if not path.ends_with(".json"): path+=".json"
	if document.save_file(path,registry.assets): file_path=path; saved_signature=signature(); update_title(); set_status("Saved "+path)
	else: show_error(document.error)

func load_path(path: String):
	if document.load_file(path,registry.assets):
		file_path=path; saved_signature=signature(); undo_stack.clear(); redo_stack.clear(); selected.clear(); rebuild(); frame_all()
		var missing=document.missing_assets(registry.assets)
		if not missing.is_empty(): show_error("Missing assets preserved: "+str(missing)+". Props show magenta placeholders; terrain uses fallback material.")
		elif not atmosphere.missing_panorama.is_empty(): show_error("Panorama missing: "+atmosphere.missing_panorama+". Procedural fallback shown; the reference is preserved.")
		else: set_status("Opened "+path)
	else: show_error(document.error)

func guard_action(action: Callable):
	if previewing: return
	if dirty(): pending_action=action; confirm.popup_centered()
	else: action.call()

func new_document():
	document.data=HabitatDocument.fresh(); file_path=""; saved_signature=signature(); selected.clear(); undo_stack.clear(); redo_stack.clear(); rebuild()

func duplicate_document():
	if previewing: return
	var before=document.data.duplicate(true); document.data.id=HabitatDocument.new_id(); document.data.name+=" Copy"; file_path=""; commit(before); rebuild()

func update_title():
	if not title_label: return
	title_label.text="  %s%s  •  %s" % [document.data.name," *" if dirty() else "",tool]
	DisplayServer.window_set_title("Fibu Habitat Creator — "+document.data.name+(" *" if dirty() else ""))

func set_status(text: String):
	if status: status.text="  "+text

func show_error(text: String):
	error_dialog.dialog_text=text; error_dialog.popup_centered(Vector2i(650,230))

func show_help():
	error_dialog.title="Desktop controls"
	error_dialog.dialog_text="WASD: camera movement • Z/X: orbit left/right • C/V: zoom in/out\nShift-left-drag or right-drag: orbit above/under • Middle-drag: pan • Wheel: zoom\nB: place • 1/Esc: select • 3: erase • G: move selection, then click destination\nR: rotate • Delete: delete • Cmd/Ctrl-D: duplicate one cell right\nShift-click: multiselect • Drag empty space: box select\nCmd/Ctrl-S: save • Cmd/Ctrl-Z: undo • Shift-Cmd/Ctrl-Z: redo\n[ / ]: build layer • Alt: force placement on build plane\nCtrl-click in Erase: delete a prop • F: focus • Tab: preview\nQ/E: camera down/up • Fly: view-relative movement • Preview: WASD/arrows, Space jumps, Esc returns\nChoose overlapping props using the selection dropdown.\nPreview is a navigation proxy, not the native Swift Fibu controller."
	error_dialog.popup_centered(Vector2i(800,410))

func toggle_preview():
	view.grab_focus()
	if not previewing:
		if painting: painting=false; commit(stroke_before)
		saved_camera=[target,yaw,pitch,distance]; previewing=true; rebuild()
		ghost.visible=false; outlines.visible=false; grid_root.visible=false; spawn_marker.visible=false
		proxy=CharacterBody3D.new(); proxy.collision_layer=4; proxy.collision_mask=1; proxy.floor_snap_length=.3; proxy.position=as_vector(document.data.spawn); world.add_child(proxy)
		var shape=CollisionShape3D.new(); var capsule=CapsuleShape3D.new(); capsule.radius=.22; capsule.height=.85; shape.shape=capsule; shape.position.y=.425; proxy.add_child(shape)
		var visual=MeshInstance3D.new(); var capsule_mesh=CapsuleMesh.new(); capsule_mesh.radius=.22; capsule_mesh.height=.85; visual.mesh=capsule_mesh; visual.position.y=.425
		var mat=StandardMaterial3D.new(); mat.albedo_color=Color("fff0c9"); visual.material_override=mat; proxy.add_child(visual)
		preview_button.text="Return to editor"; set_status("Navigation proxy • WASD/arrows • Space jumps • Stairs auto-step up to 0.3m • Esc returns")
	else:
		previewing=false; world.remove_child(proxy); proxy.queue_free(); proxy=null
		target=saved_camera[0]; yaw=saved_camera[1]; pitch=saved_camera[2]; distance=saved_camera[3]; update_camera()
		outlines.visible=true; rebuild(); preview_button.text="Preview ▶"; set_status("Returned to editing; authored layout was preserved.")

func _physics_process(delta):
	if atmosphere: atmosphere.tick(delta)
	# Command shortcuts must not also move/rotate the camera while held.
	if Input.is_key_pressed(KEY_CTRL) or Input.is_key_pressed(KEY_META): return
	var focus=get_viewport().gui_get_focus_owner()
	if focus is LineEdit or (file_dialog and file_dialog.visible) or (error_dialog and error_dialog.visible) or (confirm and confirm.visible) or (sky_window and sky_window.visible): return
	if previewing and proxy:
		var input=Vector3(float(Input.is_physical_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT))-float(Input.is_physical_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT)),0,float(Input.is_physical_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN))-float(Input.is_physical_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)))
		preview_step(delta,input,Input.is_physical_key_pressed(KEY_SPACE))
	elif camera:
		var movement=Vector3(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_E))-float(Input.is_physical_key_pressed(KEY_Q)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
		var turn=float(Input.is_physical_key_pressed(KEY_X))-float(Input.is_physical_key_pressed(KEY_Z))
		var zoom=float(Input.is_physical_key_pressed(KEY_V))-float(Input.is_physical_key_pressed(KEY_C))
		camera_step(delta,movement,turn,zoom)

func camera_step(delta: float, movement: Vector3, turn: float, zoom: float):
	if movement.length_squared()>0:
		var direction: Vector3
		if free_fly: direction=camera.basis*movement.normalized()
		else:
			var right=Vector3(cos(yaw),0,-sin(yaw))
			var backward=Vector3(sin(yaw),0,cos(yaw))
			direction=(right*movement.x+Vector3.UP*movement.y+backward*movement.z).normalized()
		target+=direction*delta*max(distance*.4,2)
	yaw+=turn*delta*1.2
	distance=clamp(distance*exp(zoom*delta*1.2),.5,5000)
	if movement.length_squared()>0 or turn!=0 or zoom!=0: update_camera()

func preview_step(delta: float, input: Vector3, jump: bool):
		var forward=Vector3(camera.global_basis.z.x,0,camera.global_basis.z.z).normalized()
		var right=Vector3(camera.global_basis.x.x,0,camera.global_basis.x.z).normalized()
		var movement=(right*input.x+forward*input.z).normalized()*2.5
		proxy.velocity.x=movement.x; proxy.velocity.z=movement.z
		if not proxy.is_on_floor(): proxy.velocity.y-=12*delta
		elif jump: proxy.velocity.y=5
		else: proxy.velocity.y=-.2
		# Small stair step: require support at both ends and clear raised capsule path.
		if proxy.is_on_floor() and movement.length_squared()>0:
			var travel=movement*delta
			var raised=proxy.global_transform; raised.origin.y+=.3
			if proxy.test_move(proxy.global_transform,travel) and not proxy.test_move(proxy.global_transform,Vector3.UP*.3) and not proxy.test_move(raised,travel):
				var ahead=proxy.position+travel+movement.normalized()*.22
				var hit=viewport.find_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(ahead+Vector3.UP*.31,ahead-Vector3.UP*.08,1))
				if not hit.is_empty() and hit.normal.y>.6: proxy.position.y=max(proxy.position.y,hit.position.y+.015)
		proxy.move_and_slide()
		if proxy.position.y < -200: proxy.position=as_vector(document.data.spawn); proxy.velocity=Vector3.ZERO
		if proxy.position.distance_to(target)>4: target=target.lerp(proxy.position,delta*2); update_camera()
func _notification(what):
	if what==NOTIFICATION_WM_CLOSE_REQUEST:
		if previewing: toggle_preview()
		guard_action(func(): get_tree().quit())


func sky_change(key: String, value):
	if previewing: return
	var before=document.data.duplicate(true)
	var settings=HabitatAtmosphere.resolved(document.data.get("environment",{}))
	settings[key]=value
	document.data.environment=settings
	atmosphere.apply(settings)
	commit(before)

func choose_sky(settings: Dictionary):
	if previewing: return
	var before=document.data.duplicate(true)
	document.data.environment=settings.duplicate(true)
	atmosphere.apply(settings); commit(before); refresh_sky_fields()

func open_sky():
	if previewing: return
	if not sky_window:
		sky_window=Window.new(); sky_window.title="Sky & Atmosphere"; sky_window.size=Vector2i(760,760); sky_window.min_size=Vector2i(640,480); sky_window.transient=true; sky_window.exclusive=true; add_child(sky_window)
		sky_window.close_requested.connect(func(): sky_window.hide())
		var layout=VBoxContainer.new(); layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); sky_window.add_child(layout)
		var presets=HFlowContainer.new(); layout.add_child(presets)
		for index in range(HabitatAtmosphere.PRESETS.size()):
			var id=HabitatAtmosphere.PRESETS[index]
			var b=button(HabitatAtmosphere.NAMES[index],func(): choose_sky(HabitatAtmosphere.preset(id)),presets)
			b.custom_minimum_size=Vector2(230,72); b.expand_icon=true; b.add_theme_constant_override("icon_max_width",80)
			var thumbnail="res://assets/skies/"+id+".png"
			if ResourceLoader.exists(thumbnail): b.icon=load(thumbnail)
		var actions=HFlowContainer.new(); layout.add_child(actions)
		sky_name=LineEdit.new(); sky_name.placeholder_text="Custom preset name"; sky_name.custom_minimum_size.x=190; actions.add_child(sky_name)
		button("Save preset",func(): save_sky_preset(false),actions)
		button("Duplicate preset",func(): save_sky_preset(true),actions)
		button("Revert session changes",func(): choose_sky(sky_revert),actions)
		sky_preset_list=OptionButton.new(); actions.add_child(sky_preset_list)
		sky_preset_list.item_selected.connect(func(index):
			if index==0: return
			var raw=JSON.parse_string(FileAccess.get_file_as_string(sky_preset_paths[index-1]))
			if raw is Dictionary and HabitatAtmosphere.validate(raw).is_empty(): choose_sky(raw))
		var scroll=ScrollContainer.new(); scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL; layout.add_child(scroll)
		sky_fields=VBoxContainer.new(); sky_fields.size_flags_horizontal=Control.SIZE_EXPAND_FILL; scroll.add_child(sky_fields)
		var footer=HFlowContainer.new(); layout.add_child(footer)
		button("Import panorama…",import_panorama,footer)
		button("Use procedural sky",func(): sky_change("panorama",""); refresh_sky_fields(),footer)
		button("Done",func(): sky_window.hide(),footer)
	sky_revert=document.data.get("environment",{}).duplicate(true)
	refresh_sky_fields(); refresh_custom_skies(); sky_window.popup_centered()

func refresh_sky_fields():
	if not sky_fields: return
	clear_children(sky_fields)
	var settings=HabitatAtmosphere.resolved(document.data.get("environment",{}))
	sky_name.text=settings.name
	for key in ["sky_top","horizon","lower_sky","sun_color","ambient_color","cloud_color","fog_color","landscape_tint"]:
		var row=HBoxContainer.new(); sky_fields.add_child(row)
		var label=Label.new(); label.text=key.capitalize(); label.custom_minimum_size.x=250; row.add_child(label)
		var picker=ColorPickerButton.new(); picker.color=Color(settings[key]); picker.edit_alpha=false; picker.custom_minimum_size=Vector2(130,30); row.add_child(picker)
		var history={}
		picker.color_changed.connect(func(color):
			if history.is_empty(): history.before=document.data.duplicate(true)
			var env=HabitatAtmosphere.resolved(document.data.get("environment",{})); env[key]=color.to_html(false); document.data.environment=env; atmosphere.apply(env); update_title())
		picker.popup_closed.connect(func():
			if history.has("before"): commit(history.before); history.clear())
	var ranges={"sun_azimuth":[-360,360,1],"sun_elevation":[-90,90,1],"sun_energy":[0,4,.01],"ambient_energy":[0,2,.01],"cloud_density":[0,1,.05],"cloud_softness":[0,1,.05],"cloud_speed":[0,.1,.005],"fog_density":[0,.05,.001],"fog_height":[-10000,10000,1],"fog_height_density":[0,.1,.001],"background_rotation":[-360,360,1],"stars":[0,2,.1],"moon":[0,1,.1],"haze":[0,1,.05],"horizon_offset":[0,1,.05]}
	for key in ranges:
		var row=HBoxContainer.new(); sky_fields.add_child(row)
		var label=Label.new(); label.text=key.capitalize(); label.custom_minimum_size.x=250; row.add_child(label)
		var spin=SpinBox.new(); spin.min_value=ranges[key][0]; spin.max_value=ranges[key][1]; spin.step=ranges[key][2]; spin.value=settings[key]; spin.custom_minimum_size.x=180; row.add_child(spin)
		spin.value_changed.connect(func(value): sky_change(key,value))
	for key in ["cloud_motion","landscape_visible"]:
		var check=CheckBox.new(); check.text=key.capitalize(); check.button_pressed=settings[key]; sky_fields.add_child(check)
		check.toggled.connect(func(value): sky_change(key,value))
	var kinds=OptionButton.new()
	for name in ["Mountain ranges","Forest silhouettes","Desert mesas","Icy mountains"]: kinds.add_item(name)
	kinds.selected=int(settings.landscape_kind); sky_fields.add_child(kinds); kinds.item_selected.connect(func(index): sky_change("landscape_kind",index))
	var info=Label.new(); info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART; info.text="Panorama: "+(settings.panorama if not settings.panorama.is_empty() else "Procedural")+". Imported panoramas replace procedural clouds and landscapes; lighting/fog remain adjustable."; sky_fields.add_child(info)

func refresh_custom_skies():
	sky_preset_list.clear(); sky_preset_list.add_item("Saved presets…"); sky_preset_paths.clear()
	var folder=content_directory().path_join("SkyPresets")
	if not DirAccess.dir_exists_absolute(folder): return
	var files=DirAccess.get_files_at(folder); files.sort()
	for filename in files:
		if not filename.ends_with(".json"): continue
		var path=folder.path_join(filename); var raw=JSON.parse_string(FileAccess.get_file_as_string(path))
		if raw is Dictionary and HabitatAtmosphere.validate(raw).is_empty():
			sky_preset_paths.append(path); sky_preset_list.add_item(raw.get("name",filename))

func save_sky_preset(duplicate: bool):
	var settings=HabitatAtmosphere.resolved(document.data.get("environment",{}))
	settings.name=sky_name.text.strip_edges()
	if settings.name.is_empty(): settings.name="Custom sky"
	if duplicate: settings.name+=" Copy"
	var filename=settings.name.to_snake_case().validate_filename()
	var folder=content_directory().path_join("SkyPresets"); DirAccess.make_dir_recursive_absolute(folder)
	var path=folder.path_join(filename+("_"+HabitatDocument.new_id().left(6) if duplicate else "")+".json")
	if FileAccess.file_exists(path):
		var replace=ConfirmationDialog.new(); replace.title="Replace sky preset?"; replace.dialog_text="Replace the saved preset “%s” with these settings?" % settings.name; sky_window.add_child(replace)
		replace.confirmed.connect(func(): write_sky_preset(settings,path); replace.queue_free())
		replace.canceled.connect(func(): replace.queue_free()); replace.popup_centered(); return
	write_sky_preset(settings,path)

func write_sky_preset(settings: Dictionary, path: String):
	var f=FileAccess.open(path+".tmp",FileAccess.WRITE)
	if not f: set_status("Cannot save preset: "+path); return
	f.store_string(JSON.stringify(settings,"\t")+"\n"); f.flush(); var result=f.get_error(); f.close()
	if result!=OK or DirAccess.rename_absolute(path+".tmp",path)!=OK: set_status("Could not finish saving sky preset."); return
	choose_sky(settings); refresh_custom_skies(); set_status("Saved sky preset: "+path)

func import_panorama():
	if not panorama_dialog:
		panorama_dialog=FileDialog.new(); panorama_dialog.access=FileDialog.ACCESS_FILESYSTEM; panorama_dialog.file_mode=FileDialog.FILE_MODE_OPEN_FILE; panorama_dialog.filters=PackedStringArray(["*.png,*.jpg,*.jpeg,*.hdr,*.exr ; Equirectangular panorama"]); sky_window.add_child(panorama_dialog)
		panorama_dialog.file_selected.connect(load_panorama)
	panorama_dialog.popup_centered_ratio(.8)


func load_panorama(path: String):
	var image=Image.load_from_file(path)
	if not image or image.is_empty(): set_status("Could not read panorama."); return
	var digest=FileAccess.get_sha256(path).left(20)
	var relative="SkyArt/"+digest+"."+path.get_extension().to_lower()
	DirAccess.make_dir_recursive_absolute(content_directory().path_join("SkyArt"))
	if DirAccess.copy_absolute(path,content_directory().path_join(relative))!=OK: set_status("Cannot copy panorama to habitat content."); return
	sky_change("panorama",relative); refresh_sky_fields(); set_status("Panorama copied into Assets/Habitats; commit it with the layout.")


func selected_water_body(cell: Dictionary) -> Array:
	for component in HabitatWater.components(document.data):
		for item in component:
			if item.cell==cell.cell: return component
	return []

func edit_water(cell: Dictionary, property: String, value, record: bool = true):
	if previewing: return
	var body=selected_water_body(cell)
	if body.is_empty(): return
	var before=document.data.duplicate(true)
	var style=HabitatWater.style_for(document.data,body); style[property]=value
	if not HabitatWater.validate_style(style).is_empty(): return
	if not document.data.has("water_styles"): document.data.water_styles={}
	var id=body[0].get("water_style","")
	# Give this connected body a unique style; do not change disconnected ponds.
	var outside=false
	for t in document.data.terrain:
		if HabitatWater.is_water(t) and not t in body and t.get("water_style","default")==id: outside=true
	if id.is_empty() or id=="default" or outside: id="water_"+HabitatDocument.new_id()
	document.data.water_styles[id]=style
	for item in body: item.water_style=id
	if record: commit(before)
	else: update_title()
	# Keep inspector focus while editing; regenerate only rendering/picking nodes.
	refresh_water_render()

func refresh_water_render():
	if water_root: world.remove_child(water_root); water_root.queue_free()
	water_root=null
	if water_visible or previewing:
		var data=document.data.duplicate(true)
		if cutaway and not previewing: data.terrain=data.terrain.filter(func(t): return t.cell[1]<=layer)
		water_root=water_renderer.build(data); world.add_child(water_root)

func water_inspector(cell: Dictionary):
	var body=selected_water_body(cell)
	if body.is_empty(): return
	var style=HabitatWater.style_for(document.data,body)
	section("Connected water · %d cells" % body.size(),inspector)
	for property in ["shallow_color","deep_color","foam_color"]:
		var row=HBoxContainer.new(); inspector.add_child(row)
		var label=Label.new(); label.text=property.capitalize(); label.custom_minimum_size.x=145; row.add_child(label)
		var picker=ColorPickerButton.new(); picker.color=Color(style[property]); picker.edit_alpha=false; picker.custom_minimum_size=Vector2(75,28); row.add_child(picker)
		var history={}
		picker.color_changed.connect(func(color):
			if history.is_empty(): history.before=document.data.duplicate(true)
			edit_water(cell,property,color.to_html(false),false))
		picker.popup_closed.connect(func():
			if history.has("before"): commit(history.before); history.clear())
	var ranges={"opacity":[.02,.8,.02],"side_opacity":[.02,.8,.02],"depth_strength":[0,2,.05],"roughness":[0,1,.05],"highlight_strength":[0,.5,.01],"ripple_speed":[0,2,.05],"ripple_strength":[0,.1,.005],"ripple_scale":[.1,10,.1],"foam_width":[.02,.3,.01],"foam_coverage":[0,1,.05],"foam_speed":[0,1,.02],"foam_irregularity":[0,1,.05]}
	for property in ranges:
		var row=HBoxContainer.new(); inspector.add_child(row)
		var label=Label.new(); label.text=property.capitalize(); label.custom_minimum_size.x=145; row.add_child(label)
		var spin=SpinBox.new(); spin.min_value=ranges[property][0]; spin.max_value=ranges[property][1]; spin.step=ranges[property][2]; spin.value=style[property]; spin.custom_minimum_size.x=85; row.add_child(spin)
		spin.value_changed.connect(func(value): edit_water(cell,property,value))
	for property in ["animation_enabled","foam_enabled"]:
		var check=CheckBox.new(); check.text=property.capitalize(); check.button_pressed=style[property]; inspector.add_child(check)
		check.toggled.connect(func(value): edit_water(cell,property,value))
