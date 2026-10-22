# FibuApp

Native SwiftUI iPhone app with an embedded Apple Watch companion. The iPhone app now shows a native 3D island MVP; the Watch companion shows a 3D island with tap-to-wave Fibu. The initial product direction is recorded in PRODUCT.md; health and interaction mechanics are not implemented yet.

Open `FibuApp.xcodeproj` in Xcode. Shared schemes are **FibuApp** (iPhone) and **FibuWatch** (Apple Watch). No package manager or project generator is needed.

## First setup

1. Finish installing Xcode in Applications, open it, and complete its agreement, administrator, and first-launch prompts. Install iOS and watchOS platform support and simulator runtimes from Xcode Settings → Components (the section name may vary by Xcode version). Free disk space if installation requires it; this Mac had approximately 14 GiB available at initial inspection.
2. Run `./scripts/build-simulators.sh` from this directory. It builds both shared schemes without signing and saves logs in `build/logs/`. The script selects `/Applications/Xcode.app` locally if present.
3. In Xcode Settings → Apple Accounts, sign in yourself. In each target's Signing & Capabilities, select the same development team and keep automatic signing enabled. The bundle IDs are provisional; change both together if Xcode reports a conflict, including the Watch target's companion ID build setting. Start with your existing account/Personal Team if available; do not purchase membership just for this setup.
4. Connect and unlock your iPhone, accept Trust prompts, and keep its paired Apple Watch nearby and unlocked. Open Xcode's Devices and Simulators window to finish pairing/preparation. Enable Developer Mode on each device when prompted; this can require restarting and confirming on the device. Never share your password or verification codes in chat.
5. Select the **FibuApp** scheme and your iPhone as destination, then Run. Select **FibuWatch** and your paired Watch destination, then Run. Allow Xcode time to prepare device support. If a destination is missing, share the exact Xcode error and device OS versions so we can resolve compatibility or pairing.

Apple's guidance: [running on devices](https://developer.apple.com/documentation/xcode/running-your-app-on-simulated-or-physical-devices), [installing Xcode components](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components), and [watchOS projects](https://developer.apple.com/documentation/watchos-apps/setting-up-a-watchos-project).

## Everyday workflow

Provide assets in chat or add them to the repository, describe the change and intended device, and include expected behavior. I update SwiftUI and asset catalogs, build both targets, and give you a short testing checklist. You run the apps on your iPhone and Watch and send observations or screenshots for the next iteration. No build upload or paid membership purchase is authorized.

Initial device checklist: each app launches, shows “FibuApp” and its device readiness text, remains readable with larger text, and works in light/dark appearance where supported. No syncing or other product behavior is implemented yet. App icons are pending supplied artwork.

Future chats should follow `AGENTS.md`.

## Verification status

Both FibuApp and FibuWatch built successfully for generic simulator destinations with Xcode 27.1 on 2026-10-22. Logs are in build/logs/. Project references, scheme XML, and asset JSON also validated. Simulator runtimes are still downloading; no simulators or connected physical devices were listed at the last check. App launch, signing, and physical device testing remain pending. Fibu's supplied model is preserved in Assets/Source/ and is not yet displayed by the placeholder apps.

## Island MVP — 2026-10-22

The iPhone screen uses SwiftUI and SceneKit with the original Fibu USDZ bundled as a resource. It includes a grassy island, sand, water, drag-to-orbit camera and reset control, a demo step counter, and three activity rings. The demo button increments steps by 500, caps at 10,000, then offers reset. Demo activity is not health data and is not persisted; exercise and stand rings are fixed sample values. No health permissions, synchronization, rewards, or survival rules were added.

Both simulator schemes built successfully. The iPhone 16 Pro simulator displayed the model and scene, and the demo increment, goal cap, and reset were verified through the UI. The Duo app launched and its primary display was inspected; additional display configurations remain untested. Xcode’s active destination is now the iPhone 16 Pro simulator. Use Device Hub to view it and Run in Xcode to rebuild. Physical-device testing is deferred at the user’s request.

## Tap to walk — 2026-10-22

Tap the grass to send Fibu to a destination; drag to orbit and use the viewfinder button to reset the camera. The destination marker disappears on arrival. Taps on water and the vertical island edge are ignored. Walk destinations are clamped to an inset ellipse so the character stays on land, including when retargeted during a walk. Avatar movement does not change the demo step counter.

FibuWalker creates procedural skeletal walk and idle animations in memory using the supplied rig; these are first-pass animations, not new authored USDZ clips. The original wave asset is preserved unchanged. Its initial pose is loaded explicitly, then opposing leg/arm motion, knee flex, body sway, a turn, and an arrival blend are applied. Grounding uses the skeleton’s feet instead of its undeformed mesh bounds.

Validation: both simulator schemes built. Focused math checks pass for boundary clamping, all 7,560 sampled path points, cardinal headings, zero distance, and retarget timing (`./scripts/test-movement.sh`). A simulator tap was observed producing a destination ring, character movement, arrival, and idle. Physical device testing is deferred.

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
