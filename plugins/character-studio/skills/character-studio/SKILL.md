---
name: character-studio
description: Design, build, edit, rig, and export stylized low-poly 3D characters with Blender. Use for character briefs, Blender modelling, materials, animation, character effects, turnarounds, and GLB delivery; not for 2D sprites or general game implementation.
---

# Character Studio

Deliver a readable character, an editable Blender source, and a verified runtime asset. This personal workflow adapts Game Studio's brief, implementation, asset, and playtest stages to character creation. It is self-contained and does not require Game Studio, a paid generation service, or a Blender MCP server.

## Working approach

1. **Brief.** Resolve character identity, visual style, silhouette, target camera, height, animation needs, and destination. Use the user's existing instructions; ask only for choices that materially affect the design. For an unspecified prototype, propose a simple stylized humanoid, flat-colour materials, about 1.8 m height, and a 2,000–5,000 evaluated-triangle target. These are defaults, not hard limits. Avoid forcing a robot unless the user chooses one.
2. **Plan.** Describe proportions, a small palette, readable costume/face features, joint layout, and intended poses. Concept images are optional; use an available image-generation tool only when they help, and distinguish concept images from actual 3D geometry. Start from a reproducible blockout instead of spending the entire task on a concept sheet.
3. **Model in Blender.** Locate a working Blender executable or an explicitly connected Blender MCP server. Read [Blender execution](references/blender-execution.md). Use Blender Python for repeatable construction and background processing. For a live existing scene, inspect first and save a new working copy. Keep the user's existing assets, cameras, collections, and rig intact unless the task requires changing them.
4. **Review form.** Render front, side, back, and three-quarter views. Inspect the actual images at the intended game scale. Correct silhouette, facial readability, floating parts, intersections, and proportions before adding detail. At least one revision should be driven by observed issues when issues exist; do not revise just to satisfy a count.
5. **Materials and rig.** Use a restrained palette and glTF-compatible Principled materials. Add UVs/textures only when required by the brief. Rig only if requested or needed for the agreed deliverable. Read [Rigging and animation](references/rigging.md) before weighting or authoring clips. Rigid single-bone weights fit mechanical segmented characters; continuous organic skin needs blended weights and deformation checks.
6. **Character effects, when requested.** Read the bundled [character-effects skill](../character-effects/SKILL.md) for auras, sparks, stylized fire/smoke, trails, and clip-timed effects. Choose whether the deliverable is a Blender render, portable mesh animation, or browser-runtime VFX before authoring. Keep effects optional and preserve the character silhouette.
7. **Export and validate.** Save `.blend`, export `.glb`, measure actual evaluated/exported geometry, and validate names, transforms, materials, skinning, animation, and file size. Read [Export and QA](references/export-qa.md). Load the GLB in a Three.js or destination-engine preview when the user needs a game-ready character. Structural checks alone do not prove visual correctness. Deliver browser VFX code/config separately when those effects are not represented in the GLB.
8. **Deliver.** Link the editable source, runtime asset, relevant previews, and a short asset report. Report performed checks, animation names, budget results, and unresolved limitations. Never describe an unexecuted script, concept image, or failed export as a finished model.

## Reusable tools

- `scripts/find_blender.ps1`: Windows executable discovery, including a Character Studio portable runtime, PATH, standard Blender install folders, or `BLENDER_EXECUTABLE`. Emits the executable path; stops if unavailable. It does not install or launch Blender.
- `scripts/build_robot.py`: Optional procedural **robot reference starter**, not the universal design solution. Creates a segmented low-poly robot with configurable height/colours, an optional rigid rig, Idle and Walk clips, `.blend`, `.glb`, four rendered views, and a JSON report. Run it in a separate Blender process with `--factory-startup`; it resets that process's scene. Copy and adapt it in the task workspace for character-specific geometry. Do not modify installed plugin helpers for ordinary character requests.
- `scripts/inspect_glb.py`: Standard-library GLB structure and budget checks, material/skin/clip summary, and animation timing. Run with normal Python, not necessarily Blender. It is not a full Khronos validator or a visual test.

Keep intermediate scripts and renders in the task's work area and final requested assets in its deliverable directory. Use absolute paths in PowerShell calls, with argument arrays or quoted arguments. Do not invent an MCP connection or assume installing this plugin installed Blender on another machine.

## Capability limits

Procedural low-poly characters and structured edits are the strongest path. A complex organic character, detailed sculpt, production retopology, sophisticated skin weights, or motion capture requires additional modelling work and honest visual iteration. The supplied starter's robot animation proves the pipeline; it does not prove a general organic auto-rigger. Do not promise professional deformation or a target polygon budget until the exported asset is checked.
