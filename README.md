# Character Studio for Codex

Build stylized low-poly Blender characters through editable body, outfit, footwear, face and hair stages, then add motion/effects and prepare GLB assets for browser games.

Character Studio is a community plugin with two Codex skills. It is inspired by Game Studio's design → implementation → asset pipeline → visual review workflow. It is independently authored and is not an official OpenAI or Blender Foundation plugin.

![Blender effects previews: aura, sparks, fire and smoke](docs/images/effects-preview.png)

![Staged humanoid: bald body, outfit, hair/face and actual GLB motion](docs/images/staged-humanoid-preview.png)

## Install

Install [Codex](https://developers.openai.com/codex/) and [Blender 4.5 LTS](https://www.blender.org/download/). Blender is a separate prerequisite; this repository does not include it. The bundled GLB inspector also needs Python 3. Browser effects need Three.js in your game project.

**Easiest: paste this into a Codex chat:**

> Install Character Studio from https://github.com/raising-heart/character-studio. Register its plugin marketplace, install character-studio@character-studio, and verify it is enabled. Locate my Blender executable or help me configure it.

**Or use the Codex CLI:**

```sh
codex plugin marketplace add raising-heart/character-studio --ref main
codex plugin add character-studio@character-studio
```

Start a new Codex chat after installation. If the skills are missing, restart the app. If your CLI supports marketplace registration but has no `plugin add` command, register the marketplace, then select **Character Studio — Community** in the app's Plugins Directory and install **Character Studio**.

For a pinned release, register the marketplace with `--ref v0.5.0` instead of `--ref main`.

The marketplace layout and GitHub registration follow [OpenAI's plugin packaging documentation](https://developers.openai.com/plugins/build/plugins). GitHub distribution is separate from listing in OpenAI's public Plugins Directory.

## Use it

Create a character:

> Use $character-studio to make a stylized low-poly adventurer in Blender: teal and warm yellow, a large readable head, 1.8 m tall, and a budget of 5,000 triangles. Deliver an editable .blend, a GLB, and front, side, back, and three-quarter renders. Add Idle and Walk if practical and verify the export.

Add effects:

> Use $character-effects to add a cyan hand aura and animation-timed sparks to my character. Make Blender previews and integrate separate Three.js effects with the GLB in my browser game.

Create an animal:

> Use $character-studio to make a stylized low-poly fox in Blender, with a readable tail and Idle, Walk, Run and Jump animations. Deliver the editable .blend, GLB, turnarounds and a runtime animation preview.

Be specific about your character's look, intended camera distance, triangle budget, required clips, and target game engine. These are workflows and starter scripts: custom character design still needs iteration and visual review.

### Match an image reference

Attach the reference in a Codex chat and ask:

> Use Character Studio to match this image as a blocky low-poly character. Start with a bald T-pose body, then build clothing, footwear, face and hair as editable parts. Estimate difficulty, inspect stage previews and fix visible issues as you continue. Add Run, Jump and Roll and test the dressed character and exported GLB. Deliver checkpoints, reference comparisons and motion previews.

Staged humanoid construction is the default for suitable stylized characters. The executable starter supports adjustable proportions, jacket/tunic, boots, mesh eyes/brows/mouth and short/braided/bald hair. Each stage has an editable `.blend`, GLB, report and previews. Robot-base remains available for mechanical designs or requested rig prototypes; animals use their own rig. Unsupported forms need task-specific modelling. Difficulty is a subjective effort estimate with reasons, not a success probability or image-match score.

The humanoid has a T-pose skeleton, simple blended weights and neutral-pose-aware Idle/Walk/Run/Jump/Roll. A boot/hair/outfit/face checkpoint edit can preserve unrelated parts and actions. Body proportion changes require a coherent fresh build. The motions are editable prototypes without foot locking or cloth/hair physics; review every final character. See [staged construction](plugins/character-studio/skills/character-studio/references/staged-construction.md), [reference comparisons](plugins/character-studio/skills/character-studio/references/reference-comparison.md) and [build paths](plugins/character-studio/skills/character-studio/references/reference-adaptation.md).

## Included workflows

| Skill | Capabilities |
| --- | --- |
| `$character-studio` | Brief, silhouette and proportions, Blender modelling/materials, optional rigging and animation, GLB export, budget checks and visual review |
| `$character-effects` | Blender mesh-effect previews; Three.js sparks, fire/smoke, dust and magic bursts; bone-attached emitters, auras, simple fading trails, animation cues, bounded particle pools, reduced motion and cleanup |

The Blender robot starter includes a rigid segmented rig, looping **Idle/Walk/Run** and one-shot **Jump/Roll**. The quadruped starter supports **fox/dog/cat** silhouettes with four-leg/tail rigs and **Idle/Walk/Run/Jump**. It is a segmented reference, not an arbitrary animal generator. Birds, snakes, fish and other body plans need custom geometry, rigs and motion.

Jump has baked vertical lift and Roll has visual pivot/ground-clearance offsets. Game controls, collision handling and horizontal travel are separate runtime work. If physics controls jump height, remove the copied Jump clip's Root position track to avoid adding lift twice. See [rigging and runtime integration](plugins/character-studio/skills/character-studio/references/rigging.md) and [animal guidance](plugins/character-studio/skills/character-studio/references/animals.md).

The effects helper adds its collection to a copy of an existing rigged Blender scene and saves a new file. Ordinary work should copy/adapt starter scripts in your own project.

![Actual GLB runtime poses: robot Run, Jump, Roll and quadruped Run](docs/images/motion-preview.png)

### Locate Blender

On Windows, the bundled `find_blender.ps1` checks an explicit executable, `BLENDER_EXECUTABLE`, PATH, standard install folders and a Character Studio portable runtime. You can also tell Codex your executable's absolute path. On macOS/Linux, use your installed Blender executable directly; the discovery helper is Windows-specific.

### Browser effects

Copy [three-character-effects.mjs](plugins/character-studio/skills/character-effects/assets/three-character-effects.mjs) into your game and supply its existing Three.js namespace. See [runtime integration](plugins/character-studio/skills/character-effects/references/runtime-effects.md) for anchors, offsets, animation cues and disposal.

Ship this runtime code/config alongside the character GLB. Blender particles, procedural shaders, compositor glow and fluid simulations do not automatically transfer as live GLB effects. Fire/smoke are stylized puffs; trails are simple lines. Advanced fluids, bloom, wide ribbons and organic/facial rigging require additional work.

## Updates and local development

The [workflow design](docs/staged-character-workflow-plan.md) records the staged implementation and future extensions.

For an installation tracking `main`, refresh the catalog and install the current plugin version:

```sh
codex plugin marketplace upgrade character-studio
codex plugin add character-studio@character-studio
```

Start a new chat afterward. A pinned tag stays on that release until you change its ref. If you already have the original `character-studio-local` installation, choose one source to enable so the duplicate skills do not compete; there is no need to reinstall your working copy just to share this repository.

To edit the source:

```sh
git clone https://github.com/raising-heart/character-studio.git
cd character-studio
codex plugin marketplace add .
codex plugin add character-studio@character-studio
```

This registers your checkout under the same community marketplace name. Edit `plugins/character-studio`, bump the plugin manifest version for a release, and reinstall. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Validation

Version 0.5.0 was checked with Blender 4.5.14 LTS and Three.js 0.186.1. The staged reference study has 3,950 triangles, six meshes, 16 bones and five clips; a second proportion/style variant has 3,094 triangles. Checks cover T-pose binding, both arm/leg chains, finite skinned vertices, ground clearance, clip endpoints, Jump lift, full Roll and one-shot holding. Browser tests cover 75 poses, desktop/mobile rendering and both one-shot completions. Checkpoint tests preserve unrelated geometry, a manual face edit and animation while actually changing the boots. Static output, invalid settings and overwrite/autoexec protections were exercised. Both final animated GLBs pass Khronos validation with zero errors or warnings.

The original robot/animal and effects pipelines retain their earlier validation; the robot/quadruped generators are unchanged, and the effects loader now explicitly disables embedded scripts. Earlier checks include:

- Both skills passed Codex's skill validator.
- Robot GLB: 1,016 triangles, 16 bones, Idle/Walk/Run/Jump/Roll; zero Khronos glTF Validator errors or warnings.
- Fox GLB: 1,184 triangles, 19 bones, Idle/Walk/Run/Jump; zero Khronos glTF Validator errors or warnings. Dog, cat and static-cat generation were also exercised.
- New animation checks covered finite skinned vertices, loop boundaries, faster Run cadence, Jump lift/landing, full Roll rotation, ground clearance and one-shot holding. Both GLBs were rendered in headless Edge at desktop/mobile sizes with zero console errors.
- The 0.3.1 gait regression checks both knees, leading ankles and foot pitch at 65 samples per side in Walk/Run. It rejects the 0.3.0 hyperextended gait and passes the corrected animation.
- The unchanged effects workflow was previously checked with Blender aura/sparks/fire/smoke renders, runtime lifecycle/cap/anchor/cue tests, and headless Edge rendering with reduced motion.

This validation covers the supplied starters, not arbitrary reconstruction. The humanoid face is static, hands are simple mittens, hair is rigid, and body attachment seams/analytic weights need visual review. Review every new character in its destination runtime. The Python GLB inspector is not a complete glTF validator.

## Security and dependencies

The shipped Blender helpers use local files and have no network client, telemetry, credentials, shell execution, install hooks or background service. The new builder uses a bounded JSON schema, refuses accidental overwrites and opens checkpoints with embedded scripts disabled. Optional image comparisons use Python with Pillow; it is not installed automatically. Model generation needs only Blender and bundled scripts. See [security review](plugins/character-studio/SECURITY.md) and [third-party notices](plugins/character-studio/THIRD_PARTY_NOTICES.md). Run `python tests/audit_plugin.py` to repeat static checks; these complement manual review and do not sandbox Blender.

## License and origin

[MIT](LICENSE). Keep the license and [attribution](plugins/character-studio/ATTRIBUTION.md) when sharing modifications. Game Studio is not required. This plugin has no bundled MCP server, API keys or paid-service dependency.
