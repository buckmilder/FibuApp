var camera = IslandCamera()
let initialPitch = IslandCamera.pitch
for zoom in [1.0, 1.25, 1.8, 2.4] {
    camera.setZoom(zoom)
    for _ in 0..<72 {
        camera.rotate(horizontalPoints: 50)
        let offset = camera.position - camera.target
        let radius = sqrt(offset.x * offset.x + offset.z * offset.z)
        precondition(abs(radius - 12) < 0.0001)
        precondition(abs(-atan2(offset.y, radius) - initialPitch) < 0.0001, "Orbit/zoom must preserve POV elevation")
        for size in [(393.0, 852.0), (440.0, 956.0), (900.0, 650.0)] {
            precondition(abs(camera.scale(width: size.0, height: size.1) * zoom - max(7.8, 5.5 * size.1 / size.0)) < 0.0001, "Layout must preserve selected zoom")
        }
    }
}
camera.setZoom(100)
precondition(camera.zoom == IslandCamera.maximumZoom)
camera.setZoom(0.01)
precondition(camera.zoom == IslandCamera.minimumZoom)
camera.setZoom(.nan)
precondition(camera.zoom == 1)
camera.reset()
precondition(camera.zoom == 1 && camera.yaw == 0)
precondition(abs(camera.position.y - 10) < 0.0001)
print("PASS: fixed camera elevation across 288 orbit/zoom positions, phone/Duo framing, zoom limits and reset")
