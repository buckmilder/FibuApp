extends SceneTree
func _initialize(): call_deferred("render_props")
func render_props():
	var editor=load("res://HabitatEditor.tscn").instantiate(); root.add_child(editor)
	await process_frame
	editor.load_path(ProjectSettings.globalize_path("res://../../Assets/Habitats/tile-footprints-study.json"))
	editor.set_tool("Select"); editor.selected=["footprint-prop-3"]; editor.refresh_selection()
	editor.target=Vector3(4,1,-4); editor.distance=17; editor.pitch=.68; editor.yaw=.5; editor.update_camera()
	for obj in editor.document.data.objects:
		var asset=editor.registry.assets[obj.asset]; var holder=Node3D.new(); editor.world.add_child(holder); holder.position=editor.as_vector(obj.position); holder.rotation_degrees=editor.as_vector(obj.rotation)
		var size=HabitatDocument.placement_size(asset,Vector3(1,.04,1))
		editor.wire_box(AABB(Vector3(-size.x/2,.035,-size.z/2),size),Color("f38f82") if asset.blocks_movement else Color("86edab"),holder)
	for frame in range(8): await process_frame
	await RenderingServer.frame_post_draw
	editor.viewport.get_texture().get_image().save_png("res://docs/prop-footprints.png")
	editor.queue_free(); await process_frame; quit()
