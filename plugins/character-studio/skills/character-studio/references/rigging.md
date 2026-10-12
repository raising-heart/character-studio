# Rigging and animation

Choose the rig to match the asset. A rigid segmented robot can assign every part to one bone. A continuous humanoid needs weight blending through shoulders, elbows, hips, knees, and neck; automatic weights are only a starting point. Keep a neutral bind pose and apply non-unit mesh scale before skinning. Preserve an existing rig and clip names when editing an animated asset.

The staged humanoid has T-pose arm bones and simple analytic blended limb/torso weights. Its clip authoring converts desired world rotations through the neutral and parent bone orientations, including lowering the arms for animation. The old robot has different arm axes: copying its local keyframes by bone name is unsuitable. Hands have one bone each and the face/hair are static head-weighted meshes. Inspect overlap seams and deformation; this starter is not a production organic auto-rigger.

Use a named root at ground level, a pelvis, spine, head, upper/lower arms, hands, upper/lower legs, and feet as needed. Follow Blender `.L` / `.R` naming when authoring. Bone count and fingers should reflect actual gameplay and camera needs. Separate a deformation skeleton from controllers; bake controller/constraint results for export if the runtime cannot evaluate them.

Give clips explicit names and ranges. The robot starter supplies looping Idle/Walk/Run and one-shot Jump/Roll. The quadruped supplies Idle/Walk/Run/Jump. Walk/Run have no accumulating horizontal travel. Loop endpoints must match in transforms; verify both boundaries and intermediate poses. Jump/Roll must return to a usable pose but are not intended to repeat continuously. In Blender 4.4+, actions can have slots: bind the correct slot when assigning/stashing an action. Use export options supported by the installed Blender RNA, and verify actual exported clip names instead of relying on the timeline label.

Render selected keyframes, inspect joints and ground contacts, and play each exported clip in a runtime preview. Check disconnected limbs, weighted attachments, collapsing shoulders, feet penetrating the floor, and accessories moving with the intended bone. Remove only unused temporary test actions, never the user's existing animation library.

The bundled robot uses rigid vertex weights, a faster wider Run, a crouch/lift/landing Jump, and a tucked forward Roll. Its joint gaps and spherical hinge covers are intentional. Locomotion is a prototype without foot locking; organic characters need a different geometry/weight strategy.

## Runtime integration

Read clip metadata in the generated JSON report. In Three.js, use `LoopRepeat` for Idle/Walk/Run and `LoopOnce` with `clampWhenFinished = true` for Jump/Roll, then crossfade back to locomotion when the action completes. Prevent repeated key presses from resetting an active one-shot unless that behaviour is requested. Put horizontal movement and collisions on an outer gameplay object, separate from the imported visual rig.

Jump includes baked vertical Root translation for standalone playback. If game physics also controls vertical position, make a copy of the Jump clip and remove its Root position track (resolve the actual exported name, usually `Root.position`), then apply physics to the outer gameplay object. Keep the rotation/limb tracks. Do not combine both lifts. Roll's Root translation compensates its body pivot and ground clearance; keep it as a visual offset and implement gameplay roll travel separately. `root_motion: false` means no accumulating gameplay travel; `visual_root_offsets` records these baked offsets.

Validate loaded bounds and the ground contact at intermediate times, finite skinned vertices, Run cadence, full Roll rotation, Jump lift, one-shot completion, transitions, and repeated actions. Smooth blending and collisions need task-specific game implementation; an exported clip alone does not provide them.
