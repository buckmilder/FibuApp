import Foundation

/// Orbit keeps a fixed elevation and roll; zoom changes framing, never perspective.
struct IslandCamera {
    static let minimumZoom = 1.0
    static let maximumZoom = 2.4
    static let pitch = -atan2(Float(11.4), Float(12))
    private(set) var zoom = 1.0
    private(set) var yaw: Float = 0

    mutating func setZoom(_ value: Double) {
        guard value.isFinite else { return }
        zoom = min(Self.maximumZoom, max(Self.minimumZoom, value))
    }
    mutating func rotate(horizontalPoints: Double) {
        guard horizontalPoints.isFinite else { return }
        yaw = (yaw + Float(horizontalPoints * 0.006)).truncatingRemainder(dividingBy: 2 * .pi)
    }
    mutating func reset() { zoom = 1; yaw = 0 }

    var target: SIMD3<Float> {
        // Keep the island above the activity card as the orthographic view tightens.
        SIMD3(0, 0.6 - 2 / Float(zoom), 0)
    }
    var position: SIMD3<Float> {
        target + SIMD3(sin(yaw) * 12, 11.4, cos(yaw) * 12)
    }
    func scale(width: Double, height: Double) -> Double {
        guard width > 0, height > 0 else { return 11.8 / zoom }
        return max(7.8, 5.5 * height / width) / zoom
    }
}
