import Foundation

/// Movement stays within a convex ellipse inset from the irregular grass edge.
/// A straight segment between two valid positions therefore stays on the island.
enum IslandMovement {
    static let radiusX: Float = 3.05
    static let radiusZ: Float = 2.48
    static let speed: Float = 1.15
    static func destination(_ point: SIMD2<Float>) -> SIMD2<Float> {
        guard point.x.isFinite, point.y.isFinite else { return .zero }
        let distance = sqrt(pow(point.x / radiusX, 2) + pow(point.y / radiusZ, 2))
        return distance > 1 ? point / distance : point
    }
    static func distance(from start: SIMD2<Float>, to end: SIMD2<Float>) -> Float {
        let delta = end - start
        return sqrt(delta.x * delta.x + delta.y * delta.y)
    }
    static func duration(from start: SIMD2<Float>, to end: SIMD2<Float>) -> Double {
        Double(distance(from: start, to: end) / speed)
    }
    static func heading(from start: SIMD2<Float>, to end: SIMD2<Float>) -> Float {
        let delta = end - start
        return atan2(delta.x, delta.y)
    }
}
