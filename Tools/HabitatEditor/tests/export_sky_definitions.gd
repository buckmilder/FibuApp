extends SceneTree
func _initialize():
	var presets=[]
	for id in HabitatAtmosphere.PRESETS: presets.append(HabitatAtmosphere.preset(id))
	var file=FileAccess.open("res://assets/skies/presets.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"version":1,"presets":presets},"\t")+"\n"); file.close()
	quit()
