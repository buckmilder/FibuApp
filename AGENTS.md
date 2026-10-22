# FibuApp project instructions

## Purpose and current scope
Native Swift and SwiftUI iPhone app with an Apple Watch companion. The user supplied the initial product direction on 2026-10-22; see PRODUCT.md. Prioritize getting the minimal apps and Fibu rendering running before adding health mechanics. The initial screens remain setup placeholders. Ask about unresolved behavior before implementing health, rewards, or survival rules.

## Project structure
- Open FibuApp.xcodeproj; no generator or third-party dependencies required.
- FibuApp/ contains the iPhone app; FibuWatch/ contains the single-target watchOS companion.
- Shared schemes: FibuApp and FibuWatch. The iPhone target depends on and embeds the watch app.
- Minimum versions: iOS 17 and watchOS 10; revisit after inspecting the user's device OS versions.
- Provisional IDs: com.ianbuckner.FibuApp and com.ianbuckner.FibuApp.watchkitapp. Keep WKCompanionAppBundleIdentifier aligned with the iPhone ID when changing identifiers.
- Automatic signing is enabled; no development team is selected. Let the user sign into Apple accounts and select their team. Never store credentials or private signing material in this repository.

## Collaboration workflow
1. The user provides assets and describes the requested behavior, including which device it affects. Inspect supplied files and clarify material ambiguity; implement routine details autonomously.
2. Update SwiftUI code and the appropriate Assets.xcassets. Use named asset sets with valid Contents.json metadata; preserve originals when useful and do not invent final branding. Use semantic colors, Dynamic Type, accessibility labels where needed, and watch-appropriate layouts.
3. Keep iPhone and Watch responsibilities explicit. Add WatchConnectivity, persistence, networking, entitlements, or permissions only when requirements justify them. Do not promise background synchronization without validating platform behavior.
4. Build BOTH schemes with ./scripts/build-simulators.sh. Inspect failures and fix them. Logs are in build/logs. A successful plist lint is not a successful build. Add meaningful tests for substantive behavior, not placeholder text.
5. When available, run on an iPhone simulator and paired Watch simulator and inspect screens. Ask the user to test on their physical iPhone and Apple Watch; provide a short device checklist for each change.
6. The user reports observations, screenshots, or errors; iterate and rebuild both schemes.
7. State what changed, what was verified, and anything blocked. Never claim a physical device test the user has not confirmed.

## Setup and permissions
Inspect Xcode and devices before choosing destinations: xcodebuild -version, xcrun simctl list devices, xcrun devicectl list devices. If xcode-select points at CommandLineTools, prefer DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer per command rather than changing system settings.
The user handles Apple account login, agreement acceptance, administrator prompts, device trust, Developer Mode, and pairing. Guide them with the actual Xcode messages. No membership purchase, TestFlight/App Store upload, archive distribution, or release without explicit approval. Local builds and code/asset updates are authorized.

## Initial machine inspection (2026-10-22)
Empty Git repository. Apple M1 Max MacBook Pro, 32 GB RAM, macOS 26.6.2. CommandLineTools selected; no Xcode app found in inspected application/developer/volume locations. simctl and devicectl unavailable; device inventory is pending. About 14 GiB disk space available. User is downloading Xcode. Builds remain pending until installation and platform setup finish. Update this status after real builds succeed.

## Current setup status (2026-10-22)
Xcode 27.1 (27A9275) is installed at /Applications/Xcode.app and its license is accepted. BOTH shared schemes compiled successfully for generic simulator destinations using ./scripts/build-simulators.sh with access to Xcode developer services. Logs: build/logs/FibuApp.log and build/logs/FibuWatch.log. No code changes were needed to achieve these builds. simctl lists no installed runtimes/devices yet; user is downloading iOS and watchOS simulator components. devicectl reports no connected devices. Launch testing, signing, and physical device tests remain pending. Sandbox restrictions can prevent CoreSimulator/CoreDevice access; use an approved local build invocation with required service/cache access before diagnosing those messages as a machine defect. Original user-supplied USDZ is preserved at Assets/Source/Fibu3.HD.HandWave.usdz, not yet bundled into either app.

## Simulator coverage
The user explicitly wants to experiment with the iPhone Duo simulator as well as the standard iPhone and Watch. Include Duo layout testing in the workflow; verify safe areas and available display configurations rather than assuming standard phone geometry. Use current simctl inventory to find destinations; do not rely on saved UUIDs across machines. iOS 27.0/27.1 and watchOS 27.0 runtimes are installed. A standard iPhone and Watch simulator have been paired. First boots and app launch checks are in progress; do not claim visual verification until screenshots are inspected.

## Physical-device signing update
Both targets use the same selected team. A generic iOS device build including the embedded Watch app successfully compiled, signed, and validated using DerivedData at /tmp/FibuDeviceBuild. The Documents-hosted build/SigningCheck failed signing because the file provider attached com.apple.FinderInfo to the generated Watch bundle. Keep signed build outputs outside file-provider-managed Documents; do not strip metadata from original user assets. Signing log: build/logs/signing-check.log. User completed Developer Mode and keychain prompts. Physical iPhone discovery still reports connecting; actual installation and launch are not yet confirmed.

## Island MVP status — 2026-10-22
The user chose the existing native Xcode project and simulator-only development for now. FibuApp/ContentView.swift implements the SceneKit island and demo SwiftUI steps/activity UI. The USDZ is now bundled through a PBXResourcesBuildPhase reference to the preserved original. Both schemes build successfully; iPhone 16 Pro visual and demo counter checks passed. Duo primary display inspected, other configurations untested. Do not request physical-device tests for this iteration. No HealthKit data or Watch synchronization is connected. Watch UI remains its prior readiness screen.

## Tap-to-walk update — 2026-10-22
FibuApp/FibuWalker.swift owns procedural idle/walk animation and movement. IslandMovement.swift owns bounded destination geometry and timing; run scripts/test-movement.sh after changes. The original imported wave is stopped only in memory after its first pose is applied. Skeletal toe/head positions determine grounding and scale. Tap hit testing filters the grass category and upward faces; water is not walkable. Both schemes built and an iPhone simulator tap, movement, and arrival were visually checked.

## Softer Fibu model — 2026-10-22

The app now bundles Assets/Models/Fibu.Soft.usdz. Assets/Models/Fibu.Soft.blend is the editable Blender source with a rig and preview walk cycle. Assets/Source/Fibu3.HD.HandWave.usdz remains unchanged. The mesh has rounder contours and a slightly fuller torso/head, matte shading, and 3,200 triangles (original: 1,836). The USDZ retains all 32 bones and the original animation data; mesh topology, UVs, and normalized skin weights were validated. Both simulator schemes build and movement math checks pass. The refined character rendered and walked in the iPhone 16 Pro simulator. No physical-device performance measurement was made.

## Island camera controls — 2026-10-22

Pinch or use the zoom buttons to zoom from 1× to 2.4×. Horizontal dragging orbits at a fixed elevation and zero roll; vertical motion cannot tilt the POV. Reset restores zoom and heading. Layout changes preserve zoom. IslandCamera.swift contains camera math; scripts/test-camera.sh checks elevation at 288 orbit/zoom positions, phone/Duo framing, limits and reset. Both simulator schemes built, movement checks passed, and zoom buttons/reset were visually checked on iPhone; Duo zoom was also checked. Automated computer control did not produce a usable pinch/drag gesture; those gestures have not been manually verified.

## Watch island — 2026-10-22

The Watch app now displays a native SceneKit island with Fibu centered at roughly one-third of the display height. Tap the centered accessible button to turn toward the viewer and play the original wave once, then return to idle; repeated taps during the greeting are ignored. The foreground scene runs at 20 fps and pauses when inactive. It has no health integration or phone controls. Assets/Models/Fibu.Watch.scn is generated from the softer USDZ by running `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun swift scripts/prepare-watch-asset.swift` from the project root. This bakes the first-frame rest pose for watchOS while retaining the wave and rig. Both simulator schemes build. Watch rendering, tap/wave, and return to idle were visually checked on the 46mm Watch simulator. Physical Watch battery/performance and smaller display sizes remain untested.

## Cloud asset handoff — 2026-10-22

See [Assets/Handoff/README.md](Assets/Handoff/README.md) and its manifest. Future Blender edits use `Assets/Blender/Fibu.Soft.blend`; exported USDZ stays at `Assets/Models/Fibu.Soft.usdz`, preserving Xcode references. The old `Assets/Models/Fibu.Soft.blend` copy is retained as a setup snapshot. Preferred handoff branch: `codex/asset-handoff`. At setup, this was an uncommitted local repository with no remote URL; no branch switch, commit, push, or app asset replacement was performed.

## Fibudex skins — 2026-10-22

Fibudex opens a skin picker with 11 supplied textures plus the embedded original. Supplied numbered SVG skin icons are used where available; Original and Leopard use rendered previews because there are no matching SVGs. The user’s Fibudex SVG is the menu button; Habitat is a disabled placeholder. Assets/Skins/ preserves source PNG/SVG files. Runtime 1024-square textures and vector icons are in the iPhone asset catalog. Selection updates only the character’s diffuse material and persists in local UserDefaults; it does not sync to Watch. All 11 skins were rendered on the updated model to validate UV wrapping. Both schemes build and scripts/test-skins.sh, test-camera.sh, and test-movement.sh pass. iPhone simulator skin changes and picker layout were visually checked; character/Watch model hashes are unchanged.

## GitHub collaboration — 2026-10-22

Repository: https://github.com/buckmilder/FibuApp.git. `main` is the shared app baseline; use `codex/asset-handoff` for future cloud asset deliveries. Preserve all existing work and never force-push. Keep Blender sources in `Assets/Blender/` and runtime USDZ exports in `Assets/Models/`. The habitat kit consists of multiple USDZ module files in `Assets/Models/`; preserve `Fibu.Soft.usdz` as the character model. See `Assets/Handoff/README.md`. Credentials, local signing material, Xcode/macOS user files, build outputs, and Blender backups are excluded by `.gitignore`.
