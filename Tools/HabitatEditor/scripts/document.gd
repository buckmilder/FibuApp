class_name HabitatDocument
extends RefCounted

const VERSION = 1
var data: Dictionary
var error = ""
var asset_catalog: Dictionary = {}

func _init():
	data = fresh()
	for asset in JSON.parse_string(FileAccess.get_file_as_string("res://assets/catalog.json")).assets: asset_catalog[asset.id]=asset

static func fresh() -> Dictionary:
	return {"format":"fibu-habitat", "version":VERSION, "id":new_id(), "name":"Untitled habitat", "grid":{"width":9,"depth":9,"cell_size":1.0}, "coordinates":"Y-up meters; cell [x,layer,row] maps to [x,layer,-row]; cell bottom Y=layer; X/Z centered", "terrain":[], "objects":[], "water_styles":{}, "spawn":[4,1.15,-0.5], "environment":HabitatAtmosphere.preset("sunny_highlands")}

static func new_id() -> String:
	return Crypto.new().generate_random_bytes(12).hex_encode()

static func finite_number(v) -> bool:
	return (v is float or v is int) and is_finite(float(v))

static func vector_valid(v, count: int = 3) -> bool:
	if not v is Array or v.size() != count:
		return false
	for n in v:
		if not finite_number(n):
			return false
	return true

static func key(cell: Array) -> String:
	return "%d,%d,%d" % [cell[0],cell[1],cell[2]]

func validate(candidate, catalog: Dictionary) -> String:
	if not candidate is Dictionary:
		return "Expected a habitat JSON object."
	if candidate.get("format") != "fibu-habitat" or candidate.get("version") != VERSION:
		return "Unsupported habitat format/version. Original file was not changed."
	if not candidate.get("id") is String or not candidate.get("name") is String:
		return "Habitat ID and name must be strings."
	var grid = candidate.get("grid", {})
	if not grid is Dictionary or not finite_number(grid.get("width")) or not finite_number(grid.get("depth")) or not finite_number(grid.get("cell_size")):
		return "Missing grid dimensions."
	if grid.width < 1 or grid.depth < 1 or grid.width != floor(grid.width) or grid.depth != floor(grid.depth) or grid.cell_size <= 0:
		return "Grid dimensions must be positive integers; cell size must be positive."
	if not is_equal_approx(float(grid.cell_size),1.0):
		return "This asset catalog uses 1-meter cells. Rescaling catalogs is not implemented."
	if not candidate.get("terrain") is Array or not candidate.get("objects") is Array or not vector_valid(candidate.get("spawn")):
		return "Missing terrain, objects, or finite spawn vector."
	var sky_error=HabitatAtmosphere.validate(candidate.get("environment",{}))
	if not sky_error.is_empty(): return sky_error
	var styles=candidate.get("water_styles",{})
	if not styles is Dictionary: return "Water styles must be an object."
	for style in styles.values():
		var water_error=HabitatWater.validate_style(style)
		if not water_error.is_empty(): return water_error
	var occupied = {}
	var ids = {}
	for cell in candidate.terrain:
		if not cell is Dictionary or not vector_valid(cell.get("cell")) or not cell.get("asset") is String:
			return "Invalid terrain cell."
		for n in cell.cell:
			if n != floor(n): return "Terrain coordinates must be integers."
		if cell.cell[0] < 0 or cell.cell[0] >= grid.width or cell.cell[2] < 0 or cell.cell[2] >= grid.depth:
			return "Terrain lies outside horizontal bounds."
		var k = key(cell.cell)
		if occupied.has(k): return "Duplicate terrain cell: " + k
		occupied[k] = true
		if catalog.has(cell.asset) and not catalog[cell.asset].kind in ["terrain","water"]: return "Prop ID used as terrain."
		if cell.has("water_style") and not cell.water_style is String: return "Water style identifier must be a string."
	for obj in candidate.objects:
		if not obj is Dictionary or not obj.get("id") is String or not obj.get("asset") is String:
			return "Invalid object identifier."
		if ids.has(obj.id): return "Duplicate object instance ID."
		ids[obj.id] = true
		if not vector_valid(obj.get("position")) or not vector_valid(obj.get("rotation")) or not vector_valid(obj.get("scale")):
			return "Object transforms must contain finite three-component vectors."
		for n in obj.scale:
			if n <= 0: return "Object scale must be positive."
		if obj.has("solid") and not obj.solid is bool: return "Solid flag must be boolean."
		if obj.get("solid",false):
			if not vector_valid(obj.get("dimensions")): return "Solid object needs collision dimensions."
			for n in obj.dimensions:
				if n <= 0: return "Collision dimensions must be positive."
		if obj.has("properties") and not obj.properties is Dictionary: return "Object properties must be an object."
		if catalog.has(obj.asset) and catalog[obj.asset].kind != "prop": return "Terrain ID used as prop."
	return ""

func load_file(path: String, catalog: Dictionary) -> bool:
	error = ""
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		error = "Could not open " + path
		return false
	var parser = JSON.new()
	if parser.parse(f.get_as_text()) != OK:
		error = "JSON line %d: %s" % [parser.get_error_line(),parser.get_error_message()]
		return false
	var candidate = parser.data
	error = validate(candidate,catalog)
	if not error.is_empty(): return false
	data = candidate.duplicate(true)
	return true

func save_file(path: String, catalog: Dictionary) -> bool:
	error = validate(data,catalog)
	if not error.is_empty(): return false
	var temp = path + ".tmp"
	var f = FileAccess.open(temp,FileAccess.WRITE)
	if not f:
		error = "Cannot write " + temp
		return false
	f.store_string(JSON.stringify(data,"\t") + "\n")
	f.flush()
	var write_error = f.get_error()
	f.close()
	if write_error != OK:
		error = "Write failed; original file preserved."
		return false
	# Same-directory rename replaces the old file atomically on macOS/Linux.
	if DirAccess.rename_absolute(temp,path) != OK:
		error = "Could not replace file; original preserved and temporary file retained."
		return false
	return true

func terrain_map() -> Dictionary:
	var result = {}
	for t in data.terrain: result[key(t.cell)] = t
	return result

func missing_assets(catalog: Dictionary) -> Array:
	var missing = []
	for item in data.terrain + data.objects:
		if not catalog.has(item.asset) and not missing.has(item.asset): missing.append(item.asset)
	return missing

func can_place(asset: Dictionary, position: Vector3, rotation_y: float, size: Vector3, ignore_ids: Array = []) -> String:
	var grid = data.grid
	var rotations=asset.get("rotations",[])
	if not rotations.is_empty():
		var allowed=false
		for r in rotations:
			if is_equal_approx(fposmod(rotation_y,360),fposmod(r,360)): allowed=true
		if not allowed: return "Rotation is not allowed for this asset."
	size = placement_size(asset,size)
	var half = size * .5
	if asset.get("solid",false) or asset.get("occupies_grid",false):
		var turns = posmod(roundi(rotation_y / 90.0),4)
		if turns % 2: half = Vector3(half.z,half.y,half.x)
		if position.x-half.x < -.5001 or position.x+half.x > grid.width-.4999 or position.z-half.z < -grid.depth+.4999 or position.z+half.z > .5001:
			return "Solid footprint exceeds habitat boundary."
		var box = AABB(Vector3(position.x-half.x+.01,position.y+.01,position.z-half.z+.01),Vector3(half.x*2-.02,size.y-.02,half.z*2-.02))
		for t in data.terrain:
			if ignore_ids.has("t:"+key(t.cell)): continue
			var p = Vector3(t.cell[0]-.5,t.cell[1],-t.cell[2]-.5)
			if box.intersects(AABB(p,Vector3.ONE)): return "Occupied by terrain."
		for obj in data.objects:
			if ignore_ids.has(obj.id): continue
			# Solid custom assets store a canonical collision size; unknown assets are preserved.
			var definition=asset_catalog.get(obj.asset,obj)
			if not definition.get("occupies_grid",false) and not definition.get("solid",false): continue
			var dims=definition.get("dimensions",[1,1,1])
			var d = placement_size(definition,Vector3(dims[0],dims[1],dims[2]))*Vector3(obj.scale[0],obj.scale[1],obj.scale[2])
			if posmod(roundi(obj.rotation[1]/90),2): d = Vector3(d.z,d.y,d.x)
			var p = Vector3(obj.position[0],obj.position[1],obj.position[2])
			if box.intersects(AABB(p-Vector3(d.x/2,0,d.z/2),d)): return "Occupied by solid object."
	else:
		if position.x < -.5 or position.x > grid.width-.5 or position.z < -grid.depth+.5 or position.z > .5:
			return "Object anchor exceeds habitat boundary."
	return ""

# Footprints are placement reservations, independent of Fibu's movement blockers.
static func placement_size(asset: Dictionary, visual_size: Vector3) -> Vector3:
	var footprint=asset.get("footprint",[])
	if asset.get("placement_grid",false) and footprint.size()==2:
		return Vector3(footprint[0],visual_size.y,footprint[1])
	return visual_size

static func snap_prop(asset: Dictionary, position: Vector3, yaw: float) -> Vector3:
	if not asset.get("placement_grid",false): return position
	var size=placement_size(asset,Vector3.ONE)
	if posmod(roundi(yaw/90),2): size=Vector3(size.z,size.y,size.x)
	# Even-width assets sit BETWEEN cell centers, covering exact whole tiles.
	var offset=Vector3(.5 if roundi(size.x)%2==0 else 0,0,.5 if roundi(size.z)%2==0 else 0)
	return (position-offset).snapped(Vector3.ONE)+offset

func blocked_cells() -> Array:
	var result=[]
	for obj in data.objects:
		var asset=asset_catalog.get(obj.asset,obj)
		if not asset.get("blocks_movement",false): continue
		var local_size=placement_size(asset,Vector3.ONE)*Vector3(obj.scale[0],obj.scale[1],obj.scale[2])
		var angle=deg_to_rad(obj.rotation[1]); var c=abs(cos(angle)); var s=abs(sin(angle))
		var size=Vector3(local_size.x*c+local_size.z*s,local_size.y,local_size.x*s+local_size.z*c)
		for x in range(floori(obj.position[0]-size.x/2+.50001),ceili(obj.position[0]+size.x/2+.49999)):
			for row in range(floori(-obj.position[2]-size.z/2+.50001),ceili(-obj.position[2]+size.z/2+.49999)):
				var cell=[x,roundi(obj.position[1]),row]
				if not result.has(cell): result.append(cell)
	return result
