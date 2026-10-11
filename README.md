# Character Studio for Codex

Design stylized low-poly 3D characters in Blender, add animation and effects, and prepare GLB assets for browser games.

Character Studio is a community plugin with two Codex skills. It is inspired by Game Studio's design → implementation → asset pipeline → visual review workflow. It is independently authored and is not an official OpenAI or Blender Foundation plugin.

![Blender effects previews: aura, sparks, fire and smoke](docs/images/effects-preview.png)

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

For a pinned release, register the marketplace with `--ref v0.2.0` instead of `--ref main`.

The marketplace layout and GitHub registration follow [OpenAI's plugin packaging documentation](https://developers.openai.com/plugins/build/plugins). GitHub distribution is separate from listing in OpenAI's public Plugins Directory.

## Use it

Create a character:

> Use $character-studio to make a stylized low-poly adventurer in Blender: teal and warm yellow, a large readable head, 1.8 m tall, and a budget of 5,000 triangles. Deliver an editable .blend, a GLB, and front, side, back, and three-quarter renders. Add Idle and Walk if practical and verify the export.

Add effects:

> Use $character-effects to add a cyan hand aura and animation-timed sparks to my character. Make Blender previews and integrate separate Three.js effects with the GLB in my browser game.

Be specific about your character's look, intended camera distance, triangle budget, required clips, and target game engine. These are workflows and starter scripts: custom character design still needs iteration and visual review.

## Included workflows

| Skill | Capabilities |
| --- | --- |
| `$character-studio` | Brief, silhouette and proportions, Blender modelling/materials, optional rigging and animation, GLB export, budget checks and visual review |
| `$character-effects` | Blender mesh-effect previews; Three.js sparks, fire/smoke, dust and magic bursts; bone-attached emitters, auras, simple fading trails, animation cues, bounded particle pools, reduced motion and cleanup |

The Blender robot starter includes a rigid segmented rig, Idle and a prototype in-place Walk. The effects helper adds its collection to a copy of an existing rigged Blender scene and saves a new file. Ordinary work should copy/adapt starter scripts in your own project.

### Locate Blender

On Windows, the bundled `find_blender.ps1` checks an explicit executable, `BLENDER_EXECUTABLE`, PATH, standard install folders and a Character Studio portable runtime. You can also tell Codex your executable's absolute path. On macOS/Linux, use your installed Blender executable directly; the discovery helper is Windows-specific.

### Browser effects

Copy [three-character-effects.mjs](plugins/character-studio/skills/character-effects/assets/three-character-effects.mjs) into your game and supply its existing Three.js namespace. See [runtime integration](plugins/character-studio/skills/character-effects/references/runtime-effects.md) for anchors, offsets, animation cues and disposal.

Ship this runtime code/config alongside the character GLB. Blender particles, procedural shaders, compositor glow and fluid simulations do not automatically transfer as live GLB effects. Fire/smoke are stylized puffs; trails are simple lines. Advanced fluids, bloom, wide ribbons and organic/facial rigging require additional work.

## Updates and local development

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

Version 0.2.0 was tested on Windows with Blender 4.5.14 LTS and Three.js 0.186.1:

- Both skills passed Codex's skill validator.
- Robot GLB: 1,016 triangles, 16 bones, Idle/Walk; zero Khronos glTF Validator errors or warnings.
- Blender aura, sparks, fire and smoke presets rendered and were visually inspected.
- Runtime lifecycle, caps/overflow, anchors, seed determinism, trail teleport resets, cue loop crossings and reduced motion passed numerical checks.
- Sparks, fire, smoke, aura and trails rendered in headless Edge with desktop/mobile checks and zero console errors.

This validation covers the supplied starters. Review and test each new character in its destination runtime. The Walk has no foot locking, the robot does not auto-rig organic meshes, and the Python GLB inspector is not a complete glTF validator.

## License and origin

[MIT](LICENSE). Keep the license and [attribution](plugins/character-studio/ATTRIBUTION.md) when sharing modifications. Game Studio is not required. This plugin has no bundled MCP server, API keys or paid-service dependency.
