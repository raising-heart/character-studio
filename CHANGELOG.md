# Changelog

## 0.6.0 — base-body foundation

- Added Character Base Body, a dedicated skill and local builder for a connected faceted T-pose mannequin before clothing/face/hair work.
- Added balanced/compact/sturdy body variants, continuous shoulder/neck/hip/foot surfaces, blended weights and five joint-study poses.
- Clarified reference-inspired original styling versus faithful reconstruction; references do not automatically define the house-style proportions.
- Added topology, symmetry, skin/pose and security checks plus actual base-body previews. The base is a style foundation; gameplay motion and fitted costumes remain subsequent work.
- Preserved the 0.5 dressed starter for compatible existing assets. Its clothing/motion is not a direct fit for the new mannequin.

## 0.5.0

- Made staged low-poly humanoid construction the default for suitable character briefs; kept robot and animal routes available.
- Added an executable humanoid builder with bald T-pose body, outfit, boots, mesh face, short/braided/bald hair, six checkpoints and selective part updates.
- Added profile/shell geometry tools, bounded JSON settings, neutral-pose-aware Idle/Walk/Run/Jump/Roll and local reference comparisons.
- Added source provenance, MIT notices, a security audit, overwrite protections and disabled embedded checkpoint scripts; hardened the effects loader too.
- Tested the orange-braided reference study, a differently proportioned humanoid, static output, checkpoint preservation, invalid inputs, exported motion and browser previews.

## 0.4.0

- Added an image-reference workflow with Robot-base and Custom build paths and optional blockout comparisons.
- Added subjective difficulty/effort estimates with reasons and explicit reference assumptions.
- Added instructions for fitting the rig, updating weights, transferring/repairing clips and testing the final character separately from the donor robot.
- Model and animation starter scripts are unchanged from 0.3.1; this release extends the Codex workflow.

## 0.3.1

- Corrected robot Run/Walk knee flexion: the recovering leg folds backward and the leading leg extends with a small positive knee bend.
- Added ankle counter-rotation to keep the forward foot readable instead of turning its sole toward the camera.
- Updated the motion preview and checked both legs throughout the gait cycle.

## 0.3.0

- Robot starter now includes Run, Jump and Roll alongside Idle and Walk.
- Added one-shot/loop metadata and guidance for integrating visual root offsets with game physics.
- Added a segmented fox/dog/cat quadruped starter with Idle, Walk, Run and Jump.
- Added animal body-plan, rigging and gait guidance.

## 0.2.0

- Added the Character Effects skill and Blender aura/sparks/fire/smoke preview helper.
- Added a bounded Three.js runtime module for particle bursts, anchored emitters, auras and simple trails.
- Added animation-cue dispatch, reduced motion and explicit resource cleanup.
- Validated Blender presets and actual browser rendering, including mobile layouts.
- Published the existing plugin as an installable GitHub marketplace, with installation and contribution instructions.

## 0.1.0

- Added the Character Studio workflow for stylized low-poly Blender characters.
- Added Blender discovery, procedural rigged robot starter and GLB inspection scripts.
- Included rigging, export and visual-review guidance.
