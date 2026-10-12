# Staged low-poly humanoid construction

Start new stylized humanoids with [Character Base Body](../../character-base-body/SKILL.md). Establish the intended house style and review the mannequin before dressing it. References can guide identity, clothing, hair and palette while the body uses the chosen original style; exact reconstruction is an explicit alternative brief.

The executable stages below describe the **legacy 0.5 dressed humanoid starter**. Its clothing, face, hair and motion do not automatically fit the new connected mannequin. Keep it for compatible existing characters or explicit requests. A low-poly budget still needs shaped surfaces and visual review. Estimate modelling and motion effort separately and identify hidden-view assumptions.

## Stages and feedback

1. **Body:** bald head, neck, shaped torso/pelvis, continuous limb strips and simple hands/feet in T-pose. Inspect front/profile/three-quarter proportions. For animation, fit the skeleton now and check both sides with basic bends before clothing hides defects. The starter overlaps separate body submeshes at neck/shoulder/hip attachments; inspect those transitions and author continuous topology where the brief needs it.
2. **Outfit:** add fitted inner/outer garments and lower garment. Check collar/armholes, thickness, layers and silhouette. Keep rough hair/clothing volumes early if they materially affect silhouette.
3. **Footwear:** shape shafts, heel, instep, toe and sole; add only readable trim/laces. Check ankle movement and foot contact, without enlarging the boots through detail.
4. **Face:** readable eyes/brows/mouth; check placement and skin continuity from front and profile. Mesh features are the starter option; a portable face atlas is an alternative when it better matches the brief. Facial expressions/rigging need additional work.
5. **Hair:** cap, bangs and major masses first, then braids/tufts. Check coverage and shoulder clearance. The helper's hair is rigidly head-weighted; add/bake secondary motion only when needed and test it.
6. **Animation:** adapt timing/poses to the final body, clothes and hair. Test the dressed mesh and exported GLB across every requested clip. The helper authors motion using neutral-pose world rotations converted to each bone's local basis; it does not blindly reuse robot arm axes.

Run a useful stage, open the real renders, fix an observed issue, and continue. A single `--stage all` build creates checkpoints but does not perform visual review for Codex: inspect intermediate evidence rather than claiming it was validated. Save a new output directory for each revision. Stop repeated attempts on the same unresolved defect after three failed repairs, preserve the usable checkpoint, and explain the remaining work. User approval at each stage is optional interactive mode, not the automatic default.

## Builder commands

Copy `build_stylized_humanoid.py`, `lowpoly_geometry.py` and `build_robot.py` together into the task workspace. Use an absolute Blender path and explicit local settings:

```text
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python <task>/build_stylized_humanoid.py -- --output <new-output> --name Adventurer --spec <task>/character-spec.json --stage body
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python <task>/build_stylized_humanoid.py -- --input <new-output>/Adventurer-body.blend --output <next-output> --name Adventurer --spec <task>/character-spec.json --stage outfit
```

Continue with `footwear`, `face`, `hair`, then `animation`. Without `--input`, a selected stage builds its prerequisite geometry. With `--input`, it regenerates only the named stage. `--stage all` on a checkpoint preserves the base body and regenerates subsequent stages; it is unsuitable when those generated stages contain manual edits that must be kept. `--no-rig` is supported for fresh static builds; the final stage is then hair. Use `--no-render` for nonvisual checks only. Render size is bounded to 128–1024. Existing outputs are refused unless `--overwrite` is explicit; the input checkpoint cannot be an output destination.

Each stage saves `<name>-<stage>.blend`, `.glb`, a report and relevant render views. Final animated delivery is `<name>-animation.*`. Named mesh groups are Body, Head, Outfit, Footwear, Face and Hair, with a separate rig. Requested-stage regeneration replaces that generated group, preserving unrelated groups, objects and actions. It does not merge manual edits inside the replaced group.

## Supported JSON settings

The optional spec is bounded JSON data (32 KiB maximum). Unknown keys/styles, invalid colours and non-finite numbers are rejected. Supported settings:

| Setting | Range/choices |
| --- | --- |
| height | 0.6–2.5 nominal metres; measure actual height after proportion changes |
| head_scale | 0.75–1.25 |
| body_width | 0.8–1.3 |
| leg_length | 0.8–1.2 |
| boot_width | 0.8–1.35 |
| outfit_style | jacket, tunic |
| hair_style | braids, short, bald |
| palette | skin, hair, outfit, trim, shirt, lower, boots, white, iris, dark, gold; #RRGGBB |

Use the bundled braided-adventurer JSON as a supported-form example, not as a mandatory design. Clothing/hair outside the listed options require adapting the task copy or direct Blender work.

Checkpoint updates can change boot_width/boots for footwear, hair_style/hair for hair, outfit_style/outfit/trim/shirt/lower for outfit, and iris for face. Shared palette colours require updating all affected stages. Height/head/body/leg changes require a fresh full build because joints, fit, weights and animation depend on them. Arbitrary existing rigs and anatomy need a custom adaptation workflow.

## Acceptance

Review the bald body, fitted outfit/boots and final face/hair from consistent views. Compare reference and model with acknowledged camera/pose differences; no invented likeness percentage. For animation, inspect shoulders, hips, elbows, both knees, boot pitch and garment/hair intersections at intermediate frames, loops and one-shot endings. Check the actual GLB in the destination runtime. The starter's analytic weights and motion are editable prototypes without foot locking, cloth simulation, finger bones or facial animation.
