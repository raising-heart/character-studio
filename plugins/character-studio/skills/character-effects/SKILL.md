---
name: character-effects
description: Add stylized character VFX with Blender previews and Three.js runtime effects. Use for sparks, fire or smoke puffs, magic auras, bone-following trails, and animation-timed cues on 3D characters; not for general cinematic fluid simulation or facial rigging.
---

# Character Effects

Build effects that read with the character and work in the intended destination. Use the user's existing style, character scale, bones, clips, and performance budget. This is an extension of Character Studio, not a universal simulation or VFX export engine.

## Select the delivery path

- **Blender render/preview:** use editable meshes, materials, keyframes, or a justified simulation. The bundled `scripts/preview_effect.py` adds a named Effects collection to a working copy of a `.blend` file and demonstrates a bone-attached aura or seeded sparks/fire/smoke mesh puffs. It saves a new `.blend`, a contact-sheet-ready set of PNGs, and a report. It is a stylized mesh preview, not a fluid solver.
- **GLB-compatible mesh effects:** mesh transforms, skeletal motion, and morph targets may be baked/exported with appropriate materials. Test the actual exported animation/materials in the destination. Do not assume a shader, material parameter driver, Geometry Nodes setup, Blender particle system, compositor glow, or volumetric simulation transfers as a live GLB effect.
- **Browser game VFX:** ship the character GLB and separate runtime code/config. Read [Runtime integration](references/runtime-effects.md). Copy `assets/three-character-effects.mjs` into the user's project and supply that project's Three.js namespace. It provides bounded seeded sparks, smoke/fire puffs, dust and magic bursts, anchored emitters, pulsing auras, short trails, cue dispatch, and explicit disposal. Adapt it to the requested art direction rather than treating the starter as a polished universal renderer.

## Workflow

1. State the effect's purpose, visual language, attachment point, trigger, lifetime, and delivery path. Infer obvious choices; clarify only missing decisions that affect implementation. Start with one effect on the actual character.
2. Define a small budget: particle cap, emitter rates, trail samples, maximum lifetime, transparency cost, and reduced-motion behaviour. Default to a few hundred particles total for a prototype, and measure on the target device before calling it production-ready.
3. Resolve named bones/nodes in the imported character. Confirm offsets with a temporary marker in the actual coordinate system. Sample anchors after the animation mixer and world matrices update. Spawn particles into scene coordinates; already-emitted particles must not drag along with a moving limb.
4. Keep deterministic seeds and time-based lifetime/velocity updates for debugging. Sync cues to clip time and playback speed. Detect loop crossings and suppress seek/reverse events unless requested. Do not emit an effect every render frame when one animation cue should emit once.
5. Inspect stills at onset, peak, fade, and loop boundary. Play both the character and effect together. Check missing attachments, teleport streaks, depth sorting, alpha edges, obscured faces, bounds/culling, pause/resume, and shutdown cleanup. Test reduced motion. Read [Acceptance checks](references/effects-qa.md).
6. Deliver an effects-enabled `.blend` and previews when requested, and for browser use the character `.glb`, runtime module, attachment/cue config, and an actual runtime preview. Clearly label which effects live in the GLB and which need runtime code. Preserve existing clips and character export behaviour.

## Blender helper invocation

Locate Blender with Character Studio's `../character-studio/scripts/find_blender.ps1`, then use a dedicated background process:

```text
blender --background --python-exit-code 1 --python <skill-root>/scripts/preview_effect.py -- --input <character.blend> --output <new-output-directory> --kind aura --bone Hand.L
```

`--kind` accepts aura, sparks, fire, or smoke. `--bone` defaults to Head; `--rig` disambiguates multiple armatures. Use `--offset X Y Z` in bone-local coordinates to move the source outside the mesh; tune it in the preview. The helper refuses existing named outputs unless `--overwrite` is explicit. It adds only its own Effects collection in a loaded working copy and does not write to the input file. It leaves the base GLB generation separate so previews cannot silently pollute the character export.

## Limits

The built-in fire/smoke is stylized particles/mesh puffs, not physically simulated fluid. Trails are simple fading line trails; wide ribbons, sprite-sheet baking, bloom postprocessing, advanced shaders, and fluid caches require additional task-specific work. Emissive colour is not automatically screen-space glow. Facial animation and organic skinning are still separate character-rigging work.
