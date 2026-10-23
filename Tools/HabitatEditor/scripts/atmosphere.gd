class_name HabitatAtmosphere
extends RefCounted

signal settings_changed(settings: Dictionary)

const PRESETS = ["sunny_highlands","golden_sunset","starry_night","misty_forest","desert_haze","frozen_twilight"]
const NAMES = ["Sunny Highlands","Golden Sunset","Starry Night","Misty Forest","Desert Haze","Frozen Twilight"]
const COLORS = [
	["368ab1","bce3cf","426b67","326343","fff7e5","fff4d8","c4dce4","aecfc6"],
	["685eac","f5ba75","77658d","6e5579","ffd2b2","ffb775","bd99b9","e5b28b"],
	["101834","3b4868","17253c","162c3b","7f92b7","a0b9ef","697ba8","344564"],
	["486f79","afc9b8","395d58","355d4e","d7e2cf","d7e2d0","a6c5b4","a5bdb1"],
	["c8ab8e","f3d5a5","a98366","ac7858","fff1d7","ffdfa2","dbc3a7","d9b58d"],
	["3e5486","abbcda","526d88","617c99","e0edfa","bacff5","9bafce","aebfd6"]
]
var environment_node: WorldEnvironment
var sunlight: DirectionalLight3D
var material: ShaderMaterial
var phase = 0.0
var motion_elapsed = 0.0
var last_settings = {}
var art_root = ""
var panorama_cache = {}
var missing_panorama = ""

static func preset(id: String) -> Dictionary:
	var index=PRESETS.find(id)
	if index<0: index=0
	var c=COLORS[index]
	return {"version":1,"preset":PRESETS[index],"name":NAMES[index],"sky_top":c[0],"horizon":c[1],"lower_sky":c[2],"landscape_tint":c[3],"cloud_color":c[4],"sun_color":c[5],"ambient_color":c[6],"fog_color":c[7],"sun_azimuth":[-30,65,-65,20,45,-55][index],"sun_elevation":[52,16,25,45,35,12][index],"sun_energy":[.65,.55,.16,.32,.65,.28][index],"ambient_energy":[.35,.35,.23,.5,.4,.4][index],"cloud_density":[.55,.45,.16,.75,.22,.45][index],"cloud_softness":.55,"cloud_motion":false,"cloud_speed":.015,"fog_density":[.001,.002,.002,.009,.006,.004][index],"fog_height":0.0,"fog_height_density":.006 if index==3 else 0.0,"landscape_visible":true,"landscape_kind":[0,0,0,1,2,3][index],"background_rotation":0.0,"stars":1.0 if index==2 else 0.0,"moon":1.0 if index==2 else 0.0,"haze":[.3,.4,.3,.8,.65,.5][index],"horizon_offset":.55,"panorama":""}

static func resolved(raw) -> Dictionary:
	var result=preset(raw.get("preset","sunny_highlands") if raw is Dictionary else "sunny_highlands")
	if raw is Dictionary: result.merge(raw,true)
	return result

static func validate(raw) -> String:
	if not raw is Dictionary: return "Sky settings must be an object."
	if raw.is_empty(): return ""
	if raw.get("version",1)!=1: return "Unsupported atmosphere version."
	for key in ["name","preset"]:
		if raw.has(key) and not raw[key] is String: return "Sky name and preset must be strings."
	if raw.has("landscape_kind") and (not HabitatDocument.finite_number(raw.landscape_kind) or raw.landscape_kind!=floor(raw.landscape_kind)): return "Landscape kind must be an integer."
	for key in ["sky_top","horizon","lower_sky","landscape_tint","cloud_color","sun_color","ambient_color","fog_color"]:
		if raw.has(key) and (not raw[key] is String or not Color.html_is_valid(raw[key])): return "Invalid sky color: "+key
	var limits={"sun_azimuth":[-360,360],"sun_elevation":[-90,90],"sun_energy":[0,4],"ambient_energy":[0,2],"cloud_density":[0,1],"cloud_softness":[0,1],"cloud_speed":[0,.1],"fog_density":[0,.05],"fog_height":[-100000,100000],"fog_height_density":[0,.1],"background_rotation":[-360,360],"stars":[0,2],"moon":[0,1],"haze":[0,1],"landscape_kind":[0,3],"horizon_offset":[0,1]}
	for key in limits:
		if raw.has(key):
			if not HabitatDocument.finite_number(raw[key]) or raw[key]<limits[key][0] or raw[key]>limits[key][1]: return "Invalid sky setting: "+key
	for key in ["cloud_motion","landscape_visible"]:
		if raw.has(key) and not raw[key] is bool: return "Invalid sky flag: "+key
	if raw.has("panorama"):
		if not raw.panorama is String or raw.panorama.is_absolute_path() or ".." in raw.panorama.split("/"): return "Panorama must be a relative habitat-content path."
	return ""

func _init(world: Node3D, content_root: String):
	art_root=content_root
	environment_node=WorldEnvironment.new(); world.add_child(environment_node)
	sunlight=DirectionalLight3D.new(); sunlight.shadow_enabled=true; sunlight.directional_shadow_max_distance=80; world.add_child(sunlight)
	material=ShaderMaterial.new(); material.shader=load("res://assets/skies/stylized.gdshader")

func apply(raw: Dictionary):
	var settings=resolved(raw)
	if settings==last_settings: return
	last_settings=settings.duplicate(true)
	missing_panorama=""
	var env=environment_node.environment
	if env==null: env=Environment.new()
	env.background_mode=Environment.BG_SKY
	var sky=env.sky
	if sky==null: sky=Sky.new()
	var background: Material = null
	env.sky_rotation=Vector3.ZERO
	sky.radiance_size=Sky.RADIANCE_SIZE_32; sky.process_mode=Sky.PROCESS_MODE_INCREMENTAL
	var panorama_path=settings.get("panorama","")
	if not panorama_path.is_empty():
		if not panorama_cache.has(panorama_path):
			var path=art_root.path_join(panorama_path)
			if FileAccess.file_exists(path):
				var image=Image.load_from_file(path)
				if image: panorama_cache[panorama_path]=ImageTexture.create_from_image(image)
			if not panorama_cache.has(panorama_path): missing_panorama=panorama_path
		if panorama_cache.has(panorama_path):
			var panorama=PanoramaSkyMaterial.new(); panorama.panorama=panorama_cache[panorama_path]; background=panorama
			env.sky_rotation.y=deg_to_rad(settings.background_rotation)
	if background==null:
		for key in ["landscape_visible","cloud_density","cloud_softness","stars","moon","haze","horizon_offset"]: material.set_shader_parameter(key,settings[key])
		material.set_shader_parameter("landscape_kind",int(settings.landscape_kind))
		for pair in [["sky_top","top_color"],["horizon","horizon_color"],["lower_sky","lower_color"],["landscape_tint","landscape_tint"],["cloud_color","cloud_color"]]: material.set_shader_parameter(pair[1],Color(settings[pair[0]]))
		material.set_shader_parameter("background_rotation",deg_to_rad(settings.background_rotation)); material.set_shader_parameter("cloud_phase",phase)
		background=material
	sky.sky_material=background
	env.sky=sky; env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color=Color(settings.ambient_color); env.ambient_light_energy=settings.ambient_energy
	env.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.fog_enabled=settings.fog_density>0 or settings.fog_height_density>0
	env.fog_light_color=Color(settings.fog_color); env.fog_density=settings.fog_density; env.fog_height=settings.fog_height; env.fog_height_density=settings.fog_height_density; env.fog_sky_affect=.15
	environment_node.environment=env
	sunlight.rotation_degrees=Vector3(-settings.sun_elevation,settings.sun_azimuth,0); sunlight.light_color=Color(settings.sun_color); sunlight.light_energy=settings.sun_energy
	settings_changed.emit(settings)

func tick(delta: float):
	if last_settings.get("cloud_motion",false) and last_settings.get("panorama","").is_empty():
		motion_elapsed+=delta
		if motion_elapsed<.1: return
		phase+=motion_elapsed*last_settings.get("cloud_speed",.015)
		motion_elapsed=0.0
		material.set_shader_parameter("cloud_phase",phase)
