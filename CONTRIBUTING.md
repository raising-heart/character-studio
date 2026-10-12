# Contributing

Use a branch or fork and open a pull request describing the problem, the resulting behaviour, and how you checked it. Keep skills focused on stylized character creation, animation, export and character effects.

Keep marketplace paths relative to the repository root and keep supporting resources under the plugin. Preserve existing character files and clips. Do not commit credentials, Blender installations, generated character files, Python caches or dependency folders.

For script changes, run the affected starter with the supported Blender version or a compatible Three.js project. Inspect actual renders for visual changes. Check exported clip names and bones rather than assuming Blender names remain unchanged. For runtime effects, check bounded allocations, animation timing, attachment offsets, reduced motion and disposal.

For a release, update `plugins/character-studio/.codex-plugin/plugin.json`, update the changelog and install instructions, verify both skills and the marketplace entry, then tag the commit. Retain the MIT license and attribution.

For robot gait changes, generate a fresh GLB with `build_robot.py`, run `npm install` in the repository, then `npm run test:gait -- /absolute/path/to/Scout.glb`. This maintenance-only test checks both knees and ankles throughout Walk/Run. It does not install runtime dependencies for plugin users; keep visual review alongside the numerical checks.
