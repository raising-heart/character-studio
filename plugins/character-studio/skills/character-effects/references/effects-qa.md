# Effects acceptance

Check observable behaviour, not just a screenshot of an emissive material.

- Sparks burst once on a cue, spread/fall/fade, and free slots after their lifetime.
- Smoke/fire emission is stable at ordinary frame rates, stays within its cap, and stops when disabled. Long hidden-tab gaps must not create a huge catch-up burst.
- Auras follow the chosen node after animation and maintain the intended size/palette.
- Trails follow the bone, reset across teleports, and disappear after removal. The starter is a line trail, not a wide ribbon renderer.
- A particle born at a hand stays in scene space after the hand moves; it does not become accidentally bone-parented.
- Cue crossing works once per crossing, including a normal clip loop. Reverse scrubbing/seeking must not emit unintended bursts.
- Reduced motion removes particle/trail movement, disables pulsing, and retains a subdued static aura. Avoid rapid flashes in either mode.
- Geometry/materials are reused; GPU resources and scene nodes are removed on disposal. Dynamic counts must remain bounded after repeated effects.
- Preview onset, peak and fade at desktop and small-screen sizes with the actual character, shadows, and camera distance. Examine transparent edges, order, face visibility, and depth intersections.
- Record which tests were actual Blender renders, browser renders, numerical tests, or export validation. Do not call numeric tests a visual browser playtest.

Blender particle systems, procedural materials, Geometry Nodes and compositor effects are authoring/render features, not a promise of a portable live GLB effect. Bake supported mesh/pose/morph animation when appropriate and validate its export, or ship browser VFX code/config separately. The preview helper intentionally does not export its puff meshes to the base character GLB.
