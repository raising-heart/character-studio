# Three.js integration

The starter module accepts the project's Three.js namespace, so it does not bundle a second copy or force a package version. It was tested with Three.js 0.186.1. Use the established project version, check compatibility when it differs, and do not introduce a renderer or animation loop alongside an existing one.

```javascript
import * as THREE from 'three';
import { createCharacterEffects, dispatchAnimationCues } from './three-character-effects.mjs';

const effects = createCharacterEffects(THREE, scene, { maxParticles: 256, seed: 7 });
// Inspect the loaded GLB's node names: export may sanitize Blender's Hand.L to HandL.
const hand = character.getObjectByName('HandL');
if (!hand) throw new Error('HandL attachment was not found');
effects.setAura('hand-aura', hand, { radius: 0.16, color: 0x55ddff });
// Move the source outside the mesh; tune this offset against your character's bone axes.
effects.setEmitter('hand-fire', { kind: 'fire', anchor: hand, rate: 24, offset: [0.18, 0, 0] });
effects.setTrail('hand-trail', hand, { samples: 24, color: 0x55ddff, offset: [0.18, 0, 0] });

// Within the existing frame loop:
mixer.update(dt);
scene.updateMatrixWorld(true);
effects.update(dt);
renderer.render(scene, camera);

// When leaving the scene:
effects.dispose();
```

Pause both the mixer and the effects simulation together. Apply playback speed consistently. Connect `setReducedMotion(matchMedia('(prefers-reduced-motion: reduce)').matches)` and listen for preference changes; reduced motion removes moving particles/trails and leaves only a static restrained aura. Remove that listener during teardown.

Positions passed to `burst(kind, position, count)` are in scene-local coordinates. Anchors are Object3D instances in the scene and their offsets are in the anchor's local coordinates; the helper samples their current world transform and converts to the scene. Emitted particles remain in scene coordinates even when the anchor later moves. Keep the scene's global transform fixed during simulation.

Available particle kinds: `sparks`, `smoke`, `fire`, `dust`, `magic`. Fire is a looping emitter of warm particles, smoke is soft gray puffs, and magic is a cool burst. The renderer uses one bounded Points pool with a soft circular shader and normal alpha blending. This is a baseline: luminous additive pools, atlases, wide ribbon trails, and volumetric effects are additional implementation work. Depth writing is disabled for the transparent effects. Frustum culling is disabled for the small dynamic pool to avoid stale-bounds disappearance; measure before scaling to large worlds.

`dispatchAnimationCues(previousElapsed, currentElapsed, duration, cues, callback)` works with monotonically accumulated **clip seconds**, including completed loops. Cues are `{time, kind, count}` or task-specific records. It fires intervals `(previous, current]`, orders them by crossing time, handles normal wrap through accumulated elapsed, and ignores reverse/seek windows. Reset accumulated time on a clip change and dispatch any time-zero startup cue explicitly. Do not feed a looping action's wrapped `action.time` directly; track loop count or the elapsed clip time. It caps crossings to prevent a huge resume/seek emission burst.

API lifecycle: `removeEmitter(name)`, `removeAura(name)`, `removeTrail(name)`, `clear()`, and idempotent `dispose()`. Overflow is dropped, not allocated beyond the configured cap. `stats()` reports active/dropped particles and scene effect counts. Call `update(0)` for attachment refresh without emitting or ageing particles. Invalid counts/rates/durations fail early.

Official reference: https://threejs.org/docs/
