extends SceneTree

func _initialize():
	call_deferred("render_presets")

func render_presets():
	var editor=load("res://HabitatEditor.tscn").instantiate()
	root.add_child(editor)
	await process_frame
	await process_frame
	editor.show_grid=false; editor.rebuild_grid(); editor.spawn_marker.visible=false
	var presets=[]
	for id in HabitatAtmosphere.PRESETS: presets.append(HabitatAtmosphere.preset(id))
	var definitions=FileAccess.open("res://assets/skies/presets.json",FileAccess.WRITE); definitions.store_string(JSON.stringify({"version":1,"presets":presets},"\t")+"\n"); definitions.close()
	for id in HabitatAtmosphere.PRESETS:
		editor.choose_sky(HabitatAtmosphere.preset(id))
		for frame in range(12): await process_frame
		await RenderingServer.frame_post_draw
		var image=editor.viewport.get_texture().get_image()
		image.save_png("res://docs/sky_"+id+".png")
		image.resize(256,160,Image.INTERPOLATE_LANCZOS)
		image.save_png("res://assets/skies/"+id+".png")
		print("Rendered ",id)
	quit()
