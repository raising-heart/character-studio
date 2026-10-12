# Reference adaptation and build paths

Use a supplied image as design evidence. Inspect it before judging difficulty or reshaping geometry. If the reference is unavailable, request it; continue only work that does not depend on the missing visual. Separate visible silhouette/proportions/palette from inferred back, depth, hidden limbs and costume construction. State those assumptions. A single image does not fully specify a 3D model.

## Choose a path

Present both paths briefly and recommend one, using the user's intended art style, target camera, current asset and animation needs:

| Path | Use when | Work required |
| --- | --- | --- |
| Robot-base | A biped with compatible joints, especially segmented or angular low-poly designs; fast gameplay prototypes | Generate or open the robot, reshape/replace parts, fit its skeleton, update weights and repair inherited clips |
| Custom | Continuous organic surfaces, substantially different anatomy, or a design poorly served by the robot silhouette | Build tailored geometry and rig; transfer compatible motion or author new clips |

Both paths can use the robot's motion as a reference. Custom does not imply discarding useful animation; Robot-base does not imply keeping visible robot panels, gaps or colours. Bone names alone do not guarantee compatibility. Quadrupeds should use their own starter or a tailored animal rig, never automatically the biped robot.

Honor an explicit path. If none is chosen and the brief clearly fits the robot, state that Robot-base is the default and proceed. Otherwise state the recommended Custom path and proceed. Give users an easy opportunity to redirect. If they ask to compare, make small blockouts or representative posed renders for both paths, explain the differences and let them choose before doing two complete assets. Do not duplicate a full project by default.

## Difficulty estimate

Before implementation, give a rough **difficulty / effort estimate from 0 to 100** (0 easiest, 100 hardest), with two or three concrete reasons and uncertainty. It is a subjective planning estimate, not a success probability, a measured reference-match percentage, or a guarantee. Use broad bands: roughly 10–30 for compatible blocky designs, 40–60 for substantial stylized proportion/weight changes, 70–90 for organic anatomy or major rig changes, and 90–100 for demanding realism/sculpting or missing critical evidence. The actual brief can override those example bands.

Describe the main geometry changes and motion risks. Revise the estimate when actual deformation/rendering reveals new work; do not keep an optimistic score after a failure. Character likeness and animation quality are separate judgements.

## Robot-base implementation

1. Copy the bundled robot helper into the task workspace or open the user's existing robot `.blend` as a new working copy. Keep the original source and actions. For an animated brief, first build/load a baseline and exercise the requested clips so rig/export failures can be distinguished from adaptation problems. Use the requested subset; the available clips are Idle, Walk, Run, Jump and Roll.
2. Adapt the **bind/rest-pose geometry** to the reference: silhouette first, then head/torso/limb proportions, costume, face and palette. Replace robot parts where the design requires it. Simple recolouring is not a shape conversion. Re-render at the target camera and compare observable features with the reference.
3. Fit hip, knee, ankle, shoulder, elbow and head pivots to the new mesh. Preserve compatible bone names, hierarchy and axes when useful, but move joints when the new proportions demand it. Update bind data and weights coherently; scaling mesh objects independently of their rig can disconnect joints or distort exported motion.
4. Reuse actions only when their local axes/rest pose remain compatible. If the rest pose, hierarchy or skeleton changes, retarget or rebake rather than blindly copying keyframes. Keep donor actions separate, and label inherited, adapted and newly authored clips. Use rigid weights for segmented geometry and blended weights for continuous skin.
5. Repair motion for the changed proportions: stride and cadence, knee direction, ankle pitch, arm clearance, ground contact, jump crouch/landing, roll tuck/pivot clearance, and costume/accessory intersections. Read the rigging reference for one-shots and baked vertical/pivot offsets. Do not add duplicate physics lift.
6. Export the **adapted character** and inspect/play its actual GLB. Test both legs and both arms, middle poses and boundaries, rather than relying on one attractive frame or the donor robot's passing results. Return to geometry, weights or clips when it fails.

## Custom implementation and motion reuse

Create a tailored blockout and a neutral bind pose. Decide whether the robot or quadruped skeleton can be fitted, a bone map/retarget pass is needed, or new motion is more efficient. Continuous shoulders/hips require deformation review; automatic weights are a starting point. Reuse clip timing and pose intent where helpful without promising that every donor action will transfer. Explain which clips need recreation for the chosen body plan.

## Animation acceptance on the final character

- Play every requested clip on the final mesh, then check the exported GLB. Name the actual source and target assets used for checks.
- Inspect a full cycle and both sides: knees bending as intended, visible shin/ankle chains, controlled foot pitch, limb intersections and shoulder/hip deformation. Avoid claiming foot locking unless implemented and tested.
- Check loop endpoints for locomotion, one-shot completion for Jump/Roll, and transitions when a runtime preview includes them. Bounds and finite vertices complement visual review, not replace it.
- Use side and three-quarter views plus the gameplay camera. Show representative motion previews alongside the reference comparison. Use transparent overlays or side-by-side reference comparisons when helpful, without inventing a numerical likeness score.
- Record pass/fail and limitations per clip. If a requested clip is poor, repair it or clearly report the remaining issue; do not silently substitute the robot render as evidence for the final character.

The built-in motions are editable prototype baselines. They provide a useful control rig and repeatable export path, but are not motion capture, production organic animation, or a general image-to-3D reconstruction service.
