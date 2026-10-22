func near(_ actual: Float, _ expected: Float, _ message: String) {
    precondition(abs(actual - expected) < 0.0001, message)
}
near(IslandMovement.destination(SIMD2(1, -1)).x, 1, "Interior tap must be unchanged")
near(IslandMovement.destination(SIMD2(100, 0)).x, IslandMovement.radiusX, "East shore clamps safely")
near(IslandMovement.destination(SIMD2(0, -100)).y, -IslandMovement.radiusZ, "North shore clamps safely")
precondition(IslandMovement.destination(SIMD2(.infinity, 0)) == .zero)
near(IslandMovement.heading(from: .zero, to: SIMD2(1, 0)), .pi / 2, "Turn east")
near(IslandMovement.heading(from: .zero, to: SIMD2(-1, 0)), -.pi / 2, "Turn west")
near(IslandMovement.heading(from: .zero, to: SIMD2(0, 1)), 0, "Turn toward camera")
precondition(IslandMovement.duration(from: SIMD2(1, 1), to: SIMD2(1, 1)) == 0)
let retarget = IslandMovement.duration(from: SIMD2(1, 0), to: SIMD2(2, 0))
precondition(abs(retarget - 1 / Double(IslandMovement.speed)) < 0.0001, "Retarget duration must use the current position")
for i in 0..<360 {
    let angle = Float(i) * .pi / 180
    let start = IslandMovement.destination(SIMD2(cos(angle) * 20, sin(angle) * 20))
    let end = IslandMovement.destination(SIMD2(cos(angle + 2.2) * 20, sin(angle + 2.2) * 20))
    for step in 0...20 {
        let p = start + (end - start) * Float(step) / 20
        let ellipse = pow(p.x / IslandMovement.radiusX, 2) + pow(p.y / IslandMovement.radiusZ, 2)
        precondition(ellipse <= 1.0001, "A walk segment must never leave the safe grass area")
    }
}
print("PASS: shoreline bounds, 7,560 path points, headings, zero-distance and mid-walk retarget timing")
