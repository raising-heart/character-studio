# Reusable T-pose mannequin

Use the mannequin as an editable design foundation. Each generated `.blend` has a body collection, separate rig and preview stage. The body is one connected surface, including head/neck, shoulder openings, crotch fork, ankle and feet. Named vertex groups follow the 16-bone rig. No clothing, hair or source-image geometry is included.

## Generate

```text
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python <plugin>/skills/character-base-body/scripts/build_base_body.py -- --output <new-output> --name StudioBase --spec <plugin>/skills/character-base-body/assets/studio-base.json
```

For adaptation, preserve the relative `skills/character-base-body/scripts/` and `skills/character-studio/scripts/` layout. Copy the base builder plus `build_stylized_humanoid.py`, `lowpoly_geometry.py` and `build_robot.py`; the builder imports their geometry, rig and export utilities. Running the installed helper without editing it is also supported.

JSON accepts only `height` (0.6–2.5 nominal metres), `build` (`balanced`, `compact`, `sturdy`) and `colour` (#RRGGBB); maximum size 32 KiB. `--build` overrides the JSON build choice. The nominal top height is normalised after proportion changes, and joints are fitted with the same scale; the report measures actual height excluding the tiny sole clearance. Render size is 128–1024. Existing outputs are refused unless `--overwrite` is explicit. `--no-rig` makes a static body; `--no-render` is for nonvisual checks.

Outputs are `<name>.blend`, `.glb`, `-report.json`, four T-pose views and, when rigged, front/side/three-quarter renders of five joint studies. The source opens in rest T-pose with all study tracks muted. Unmute one NLA track to inspect `CheckShoulders`, `CheckElbows`, `CheckKnees`, `CheckHipSpread` or `CheckTwist`; mute it before editing the rest geometry. The GLB includes these static study actions, not Run/Jump/Roll.

## Reuse and edit

Save a new copy of the chosen mannequin in the character's project. Preserve the base original. Keep the skin, rig and future clothing in distinct named collections. Refit both mesh and skeleton after structural edits, then recheck weighting and all affected poses. An existing character with clothes or gameplay clips needs a task-specific preservation/retarget pass; this fresh builder does not overwrite or selectively edit such checkpoints.

Bind-pose checks cover closed manifold edges, connected component count, nonzero face areas, finite coordinates, symmetry and normalised weights. Inspect shoulder, elbow, knee and hip volume visually in the actual exported skin. The mannequin is deliberately simple: a bevelled faceted head, mitten-like palms and broad feet. Its family proportions can be revised after user feedback. A source reference supplies character cues; it does not force a replication target when the user requested original styling.
