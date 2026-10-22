import SwiftUI
import SceneKit

struct ContentView: View {
    @State private var steps = 6420
    @State private var resetCamera = 0
    @State private var zoom = 1.0
    @State private var showingSkins = false
    @AppStorage("fibu.selectedSkin") private var selectedSkinID = FibuSkin.original.rawValue
    private let ink = Color(red: 0.14, green: 0.28, blue: 0.23)

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                IslandView(resetCamera: resetCamera, zoom: $zoom, skin: FibuSkin.saved(selectedSkinID)).ignoresSafeArea()
                VStack(spacing: 0) {
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Fibu’s island").font(.system(.title, design: .rounded, weight: .bold))
                            Text("A little place to feel good.").font(.subheadline)
                        }
                        Spacer()
                        HStack(spacing: 8) {
                            Button { showingSkins = true } label: {
                                Image("FibudexIcon").renderingMode(.original).resizable()
                                    .scaledToFit().frame(width: 34, height: 34)
                                    .frame(width: 48, height: 48)
                                    .background(.white.opacity(0.8), in: Circle())
                            }.buttonStyle(.plain)
                                .accessibilityLabel("Open Fibudex")
                                .accessibilityHint("Choose Fibu’s skin")
                                .accessibilityValue(FibuSkin.saved(selectedSkinID).name)
                            Button {} label: {
                                Image("HabitatIcon").renderingMode(.original).resizable()
                                    .scaledToFit().frame(width: 34, height: 34)
                                    .frame(width: 48, height: 48)
                                    .background(.white.opacity(0.8), in: Circle())
                            }.buttonStyle(.plain).disabled(true).opacity(0.65)
                                .accessibilityLabel("Habitat appearance, coming later")
                        }
                    }.padding(.horizontal, 24).padding(.top, 12)
                    Spacer()
                    HStack {
                        Label("Tap to walk · pinch to zoom", systemImage: "hand.tap")
                            .font(.caption.weight(.medium))
                        Spacer()
                        Button { zoom = max(IslandCamera.minimumZoom, zoom / 1.25) } label: {
                            Image(systemName: "minus.magnifyingglass").padding(10)
                        }.accessibilityLabel("Zoom out")
                            .disabled(zoom <= IslandCamera.minimumZoom)
                        Button { zoom = min(IslandCamera.maximumZoom, zoom * 1.25) } label: {
                            Image(systemName: "plus.magnifyingglass").padding(10)
                        }.accessibilityLabel("Zoom in")
                            .disabled(zoom >= IslandCamera.maximumZoom)
                        Button { zoom = 1; resetCamera += 1 } label: {
                            Image(systemName: "viewfinder").font(.title3).padding(12)
                        }.accessibilityLabel("Reset island view")
                    }.padding(.horizontal, 24)
                    activityCard
                        .padding(.horizontal, 18).padding(.bottom, 12)
                }
                .frame(maxWidth: 600)
            }
            .foregroundStyle(ink)
        }
        .preferredColorScheme(.light)
        .sheet(isPresented: $showingSkins) { SkinPicker(selectedID: $selectedSkinID) }
    }

    private var activityCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text("YOUR DAILY MOMENT").font(.system(size: 10, weight: .bold, design: .rounded)).tracking(2)
                Spacer()
                Text("DEMO DATA").font(.system(size: 9, weight: .bold)).tracking(1)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(ink.opacity(0.07), in: Capsule())
            }
            HStack(alignment: .center, spacing: 20) {
                VStack(alignment: .leading, spacing: 5) {
                    Label("Steps today", systemImage: "figure.walk").font(.subheadline.weight(.medium))
                    Text(steps.formatted()).font(.system(size: 38, weight: .bold, design: .rounded)).monospacedDigit()
                        .contentTransition(.numericText())
                    Text("of 10,000 steps").font(.caption).foregroundStyle(.secondary)
                    ProgressView(value: min(Double(steps) / 10000, 1))
                        .tint(Color(red: 0.31, green: 0.61, blue: 0.36)).padding(.top, 6)
                }.frame(maxWidth: .infinity, alignment: .leading)
                VStack(spacing: 8) {
                    ActivityRings(progress: min(Double(steps) / 10000, 1))
                        .frame(width: 86, height: 86)
                    Text("Activity rings").font(.caption.weight(.medium))
                }.accessibilityElement(children: .ignore)
                    .accessibilityLabel("Demo activity rings, move \(Int(min(Double(steps) / 10000, 1) * 100)) percent, exercise 70 percent, stand 83 percent")
            }
            HStack {
                Text("Every little step counts.").font(.caption).foregroundStyle(.secondary)
                Spacer()
                Button {
                    withAnimation(.easeInOut(duration: 0.4)) { steps = steps >= 10000 ? 6420 : min(steps + 500, 10000) }
                } label: {
                    Text(steps >= 10000 ? "Reset demo" : "+ 500 demo steps")
                        .font(.caption.weight(.semibold)).padding(.vertical, 9).padding(.horizontal, 12)
                        .background(Color(red: 0.89, green: 0.94, blue: 0.85), in: Capsule())
                }.buttonStyle(.plain)
            }
        }
        .padding(22)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 28))
        .overlay(RoundedRectangle(cornerRadius: 28).stroke(.white.opacity(0.7), lineWidth: 1))
        .shadow(color: ink.opacity(0.09), radius: 20, y: 8)
    }
}

private struct ActivityRings: View {
    let progress: Double
    var body: some View {
        ZStack {
            ring(.pink, progress, 0)
            ring(Color(red: 0.62, green: 0.87, blue: 0.12), 0.7, 12)
            ring(.cyan, 0.83, 24)
        }
    }
    private func ring(_ color: Color, _ value: Double, _ inset: CGFloat) -> some View {
        ZStack {
            Circle().stroke(color.opacity(0.16), lineWidth: 9)
            Circle().trim(from: 0, to: value)
                .stroke(color, style: StrokeStyle(lineWidth: 9, lineCap: .round))
                .rotationEffect(.degrees(-90))
        }.padding(inset)
    }
}

private struct IslandView: UIViewRepresentable {
    let resetCamera: Int
    @Binding var zoom: Double
    let skin: FibuSkin
    func makeCoordinator() -> Coordinator { Coordinator(zoom: $zoom) }
    func makeUIView(context: Context) -> SCNView {
        let view = IslandSceneView()
        view.backgroundColor = UIColor(red: 0.67, green: 0.85, blue: 0.86, alpha: 1)
        view.antialiasingMode = .multisampling4X
        view.preferredFramesPerSecond = 30
        view.scene = IslandScene.make()
        view.pointOfView = view.scene?.rootNode.childNode(withName: "camera", recursively: true)
        view.isPlaying = true
        view.allowsCameraControl = false
        let drag = UIPanGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.drag(_:)))
        drag.maximumNumberOfTouches = 1
        view.addGestureRecognizer(drag)
        let pinch = UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.pinch(_:)))
        view.addGestureRecognizer(pinch)
        let tap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.tap(_:)))
        tap.require(toFail: drag)
        tap.require(toFail: pinch)
        view.addGestureRecognizer(tap)
        context.coordinator.view = view
        view.onLayout = { [weak coordinator = context.coordinator] in coordinator?.positionCamera() }
        if let actor = view.scene?.rootNode.childNode(withName: "Fibu", recursively: true) {
            context.coordinator.walker = FibuWalker(actor: actor)
            actor.enumerateChildNodes { node, _ in
                for material in node.geometry?.materials ?? [] {
                    context.coordinator.skinMaterials.append((material, material.diffuse.contents))
                }
            }
            context.coordinator.applySkin(skin)
        }
        view.accessibilityLabel = "Fibu on a grassy island. Tap the grass to walk, pinch to zoom, or drag horizontally to rotate."
        return view
    }
    func updateUIView(_ view: SCNView, context: Context) {
        context.coordinator.applySkin(skin)
        context.coordinator.zoom = $zoom
        context.coordinator.camera.setZoom(zoom)
        if context.coordinator.lastReset != resetCamera {
            context.coordinator.lastReset = resetCamera
            context.coordinator.camera.reset()
        }
        context.coordinator.positionCamera()
    }
    class Coordinator: NSObject {
        weak var view: SCNView?
        var lastReset = 0
        var camera = IslandCamera()
        var zoom: Binding<Double>
        var walker: FibuWalker?
        var skinMaterials: [(SCNMaterial, Any?)] = []
        private var appliedSkin: FibuSkin?
        func applySkin(_ skin: FibuSkin) {
            guard appliedSkin != skin else { return }
            let texture = skin.textureName.flatMap { UIImage(named: $0) }
            SCNTransaction.begin()
            SCNTransaction.disableActions = true
            for (material, original) in skinMaterials {
                material.diffuse.contents = texture ?? original
            }
            SCNTransaction.commit()
            appliedSkin = skin
        }
        init(zoom: Binding<Double>) { self.zoom = zoom }
        @objc func tap(_ gesture: UITapGestureRecognizer) {
            guard let view, gesture.state == .ended else { return }
            let hits = view.hitTest(gesture.location(in: view), options: [.categoryBitMask: 2])
            guard let hit = hits.first(where: { $0.worldNormal.y > 0.8 }) else { return }
            walker?.walk(to: SIMD2(hit.worldCoordinates.x, hit.worldCoordinates.z))
        }
        @objc func drag(_ gesture: UIPanGestureRecognizer) {
            camera.rotate(horizontalPoints: Double(gesture.translation(in: view).x))
            gesture.setTranslation(.zero, in: view)
            positionCamera()
        }
        @objc func pinch(_ gesture: UIPinchGestureRecognizer) {
            guard gesture.state == .began || gesture.state == .changed else { return }
            camera.setZoom(camera.zoom * Double(gesture.scale))
            gesture.scale = 1
            zoom.wrappedValue = camera.zoom
            positionCamera()
        }
        func positionCamera() {
            guard let view, let node = view.pointOfView else { return }
            let position = camera.position
            SCNTransaction.begin()
            SCNTransaction.disableActions = true
            node.position = SCNVector3(position.x, position.y, position.z)
            // Explicit pitch and zero roll prevent vertical drags or zoom from tilting the POV.
            node.eulerAngles = SCNVector3(IslandCamera.pitch, camera.yaw, 0)
            node.camera?.orthographicScale = camera.scale(width: Double(view.bounds.width), height: Double(view.bounds.height))
            SCNTransaction.commit()
        }
    }
}

private final class IslandSceneView: SCNView {
    var onLayout: (() -> Void)?
    override func layoutSubviews() {
        super.layoutSubviews()
        onLayout?()
    }
}

private enum IslandScene {
    static func material(_ color: UIColor) -> SCNMaterial {
        let m = SCNMaterial(); m.diffuse.contents = color; m.roughness.contents = 0.95
        return m
    }
    static func make() -> SCNScene {
        let scene = SCNScene()
        scene.background.contents = UIColor(red: 0.67, green: 0.85, blue: 0.86, alpha: 1)
        let camera = SCNNode(); camera.name = "camera"; camera.camera = SCNCamera()
        camera.camera?.usesOrthographicProjection = true; camera.camera?.orthographicScale = 11.8
        camera.camera?.zFar = 100
        camera.position = SCNVector3(0, 10, 12); camera.look(at: SCNVector3(0, -1.4, 0))
        scene.rootNode.addChildNode(camera)
        let ambient = SCNNode(); ambient.light = SCNLight(); ambient.light?.type = .ambient
        ambient.light?.color = UIColor(red: 0.85, green: 0.92, blue: 1, alpha: 1)
        ambient.light?.intensity = 650; scene.rootNode.addChildNode(ambient)
        let sun = SCNNode(); sun.light = SCNLight(); sun.light?.type = .directional
        sun.light?.intensity = 1100; sun.light?.castsShadow = true
        sun.light?.shadowColor = UIColor(red: 0.16, green: 0.3, blue: 0.25, alpha: 0.23)
        sun.light?.shadowRadius = 5; sun.light?.shadowMapSize = CGSize(width: 2048, height: 2048)
        sun.eulerAngles = SCNVector3(-Float.pi / 3, -Float.pi / 5, 0)
        scene.rootNode.addChildNode(sun)
        let water = SCNPlane(width: 150, height: 150)
        water.materials = [material(UIColor(red: 0.49, green: 0.77, blue: 0.81, alpha: 1))]
        let ocean = SCNNode(geometry: water); ocean.eulerAngles.x = -.pi / 2; ocean.position.y = -0.42
        scene.rootNode.addChildNode(ocean)
        scene.rootNode.addChildNode(land(radius: 4.25, height: 0.45, y: -0.18, color: UIColor(red: 0.93, green: 0.82, blue: 0.59, alpha: 1)))
        let ground = land(radius: 3.8, height: 0.24, y: 0.16, color: UIColor(red: 0.54, green: 0.72, blue: 0.34, alpha: 1))
        ground.name = "walkableGround"
        ground.categoryBitMask = 2
        scene.rootNode.addChildNode(ground)
        // A deterministic scatter keeps the scene stable across launches.
        for i in 0..<170 {
            let theta = Float(i) * 2.39996
            let radius = 0.95 + sqrt(Float(i) / 170) * 2.55
            let x = cos(theta) * radius, z = sin(theta) * radius * 0.85
            let tuft = grass(size: 0.10 + Float(i % 5) * 0.018)
            tuft.position = SCNVector3(x, 0.29, z)
            tuft.eulerAngles.y = theta
            scene.rootNode.addChildNode(tuft)
        }
        for i in 0..<15 {
            let theta = Float(i) * 2.39996
            let r: Float = 2.1 + Float(i % 4) * 0.3
            let flower = SCNSphere(radius: 0.045); flower.segmentCount = 6
            flower.materials = [material(i % 2 == 0 ? .init(red: 1, green: 0.95, blue: 0.72, alpha: 1) : .white)]
            let node = SCNNode(geometry: flower); node.position = SCNVector3(cos(theta) * r, 0.36, sin(theta) * r * 0.8)
            scene.rootNode.addChildNode(node)
        }
        for i in 0..<4 {
            let ripple = SCNTorus(ringRadius: CGFloat(4.6 + Double(i) * 0.75), pipeRadius: 0.014)
            ripple.ringSegmentCount = 96; ripple.pipeSegmentCount = 3
            ripple.materials = [material(UIColor.white.withAlphaComponent(0.25))]
            let n = SCNNode(geometry: ripple); n.position.y = -0.39; n.scale.z = 0.86
            scene.rootNode.addChildNode(n)
        }
        if let url = Bundle.main.url(forResource: "Fibu.Soft", withExtension: "usdz"),
           let source = try? SCNScene(url: url, options: [.checkConsistency: true]) {
            // The USD skeleton's animated bounds differ from its undeformed mesh bounds.
            // Establish the imported first-frame pose before measuring the feet and head.
            FibuWalker.preparePose(source.rootNode)
            let fibu = SCNNode(); fibu.name = "Fibu"
            fibu.position.y = 0.29
            let body = SCNNode(); body.name = "FibuMotion"
            let model = SCNNode()
            for child in source.rootNode.childNodes { model.addChildNode(child) }
            let toes = ["Toe_L_end", "Toe_R_end", "Foot_L", "Foot_R"].compactMap {
                model.childNode(withName: $0, recursively: true)?.convertPosition(SCNVector3Zero, to: model).y
            }
            let floor = toes.min() ?? model.boundingBox.min.y
            let top = model.childNode(withName: "Head_end", recursively: true)?.convertPosition(SCNVector3Zero, to: model).y ?? model.boundingBox.max.y
            let scale: Float = 1.85 / max(top - floor, 0.001)
            model.scale = SCNVector3(scale, scale, scale)
            model.position.y = -floor * scale + 0.025
            body.addChildNode(model); fibu.addChildNode(body)
            scene.rootNode.addChildNode(fibu)
        } else {
            // Make asset failure visible rather than silently substituting another character.
            let text = SCNText(string: "Fibu model unavailable", extrusionDepth: 0)
            text.font = .systemFont(ofSize: 0.2); text.firstMaterial?.diffuse.contents = UIColor.darkGray
            let label = SCNNode(geometry: text); label.position = SCNVector3(-1, 1, 0)
            scene.rootNode.addChildNode(label)
        }
        return scene
    }

    static func land(radius: Float, height: Float, y: Float, color: UIColor) -> SCNNode {
        let count = 96
        var vertices = [SCNVector3(0, height / 2, 0)]
        for level in [height / 2, -height / 2] {
            for i in 0..<count {
                let a = Float(i) / Float(count) * .pi * 2
                let r = radius * (1 + 0.035 * sin(a * 3) + 0.018 * cos(a * 5))
                vertices.append(SCNVector3(cos(a) * r, level, sin(a) * r * 0.86))
            }
        }
        var indices: [Int32] = []
        for i in 0..<count {
            let a = Int32(i + 1), b = Int32((i + 1) % count + 1), c = a + Int32(count), d = b + Int32(count)
            indices += [0, b, a, a, b, c, b, d, c]
        }
        let shape = SCNGeometry(sources: [SCNGeometrySource(vertices: vertices)], elements: [SCNGeometryElement(indices: indices, primitiveType: .triangles)])
        shape.materials = [material(color)]
        let node = SCNNode(geometry: shape); node.position.y = y
        return node
    }

    static func grass(size: Float) -> SCNNode {
        let vertices = [SCNVector3(-0.07, 0, 0), SCNVector3(-0.045, size, 0), SCNVector3(0.025, 0, 0), SCNVector3(0, 0, 0.01), SCNVector3(0.08, size * 0.8, 0.01), SCNVector3(0.07, 0, 0.01)]
        let shape = SCNGeometry(sources: [SCNGeometrySource(vertices: vertices)], elements: [SCNGeometryElement(indices: [Int32(0), 1, 2, 3, 4, 5], primitiveType: .triangles)])
        let m = material(UIColor(red: 0.32, green: 0.55, blue: 0.22, alpha: 1)); m.isDoubleSided = true
        shape.materials = [m]
        return SCNNode(geometry: shape)
    }
}

#Preview { ContentView() }
