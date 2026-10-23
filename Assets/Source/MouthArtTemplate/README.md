# Draw Fibu's mouth art

Use `frames/replace_me.png` as a blank **512 × 512 RGBA** canvas. It is deliberately empty and is not installed in the app. Import `guides/registration.png` as a separate reference layer, then hide it before export. Draw only the mouth/tongue/teeth and leave the background transparent. Keep the whole canvas identical across every frame; do not trim to the drawing's bounds.

Export numbered PNGs, such as `eat_000.png`, `eat_001.png`, etc. PNG preserves full color, soft edges and partial transparency. A ZIP of the PNG sequence plus a message with its frame rate or frame durations is enough to send back to cloud Codex. You do not have to write JSON yourself. The included `mouth.json` shows the technical format we will prepare from your instructions.

Keep the mouth positioned consistently around the center crosshair. The blue inset is a suggested drawing area, not a cropping boundary. We preserve the complete canvas and your exact frame pixels. Use the same registration point across smile, eating and other clips. 1024 × 1024 is also supported if every frame and the manifest use that size.

GIF is supported as an alternate reference/import: it has a limited palette and cannot preserve the same soft alpha edges as RGBA PNG. If your drawing program offers PNG sequence export, use that for the final art.

Useful clips to start: `smile` (one frame), `eat` (animated), then `happy`, `hungry`, `whistle`. Tell us which should loop. The current body eating action lasts 2.8 seconds and bites at 0.9667 seconds; these are optional timing guides while drawing. Your art is never automatically sped up, redrawn, recolored or recentered. Shorter one-shot art holds its last frame by default until its action ends.
