import SceneKit
import SwiftUI
import simd

final class WatchIsland: ObservableObject {
    let scene = SCNScene()
    let camera = SCNNode()
    @Published private(set) var isGreeting = false
    private(set) var hasModel = false
    private let actor = SCNNode()
    private let body = SCNNode()
    private var waveClips: [(SCNNode, SCNAnimation)] = []
    private var greetingTask: Task<Void, Never>?

    init() {
        scene.background.contents = UIColor(red: 0.55, green: 0.80, blue: 0.83, alpha: 1)
        camera.camera = SCNCamera()
        camera.camera?.usesOrthographicProjection = true
        camera.camera?.orthographicScale = 2.5
        camera.camera?.zFar = 50
        camera.position = SCNVector3(0, 8.2, 12)
        camera.look(at: SCNVector3(0, 1.2, 0))
        scene.rootNode.addChildNode(camera)
        let ambient = SCNNode()
        ambient.light = SCNLight(); ambient.light?.type = .ambient; ambient.light?.intensity = 700
        scene.rootNode.addChildNode(ambient)
        let sun = SCNNode()
        sun.light = SCNLight(); sun.light?.type = .directional; sun.light?.intensity = 850
        sun.eulerAngles = SCNVector3(-0.9, -0.5, 0)
        scene.rootNode.addChildNode(sun)
        scene.rootNode.addChildNode(land(radius: 3.5, height: 0.35, y: -0.08,
                                       color: UIColor(red: 0.94, green: 0.83, blue: 0.60, alpha: 1)))
        scene.rootNode.addChildNode(land(radius: 3.15, height: 0.20, y: 0.18,
                                       color: UIColor(red: 0.57, green: 0.76, blue: 0.36, alpha: 1)))
        let grassMaterial = material(UIColor(red: 0.35, green: 0.59, blue: 0.25, alpha: 1))
        grassMaterial.isDoubleSided = true
        let blades = SCNGeometry(sources: [SCNGeometrySource(vertices: [
            SCNVector3(-0.05, 0, 0), SCNVector3(-0.03, 0.14, 0), SCNVector3(0.03, 0, 0),
            SCNVector3(0, 0, 0.01), SCNVector3(0.07, 0.11, 0.01), SCNVector3(0.06, 0, 0.01)
        ])], elements: [SCNGeometryElement(indices: [Int32(0), 1, 2, 3, 4, 5], primitiveType: .triangles)])
        blades.materials = [grassMaterial]
        for i in 0..<48 {
            let theta = Float(i) * 2.39996
            let radius = 0.85 + sqrt(Float(i) / 48) * 2.0
            let tuft = SCNNode(geometry: blades)
            tuft.position = SCNVector3(cos(theta) * radius, 0.29, sin(theta) * radius * 0.86)
            tuft.eulerAngles.y = theta
            scene.rootNode.addChildNode(tuft)
        }
        for i in 0..<7 {
            let theta = Float(i) * 2.39996
            let bloom = SCNSphere(radius: 0.045); bloom.segmentCount = 6
            bloom.materials = [material(i % 2 == 0 ? .white : UIColor(red: 1, green: 0.94, blue: 0.65, alpha: 1))]
            let flower = SCNNode(geometry: bloom)
            flower.position = SCNVector3(cos(theta) * 2.3, 0.33, sin(theta) * 1.95)
            scene.rootNode.addChildNode(flower)
        }
        loadFibu()
    }

    private func loadFibu() {
        guard let url = Bundle.main.url(forResource: "Fibu.Watch", withExtension: "scn"),
              let imported = try? SCNScene(url: url, options: [.checkConsistency: true]) else { return }
        imported.rootNode.enumerateChildNodes { node, _ in
            for key in node.animationKeys {
                if let player = node.animationPlayer(forKey: key) {
                    let clip = player.animation
                    self.waveClips.append((node, clip))
                }
            }
            node.removeAllAnimations()
        }
        let model = SCNNode()
        for child in imported.rootNode.childNodes { model.addChildNode(child) }
        let toes = ["Toe_L_end", "Toe_R_end", "Foot_L", "Foot_R"].compactMap {
            model.childNode(withName: $0, recursively: true)?.convertPosition(SCNVector3Zero, to: model).y
        }
        let floor = toes.min() ?? model.boundingBox.min.y
        let top = model.childNode(withName: "Head_end", recursively: true)?.convertPosition(SCNVector3Zero, to: model).y ?? model.boundingBox.max.y
        let scale: Float = 1.85 / max(top - floor, 0.001)
        model.scale = SCNVector3(scale, scale, scale)
        model.position.y = -floor * scale + 0.025
        actor.position.y = 0.29
        actor.eulerAngles.y = -0.32
        body.addChildNode(model); actor.addChildNode(body); scene.rootNode.addChildNode(actor)
        // An inexpensive soft contact shadow, without a dynamic shadow map on Watch.
        let shadow = SCNCylinder(radius: 0.62, height: 0.003)
        shadow.radialSegmentCount = 24
        let shadowMaterial = material(UIColor(red: 0.24, green: 0.43, blue: 0.19, alpha: 0.15))
        shadowMaterial.lightingModel = .constant
        shadow.materials = [shadowMaterial]
        let shadowNode = SCNNode(geometry: shadow)
        shadowNode.scale.z = 0.60; shadowNode.position.y = 0.284
        scene.rootNode.addChildNode(shadowNode)
        hasModel = true
        idle()
    }

    func greet() {
        guard hasModel, !isGreeting else { return }
        isGreeting = true
        body.removeAction(forKey: "idle")
        body.position.y = 0
        let faceViewer = SCNAction.rotateTo(x: 0, y: 0, z: 0, duration: 0.22, usesShortestUnitArc: true)
        faceViewer.timingMode = .easeInEaseOut
        actor.runAction(faceViewer, forKey: "turn")
        greetingTask?.cancel()
        greetingTask = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(220))
            guard !Task.isCancelled, let self else { return }
            for (node, template) in self.waveClips {
                guard let clip = template.copy() as? SCNAnimation else { continue }
                clip.repeatCount = 1; clip.isRemovedOnCompletion = true
                clip.blendInDuration = 0.12; clip.blendOutDuration = 0.18
                let player = SCNAnimationPlayer(animation: clip)
                node.addAnimationPlayer(player, forKey: "hello")
                player.play()
            }
            try? await Task.sleep(for: .milliseconds(1800))
            guard !Task.isCancelled else { return }
            self.finishGreeting()
        }
    }

    func setActive(_ active: Bool) {
        scene.isPaused = !active
        if !active {
            greetingTask?.cancel()
            for (node, _) in waveClips { node.removeAnimation(forKey: "hello") }
            actor.removeAction(forKey: "turn")
            actor.eulerAngles.y = -0.32
            isGreeting = false
            idle()
        }
    }
    private func finishGreeting() {
        for (node, _) in waveClips { node.removeAnimation(forKey: "hello", blendOutDuration: 0.15) }
        actor.runAction(.rotateTo(x: 0, y: -0.32, z: 0, duration: 0.3, usesShortestUnitArc: true), forKey: "turn")
        isGreeting = false
        idle()
    }
    private func idle() {
        body.removeAction(forKey: "idle"); body.position.y = 0
        body.runAction(.repeatForever(.sequence([
            .moveBy(x: 0, y: 0.016, z: 0, duration: 1.3),
            .moveBy(x: 0, y: -0.016, z: 0, duration: 1.3)
        ])), forKey: "idle")
    }
    private func material(_ color: UIColor) -> SCNMaterial {
        let result = SCNMaterial(); result.diffuse.contents = color; result.roughness.contents = 0.9
        return result
    }
    private func land(radius: CGFloat, height: CGFloat, y: Float, color: UIColor) -> SCNNode {
        let shape = SCNCylinder(radius: radius, height: height)
        shape.radialSegmentCount = 48; shape.materials = [material(color)]
        let node = SCNNode(geometry: shape); node.position.y = y; node.scale.z = 0.86
        return node
    }
}
