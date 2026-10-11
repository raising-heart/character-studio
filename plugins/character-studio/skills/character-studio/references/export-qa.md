# Export and QA

Save editable `.blend` before exporting. Export explicit selected character objects to GLB with materials, normals, skinning and requested animation enabled. Exclude staging floors, render cameras and lights. Use Blender's documented glTF material subset and inspect converted materials; complex procedural shaders do not automatically become portable textures.

Run the bundled GLB inspection script using a regular Python executable:

```powershell
& '<python-executable>' '<skill-root>\scripts\inspect_glb.py' '<asset.glb>' --max-triangles 5000 --require-skin --require-animation Idle --require-animation Walk --report '<asset-report.json>'
```

Omit skin/clip requirements for static characters. A budget threshold is a task choice, not a universal cap. The triangle count sums exported mesh primitives once and separately reports scene-instanced triangles. Vertex counts can increase at hard-normal, UV, and material boundaries. Check both geometry counts and runtime draw calls; a low-triangle asset with many small meshes is still expensive.

The helper verifies GLB framing, buffers, buffer views, accessor storage, core references, supported primitive counts, basic skeleton data, animation references/timing, required clips, and optional geometry budgets. It detects external resources. It does not replace the full Khronos glTF Validator, decode geometry compression, evaluate poses, check every glTF extension, or prove visuals. Compressed assets that the helper cannot count must be checked with an appropriate decoder/validator rather than receiving a false passing budget.

Visual acceptance:
- front / side / back / three-quarter images match the design and read at gameplay scale;
- dimensions, grounding, origin, and conversion are correct;
- intended hard/smooth shading, normals, materials, and transparency render correctly;
- requested clips exist, loop correctly, and move the intended parts;
- the actual GLB loads in the target engine, with shadows and camera distance representative of use;
- final file sizes and geometry/material counts match the agreed budget.

For browser assets, reuse Game Studio's delivery principles: GLB/glTF 2.0, consistent units/pivots/names, intentional texture budgets, optional glTF Transform optimization, and runtime verification after export. Do not substitute export-only success for a playtest.

References:
- https://docs.blender.org/manual/en/4.5/addons/import_export/scene_gltf2.html
- https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- https://gltf-transform.dev/
