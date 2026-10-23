extends SceneTree
func _initialize():
	call_deferred("render_views")

func render_views():
	var editor=load("res://HabitatEditor.tscn").instantiate(); root.add_child(editor)
	await process_frame
	editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	for angle in [["underside",-1.1],["birdseye",1.52]]:
		editor.pitch=angle[1]; editor.update_camera()
		for frame in range(4): await process_frame
		await RenderingServer.frame_post_draw
		editor.viewport.get_texture().get_image().save_png("res://docs/camera_"+angle[0]+".png")
	editor.queue_free()
	await process_frame
	await process_frame
	quit()
