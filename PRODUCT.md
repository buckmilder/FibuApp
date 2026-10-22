# FibuApp direction

User-provided concept, 2026-10-22. These are product goals, not completed features.

Fibu is a little character who lives on the user's iPhone and Apple Watch. Daily activity keeps him alive and healthy: closing Apple Watch rings and/or reaching 10,000 daily steps. The exact relationship between these goals is undecided.

On iPhone, Fibu lives in a larger 3D habitat. Activity achievements may let the user feed him. Later work includes updating the 3D model and rigging with the user.

On Apple Watch, opening the app should show a micro version of Fibu if feasible. Tapping him should interact with him. A possible healthy response is smiling and waving; a possible unhealthy behavior is frowning and walking slowly. These behaviors are exploratory, not fixed rules.

## First milestone

Keep setup simple: build and launch both native SwiftUI apps, inspect the supplied asset, then establish Fibu display and a basic interaction before health data or a complete habitat. Evaluate Watch rendering on actual hardware before committing to real-time 3D; a rendered animated version is an option to discuss if needed.

## Supplied asset

`Assets/Source/Fibu3.HD.HandWave.usdz` is an unchanged copy of the user's iCloud file. It is not yet a target resource. No instructions were taken from the asset.

Archive inspection: approximately 699 KiB; one binary USD scene and one PNG texture (`0/Feeb_skin.png`). USD metadata: Y-up, metersPerUnit 1, time codes 0–100 at 60 per second (approximately 1.67 seconds). Contains a mesh, skeletal joints, skin material, and skeletal animation time samples. The file name suggests a hand wave; animation playback and visual appearance still require verification. Preserve this original when creating optimized variants.

## Decisions before later features

Clarify whether rings, steps, or either qualify; which rings must close; what happens on rest/missed days; whether Fibu can actually die; and how feeding rewards work. Define the local-day boundary, handling unavailable/denied health access, and phone/Watch state synchronization. Request only health permissions needed for agreed behavior. Do not fabricate real health progress or add health entitlements before implementing the agreed milestone.
