extends SceneTree
func _initialize(): call_deferred("render_water")
func render_water():
	var editor=load("res://HabitatEditor.tscn").instantiate(); root.add_child(editor)
	await process_frame
	editor.load_path(ProjectSettings.globalize_path("res://../../Assets/Habitats/water-study.json"))
	editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	editor.target=Vector3(4,.8,-4); editor.distance=17; editor.yaw=.65; editor.pitch=.65; editor.update_camera()
	for frame in range(8): await process_frame
	await RenderingServer.frame_post_draw
	editor.viewport.get_texture().get_image().save_png("res://docs/water-study.png")
	editor.load_path(ProjectSettings.globalize_path("res://../../Assets/Habitats/water-garden.json"))
	editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	editor.target=Vector3(4,.7,-4); editor.yaw=.65; editor.pitch=.55; editor.distance=17; editor.update_camera()
	for frame in range(6): await process_frame
	await RenderingServer.frame_post_draw
	editor.viewport.get_texture().get_image().save_png("res://docs/water-garden.png")
	editor.choose_sky(HabitatAtmosphere.preset("starry_night"))
	for frame in range(6): await process_frame
	await RenderingServer.frame_post_draw
	editor.viewport.get_texture().get_image().save_png("res://docs/water-night.png")
	# Render a genuine single-cell catalog thumbnail, with a submerged stone floor.
	editor.new_document(); editor.document.data.terrain=[{"cell":[0,0,0],"asset":"water_teal"},{"cell":[0,-1,0],"asset":"terrain_limestone"}]; editor.rebuild()
	editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	editor.target=Vector3(0,.25,0); editor.distance=3.2; editor.pitch=.45; editor.update_camera()
	for frame in range(6): await process_frame
	await RenderingServer.frame_post_draw
	var image=editor.viewport.get_texture().get_image(); image.resize(192,128,Image.INTERPOLATE_LANCZOS); image.save_png("res://assets/thumbnails/water_teal.png")
	editor.load_path(ProjectSettings.globalize_path("res://../../Assets/Habitats/water-garden.json"))
	editor.water_visible=true; editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	editor.target=Vector3(4,.7,-4); editor.distance=17; editor.pitch=.55; editor.update_camera()
	for i in range(editor.category.item_count):
		if editor.category.get_item_text(i)=="Water": editor.category.select(i)
	editor.active_asset=HabitatWater.ID; editor.set_tool("Select"); editor.selected=["t:3,0,1"]; editor.refresh_selection(); editor.refresh_palette()
	for frame in range(6): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://docs/water-editor.png")
	editor.queue_free(); await process_frame; await process_frame; quit()
