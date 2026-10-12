# Staged low-poly character workflow — implementation plan

Status: 0.6.1 makes Balanced house-style reference interpretation and one pre-detail blockout feedback checkpoint the defaults, with explicit user overrides. 0.6.0 adds a dedicated connected T-pose base-body foundation with balanced/compact/sturdy forms and joint studies. Balanced is the selected starting style. References inspire identity and costume cues within that style unless reconstruction is explicitly requested. The legacy 0.5 dressed starter remains available, but its clothes and motion do not directly fit the new mannequin. Fitting the later costume/face/hair modules, gameplay motion, A-pose presets, facial animation and secondary motion remains subsequent work. The design below records the broader direction.

## Intended behaviour

A user attaches a character reference and asks Character Studio to build it. For a stylized humanoid, Codex starts with a shaped low-poly body in a neutral pose, then constructs editable clothing, footwear, facial features and hair. It inspects actual Blender renders at each useful checkpoint, repairs observed problems, and validates requested animation on the dressed character and exported GLB.

The visual default is a simple faceted body with a large bevelled head, short neck and substantial limbs, followed by costume geometry and readable face/hair features. Low polygon count does not mean replacing every anatomical part with a cube. Resolve the style intent: the house style translates reference cues into its own body proportions; an explicit reconstruction brief can instead preserve reference ratios. An orc may require a distinct body build.

Keep the robot route available for explicit robots, segmented mechanical designs and fast rig/motion prototypes. Route animals to the quadruped or a tailored species workflow. Preserve existing user assets and explicit build-path choices. For new reference-based designs, show one body-and-outfit blockout and wait for feedback before facial features or hair detail by default. Users may override this with a request to finish without interactive reviews. Continue other checks autonomously; do not add approval at every stage or expand base-only/edit/animation/effects tasks.

## Reference analysis and construction brief

Inspect the actual reference before building. Record:

- Character silhouette and head/body/limb ratios, using visible landmarks and approximate relative measurements rather than guessed precision.
- Body plan, intended game camera, neutral construction pose, requested clips and budget.
- Clothing layers, footwear, facial features, hair masses, accessories and palette.
- Visible evidence versus inferred depth, back view and hidden construction.
- A rough difficulty estimate from 0 easiest to 100 hardest, with reasons and uncertainty. Separate modelling difficulty from motion/deformation difficulty; neither score is a likeness measurement.

For the supplied orange-haired reference, the study should prioritize the large head, compact torso, simple limbs, green jacket silhouette, tall boots and two braids. Model the main character; determine whether orange shapes behind it belong to the costume/body or a separate animal instead of silently attaching them. The forest is staging/background evidence, not character geometry.

Capture the brief in a task-local `character-spec.json` and a short report. Parameters should include height, head ratio, shoulder/hip width, limb lengths, palette, part styles, requested clips and reference assumptions. Keep the schema focused on geometry the builder actually implements. Unsupported styles require task-specific modelling, not a misleading fallback labelled as a match.

## Construction stages and acceptance

| Stage | Work | Evidence needed to continue |
| --- | --- | --- |
| Reference and silhouette | Establish proportions and palette; create a bald body plus optional rough clothing/hair masses for silhouette comparison | Subject is isolated; assumptions are stated; important shapes are represented |
| Base body | Shape head, neck, torso, pelvis, limbs, simple hands and feet; default to T-pose, allowing A-pose when the rig/brief benefits | Front/side/three-quarter views show appropriate proportions and connected-looking joints, without costume hiding errors |
| Early rig check, for animated briefs | Place joints from the body parameters; test shoulders, elbows, hips and knees with simple poses | Both sides bend as intended; bind pose, axes and grounding are coherent |
| Clothing | Add inner garment, outer garment, lower garment and requested accessories as editable parts | Layers have readable thickness and openings; bending does not expose obvious gaps or severe intersections |
| Footwear | Construct shoes/boots and distinctive trim; use economical laces/straps | Feet fit inside; ankle articulation and ground contact work; details read at game scale |
| Face | Add eyes, brows and mouth; add a small nose only if it improves the reference match | Features remain readable at the target camera and in GLB; no floating decals or transparency artifacts |
| Hair | Refine cap, bangs and large strands/braids; add small details only when visible | Outline matches the design; scalp is covered; hair clears shoulders/costume in representative poses |
| Final rig and motion | Update weights and attachments; retarget or author requested clips for final proportions and costume | Every requested clip passes visual review on the dressed character and exported GLB |
| Delivery | Export, inspect in the destination runtime, optimize a separate runtime copy where useful | Editable source and actual runtime asset agree; budgets and unresolved issues are reported |

Stages are dependency-aware, not an inflexible order. Rough hair and clothing masses can be introduced early because they affect silhouette. Detailed facial/hair work waits until body proportions are stable. Static assets skip rig and motion stages.

## Editable parts and checkpoints

Use named Blender collections or object groups for Body, Head, Face, Hair, Outfit, Footwear, Accessories and Rig. The authoring source should support hiding and replacing these groups. Continuous skin needs suitable geometry and blended weights through bend regions; separate editability does not imply rigidly assigning every surface to one bone.

At meaningful stages, save versioned `.blend` checkpoints and labelled renders. Record the changed parts, remaining issues and stage status. Resume from the relevant checkpoint instead of rebuilding the entire character. If proportions or topology change, identify downstream clothing, rig, weights and motions that need rechecking. Preserve manual edits by saving a new copy and rebuilding only designated generated parts; use stable part identifiers.

Provide an automatic mode and a user-requested interactive mode. In automatic mode, inspect and correct issues before continuing. In interactive mode, show the selected stage and await feedback. Cap repeated unsuccessful attempts to fix the same issue, preserve the latest usable checkpoint, and report the specific unresolved problem rather than repeatedly rebuilding everything.

The source may retain separate parts for editing. A runtime copy can combine compatible meshes/materials to reduce draw calls, while retaining skinning and animation. Measure exported counts; do not assume many small objects are cheap merely because they have few triangles.

## Face, hair and materials

Use restrained flat colours and intentional faceted shading for body/clothing. Spend geometry or texture detail on what the game camera can resolve. Aim initially at the existing 2,000–5,000 triangle range, adjusting for the user's requirements and measuring the actual export.

Provide a simple portable face method: a small eye/brow/mouth texture atlas on fitted UV surfaces, or economical mesh features when more suitable. Compare the result in Blender and the GLB viewer. Avoid tiny spherical eyes as the only option for illustrated faces; inspect alpha, depth placement and surface orientation. Facial expressions and facial animation are optional requested work, not implied by adding a readable face.

Build hair as shaped low-poly masses, with supported simple cap/bang and braid patterns. Convert procedural curves or other constructions to portable mesh where required. Use head attachment for rigid hair; add limited secondary bones only when requested motion needs them. Do not claim cloth, hair dynamics or constraints survive GLB without baking or runtime implementation.

## Animation strategy

Retain the robot as a donor/reference and regression fixture, rather than as the visual template for every humanoid. Keep source actions separate from target actions. Test source motion when transferring it, then fit/retarget/rebake onto the character's own neutral pose and skeleton.

The current robot animation uses local rotations tied to its down-facing arm bones and specific leg/foot axes. A T-pose skeleton changes those orientations. Do not call the current animation function on a new skeleton and assume bone names make it compatible. Derive target poses from neutral transforms or implement an explicit retarget mapping, then test the resulting motion.

Check undressed body deformation early and dressed-character motion at the end. Inspect both sides and full cycles, including arm clearance, boot pitch, knee direction, skirt/coat intersections, braid movement, jump landing and roll clearance. Animal gaits require their own acceptance criteria. Recreate a clip when transfer is unsuitable; report requested motions that remain incomplete.

Keep existing guidance for looping versus one-shot clips and baked visual root offsets. Game controls and collisions remain separate runtime tasks. Do not claim foot locking or physical garment simulation unless actually implemented and verified.

## Plugin implementation

1. Update the main skill and reference-adaptation routing so staged low-poly humanoid construction is the default for appropriate character briefs. Add a focused staged-construction reference; keep detailed procedures out of the discovery description.
2. Add `scripts/build_stylized_humanoid.py` with a parameterized bald body and coherent neutral-pose joints. Reuse suitable material/render/export utilities, without changing the validated robot or quadruped outputs accidentally.
3. Add modular supported clothing, footwear, face and hair builders. Support complete builds and stage/part updates using a specification plus an existing checkpoint. Reject unsupported options clearly. Keep work in a task copy rather than installed plugin resources.
4. Implement neutral-pose-aware skinning and motion adaptation. Demonstrate Idle/Walk/Run/Jump/Roll on the new humanoid, with appropriate repairs and limitations.
5. Add stage-aware visual reports and runtime/export checks. Preserve editable source; optimize only a delivery copy where needed.
6. Update metadata, usage prompts and changelog after these resources work. Bump the plugin version, install locally, and test GitHub distribution using the established release workflow.

## Validation and release gate

The next release should demonstrate behaviour, not just valid skill Markdown:

- A reference-guided large-headed humanoid built through body, clothing, footwear, face and hair stages, with actual renders inspected at each stage.
- A second humanoid with different proportions to expose overfitting to the reference.
- A part-edit exercise: change boots or hair from a checkpoint and verify unrelated authored parts and actions remain intact.
- Static and animated export, with named clips, coherent skinning, measured geometry/material counts and Khronos validation.
- Runtime visual review of the dressed humanoid across all requested motion, including both legs and intermediate poses. Numerical checks complement that review.
- Existing robot gait and quadruped checks when shared helpers change; effects checks when effects integration changes.
- Both skill validators, package links/metadata, installed-cache consistency and a clean GitHub-tag install.

Do not announce a tested modular character generator after a documentation-only change. Instruction changes can be reviewed first, but enabling the new default should follow a working builder and representative visual validation.

## First release scope

Prioritize one dependable stylized humanoid pipeline: configurable proportions, T/A neutral pose, simple layered clothing, boots, readable static face, shaped hair with a braid example, checkpoint edits, and validated core motion. Keep robot and quadruped routes accessible. Extend specialized garments, expression rigs, animal-specific modules and dynamic secondary motion after this foundation works.

Example user prompt after implementation:

> Use Character Studio to build a blocky low-poly character from this reference. Start with a bald T-pose body, then build the outfit, boots, face and hair as editable parts. Interpret the reference in our Balanced house style, show the body-and-outfit blockout for feedback before face and hair, and fix observed issues as you continue. Add Run, Jump and Roll; test the dressed character and exported GLB. Deliver the checkpoints, final .blend and GLB, and a brief validation report.
