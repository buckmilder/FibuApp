extends SceneTree
func _initialize(): call_deferred("render_study")
func render_study():
	var editor=load("res://HabitatEditor.tscn").instantiate();root.add_child(editor);await process_frame
	editor.load_path(ProjectSettings.globalize_path("res://../../Assets/Habitats/soft-terrain-study.json"))
	editor.show_grid=false;editor.rebuild_grid();editor.spawn_marker.visible=false
	editor.target=Vector3(4,1,-4);editor.distance=17;editor.yaw=.6;editor.pitch=.6;editor.update_camera()
	for i in range(editor.category.item_count):
		if editor.category.get_item_text(i)=="Terrain":editor.category.select(i)
	editor.active_asset="terrain_meadow";editor.set_tool("Select");editor.refresh_palette()
	for frame in range(12):await process_frame
	await RenderingServer.frame_post_draw
	var dest=ProjectSettings.globalize_path("res://../../Assets/Handoff/SoftTerrain/")
	editor.viewport.get_texture().get_image().save_png(dest+"builder-study.png")
	root.get_texture().get_image().save_png(dest+"editor.png")
	editor.queue_free();await process_frame;quit()
