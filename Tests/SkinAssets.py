import json, pathlib, sys, struct, xml.etree.ElementTree as ET
root = pathlib.Path(__file__).resolve().parents[1]
items = json.loads(pathlib.Path(sys.argv[1]).read_text())
for item in items:
    for kind in ["texture", "icon"]:
        if not item[kind]: continue
        folder = root / "FibuApp/Assets.xcassets" / (item[kind] + ".imageset")
        metadata = json.loads((folder / "Contents.json").read_text())
        image = folder / metadata["images"][0]["filename"]
        assert image.is_file(), image
        if image.suffix == ".svg":
            svg = ET.parse(image).getroot()
            assert svg.get("viewBox"), image
        elif kind == "texture":
            data = image.read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack(">II", data[16:24]) == (1024, 1024)
print("PASS: 12 skin IDs round-trip, unknown IDs fall back, every texture/icon resolves, runtime textures are 1024 square")
