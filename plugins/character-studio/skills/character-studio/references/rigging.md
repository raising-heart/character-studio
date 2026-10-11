# Rigging and animation

Choose the rig to match the asset. A rigid segmented robot can assign every part to one bone. A continuous humanoid needs weight blending through shoulders, elbows, hips, knees, and neck; automatic weights are only a starting point. Keep a neutral bind pose and apply non-unit mesh scale before skinning. Preserve an existing rig and clip names when editing an animated asset.

Use a named root at ground level, a pelvis, spine, head, upper/lower arms, hands, upper/lower legs, and feet as needed. Follow Blender `.L` / `.R` naming when authoring. Bone count and fingers should reflect actual gameplay and camera needs. Separate a deformation skeleton from controllers; bake controller/constraint results for export if the runtime cannot evaluate them.

Give Idle and Walk explicit names and ranges if requested. For a prototype, an in-place Walk is convenient; do not imply root motion exists. Loop endpoints must match in transforms, and verify both the loop boundary and intermediate poses. In Blender 4.4+, actions can have slots: bind the correct slot when assigning/stashing an action. Use export options supported by the installed Blender RNA, and verify actual exported clip names instead of relying on the timeline label.

Render selected keyframes, inspect joints and ground contacts, and play each exported clip in a runtime preview. Check disconnected limbs, weighted attachments, collapsing shoulders, feet penetrating the floor, and accessories moving with the intended bone. Remove only unused temporary test actions, never the user's existing animation library.

The bundled robot uses rigid vertex weights and basic Idle / in-place Walk motion. Its joint gaps and spherical hinge covers are intentional, and organic characters need a different geometry/weight strategy.
