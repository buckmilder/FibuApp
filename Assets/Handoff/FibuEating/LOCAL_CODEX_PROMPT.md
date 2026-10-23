Fetch `origin/codex/fibu-eating` and integrate its latest asset changes without overwriting local work. Read `Assets/Handoff/FibuEating/README.md`.

Use the UPDATED FULL CHARACTER MODEL at `Assets/Models/FibuEating/Fibu.Eat.usdz`, plus its `EatingTextures` folder and version-2 `timeline.json`. This model includes the elastic-arm morphs, fitted mouth expressions and empty `FoodSocket`; copying just an animation onto the old model will omit those features. Preserve the approved proportions model for wave/rollback, all local unlocked skins, and the Watch model.

Start eating only when the user manually taps a READY food. Hold the model at its time-zero pose on scene load; disable automatic eating playback.

At FRAME 0 / TIME 0.0 SECONDS, BEFORE playing the action, create a sprite using the EXACT FOOD THE USER TAPPED and parent it to `FoodSocket` at socket-local origin. This is Fibu's RIGHT palm (viewer's LEFT in the front view). Apply the sprite's grip pivot and local size using the handoff dimensions. Show it in his hand from the first frame. No food geometry is baked into the model.

Keep that same sprite parented to the socket throughout the reach. `FoodSocket` follows a rolling contact on the expanding palm and carries it toward the mouth. Use its imported track or the timeline's `foodSocketPosition`, with the character wrapper transform applied once. The old `Hand_R_end` bone stays still during this morph-driven action and is not the attachment point.

At ZERO-BASED RUNTIME FRAME 29 (Blender frame 30) / approximately 0.9667 SECONDS, remove/hide the sprite and update the selected food's consumed state exactly once. At the 2.8-second end, restore normal idle control, smile, and zero arm morphs. Guard repeated taps and clean up the temporary sprite on interruption.

Play all four body morphs (`CheekPuff`, `Swallow`, `ArmPrepare`, `ArmBite`), both facial morphs, expression visibility, and the socket on ONE clock. Set morph calculation to additive and pause competing procedural body/arm/walk/wave deformation during eating. Keep the torso fixed. Map selected skins to their NoSmile runtime derivatives while preserving artist originals.

Verify first-frame sprite placement, palm contact during the reach, removal at the bite, torso stability from both sides, all existing skins and return to idle in the iPhone simulator. Build both schemes and run relevant existing checks. Keep the Watch model unchanged.
