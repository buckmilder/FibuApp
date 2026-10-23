class_name HabitatRegistry
extends RefCounted
var assets: Dictionary = {}
var scenes: Dictionary = {}
var materials: Dictionary = {}

func _init():
	var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://assets/catalog.json"))
	for asset in parsed.assets:
		assets[asset.id] = asset
		if asset.kind == "prop": scenes[asset.id] = load(asset.godot)

func instance(id: String) -> Node3D:
	if scenes.has(id) and scenes[id]: return scenes[id].instantiate()
	var placeholder = MeshInstance3D.new()
	placeholder.mesh = BoxMesh.new()
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color.MAGENTA
	placeholder.material_override = mat
	return placeholder

func material_for(id: String, face: String) -> Material:
	var cache_key = id + face
	if materials.has(cache_key): return materials[cache_key]
	var theme = assets.get(id,{}).get("theme","meadow")
	var mat = StandardMaterial3D.new()
	mat.albedo_texture = load("res://assets/textures/%s_%s.png" % [theme,face])
	mat.normal_enabled = true
	mat.normal_texture = load("res://assets/textures/%s_%s_normal.png" % [theme,face])
	mat.normal_scale = .4
	mat.roughness_texture = load("res://assets/textures/%s_%s_roughness.png" % [theme,face])
	mat.roughness = .9
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	materials[cache_key] = mat
	return mat
