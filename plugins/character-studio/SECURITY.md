# Security review and execution scope

## 0.6.0 base-body addition

The connected mannequin builder is newly authored local geometry code. It reuses reviewed adjacent rig/export utilities, accepts a closed JSON schema and requires a dedicated factory-startup Blender process. It does not load user checkpoints, download source meshes, execute shell commands or install services. Generated Blender assets are separate deliverables; the shipped plugin contains the reproducible source and JSON preset, not binary assets or scripts hidden inside `.blend` files.

Repeat the package audit for this version and inspect the helper's imports and file writes. Base-body checks cover static generation, invalid settings, overwrite refusal, connected manifold geometry, symmetry, normalised weights and observable joint-study poses. The existing checkpoint-loader protections are unchanged. This review does not turn Blender into a sandbox or certify arbitrary edited code/assets.

## 0.5.0 review

Reviewed the shipped Python, PowerShell and Three.js helpers, manifest, settings and adapted upstream sources. The new code includes a small reviewed MIT geometry adaptation and rewritten stage/form-review guidance. Full upstream plugins, MCP servers, installers and remote generation clients are excluded. Sources and pinned revisions are recorded in [third-party notices](THIRD_PARTY_NOTICES.md).

Shipped helpers contain no networking, telemetry, credential access, shell subprocess calls, eval/exec or encoded payload loader. They use the Python standard library, Blender modules, adjacent reviewed helpers and, for the optional image-comparison tool, Pillow. No install hooks, bundled binaries or new runtime package manager dependencies are introduced. The Windows discovery helper invokes a selected local Blender executable with `--version`; it neither downloads nor installs it. Runtime VFX uses the caller's Three.js namespace.

The new builder accepts only bounded JSON settings, validates output names, refuses output overwrites by default and prevents replacing its input checkpoint. Fresh scene clearing requires `--factory-startup`. Checkpoint loading and the effects preview helper explicitly use `use_scripts=False`; documented commands also use `--disable-autoexec`.

Controlled tests reject unknown/code-bearing settings, invalid colours, non-finite dimensions, unsupported styles, existing outputs, input/output aliasing and unsupported proportion edits. The part-edit test preserves unrelated objects, a manual face edit and animation keyframes. A fixture with an embedded auto-run Python text loads without creating its controlled marker file. The browser GLB test uses loopback-only assets and records no external requests.

Run `python tests/audit_plugin.py` from the repository to check imports, dynamic execution/network primitives, install hooks, unexpected executable/binary files and per-file hashes. Review the results manually; the audit is a focused regression check, not an antivirus scanner or proof against every possible malicious implementation.

## Boundaries

Blender and user-modified scripts execute with the current user's process permissions. This plugin is not a security sandbox. Verify Blender's source, review new code before running it, and keep auto-execution disabled for untrusted `.blend` files. JSON values and reference images are input data and must not supply instructions for executing programs or accessing accounts.

The review covers the pinned 0.5.0 source and packaged files. It does not endorse later upstream changes, arbitrary downloaded assets, external services, or modifications made after installation. If a future feature needs networking or a new service, document that separately and obtain task-specific authorization rather than adding a silent dependency.
