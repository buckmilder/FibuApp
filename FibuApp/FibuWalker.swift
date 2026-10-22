import SceneKit
import simd

/// First-pass procedural idle/walk clips for the supplied USDZ skeleton.
/// The source asset is never modified; the imported wave is replaced in memory.
final class FibuWalker {
    private let actor: SCNNode
    private let body: SCNNode
    private var joints: [(node: SCNNode, rest: simd_quatf, amplitude: Float, phase: Float, knee: Bool)] = []
    private var marker: SCNNode?

    init(actor: SCNNode) {
        self.actor = actor
        self.body = actor.childNode(withName: "FibuMotion", recursively: true) ?? actor
        let channels: [(String, Float, Float, Bool)] = [
            ("Thigh_L", 0.38, 0, false), ("Thigh_R", 0.38, .pi, false),
            ("Calf_L", 0.48, .pi, true), ("Calf_R", 0.48, 0, true),
            ("Bicep_L", 0.22, .pi, false), ("Bicep_R", 0.22, 0, false)
        ]
        for (name, amplitude, phase, knee) in channels {
            if let node = body.childNode(withName: name, recursively: true) {
                joints.append((node, node.simdOrientation, amplitude, phase, knee))
            }
        }
        idle()
    }

    func walk(to requestedPoint: SIMD2<Float>) {
        let target = IslandMovement.destination(requestedPoint)
        let current = actor.presentation.position
        let start = SIMD2(current.x, current.z)
        guard IslandMovement.distance(from: start, to: target) > 0.08 else { return }
        let currentHeading = actor.presentation.eulerAngles.y
        actor.removeAction(forKey: "travel")
        actor.removeAction(forKey: "turn")
        actor.position = current
        actor.eulerAngles.y = currentHeading
        let turn = SCNAction.rotateTo(x: 0, y: CGFloat(IslandMovement.heading(from: start, to: target)), z: 0, duration: 0.2, usesShortestUnitArc: true)
        turn.timingMode = .easeInEaseOut
        actor.runAction(turn, forKey: "turn")
        showDestination(target)
        startWalking()
        let move = SCNAction.move(to: SCNVector3(target.x, 0.29, target.y), duration: IslandMovement.duration(from: start, to: target))
        move.timingMode = .linear
        actor.runAction(.sequence([move, .run { [weak self] _ in self?.arrive() }]), forKey: "travel")
    }

    private func startWalking() {
        body.removeAction(forKey: "pose")
        body.removeAction(forKey: "idle")
        guard body.action(forKey: "walk") == nil else { return }
        let cycle = SCNAction.customAction(duration: 0.68) { [weak self] _, elapsed in
            guard let self else { return }
            let phase = Float(elapsed) / 0.68 * 2 * Float.pi
            for joint in self.joints {
                let wave = sin(phase + joint.phase)
                let angle = (joint.knee ? max(0, wave) : wave) * joint.amplitude
                joint.node.simdOrientation = joint.rest * simd_quatf(angle: angle, axis: SIMD3(1, 0, 0))
            }
            self.body.position.y = 0.045 * (1 - cos(phase * 2))
            self.body.eulerAngles.z = sin(phase) * 0.035
        }
        body.runAction(.repeatForever(cycle), forKey: "walk")
    }

    private func arrive() {
        body.removeAction(forKey: "walk")
        let rotations = joints.map { $0.node.simdOrientation }
        let height = body.position.y
        let tilt = body.eulerAngles.z
        let settle = SCNAction.customAction(duration: 0.16) { [weak self] _, elapsed in
            guard let self else { return }
            let progress = min(Float(elapsed) / 0.16, 1)
            for (index, joint) in self.joints.enumerated() {
                joint.node.simdOrientation = simd_slerp(rotations[index], joint.rest, progress)
            }
            self.body.position.y = height * (1 - progress)
            self.body.eulerAngles.z = tilt * (1 - progress)
        }
        body.runAction(.sequence([settle, .run { [weak self] _ in self?.idle() }]), forKey: "pose")
        marker?.runAction(.sequence([.fadeOut(duration: 0.25), .removeFromParentNode()]))
        marker = nil
    }

    private func idle() {
        body.runAction(.repeatForever(.sequence([
            .moveBy(x: 0, y: 0.018, z: 0, duration: 1.2),
            .moveBy(x: 0, y: -0.018, z: 0, duration: 1.2)
        ])), forKey: "idle")
    }

    private func showDestination(_ point: SIMD2<Float>) {
        marker?.removeFromParentNode()
        let ring = SCNTorus(ringRadius: 0.18, pipeRadius: 0.025)
        let material = SCNMaterial()
        material.diffuse.contents = UIColor.white
        material.emission.contents = UIColor.white.withAlphaComponent(0.3)
        ring.materials = [material]
        let node = SCNNode(geometry: ring)
        node.position = SCNVector3(point.x, 0.32, point.y)
        actor.parent?.addChildNode(node)
        marker = node
    }

    static func preparePose(_ root: SCNNode) {
        root.enumerateChildNodes { node, _ in
            for key in node.animationKeys {
                if let player = node.animationPlayer(forKey: key) {
                    applyFirstFrame(CAAnimation(scnAnimation: player.animation), to: node)
                }
            }
            node.removeAllAnimations()
        }
    }

    private static func applyFirstFrame(_ animation: CAAnimation, to root: SCNNode) {
        if let group = animation as? CAAnimationGroup {
            for child in group.animations ?? [] { applyFirstFrame(child, to: root) }
        } else if let channel = animation as? CAKeyframeAnimation,
                  let path = channel.keyPath, let value = channel.values?.first as? NSValue {
            let parts = path.split(separator: ".")
            let node = parts.count == 2 ? root.childNode(withName: String(parts[0].dropFirst()), recursively: true) : root
            switch parts.last {
            case "position": node?.position = value.scnVector3Value
            case "orientation": node?.orientation = value.scnVector4Value
            case "scale": node?.scale = value.scnVector3Value
            case "eulerAngles": node?.eulerAngles = value.scnVector3Value
            default: break
            }
        }
    }
}
