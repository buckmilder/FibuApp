import SwiftUI
import SceneKit

struct ContentView: View {
    @StateObject private var island = WatchIsland()
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                SceneView(scene: island.scene, pointOfView: island.camera,
                          options: scenePhase == .active ? [.rendersContinuously] : [],
                          preferredFramesPerSecond: 20, antialiasingMode: .multisampling2X)
                    .ignoresSafeArea()
                    .accessibilityHidden(true)
                VStack {
                    Spacer()
                    Text(island.isGreeting ? "Hello there!" : "Tap Fibu to say hello")
                        .font(.system(size: 10, weight: .medium, design: .rounded))
                        .foregroundStyle(Color(red: 0.14, green: 0.28, blue: 0.23))
                        .padding(.horizontal, 10).padding(.vertical, 5)
                        .background(.white.opacity(0.65), in: Capsule())
                        .padding(.bottom, 8)
                }.allowsHitTesting(false)
                Button { island.greet() } label: { Color.clear.contentShape(Rectangle()) }
                    .buttonStyle(.plain)
                    .frame(width: geometry.size.width / 3 + 24, height: geometry.size.height / 3 + 24)
                    .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
                    .accessibilityLabel("Say hello to Fibu")
                    .accessibilityHint("Fibu looks toward you and waves")
                    .disabled(island.isGreeting || !island.hasModel)
                if !island.hasModel {
                    Text("Fibu couldn’t load").font(.caption).padding()
                }
            }
        }
        .onAppear { island.setActive(scenePhase == .active) }
        .onChange(of: scenePhase) { _, phase in island.setActive(phase == .active) }
    }
}

#Preview { ContentView() }
