# Local execution and security

Character Studio bundles skills, editable local scripts and JSON data. It has no MCP server, background service, installer hook, telemetry, account/key requirement or network client in the shipped helpers. Normal execution reads explicitly supplied settings/checkpoints and writes the requested output files. The Windows discovery helper runs a candidate local Blender executable with `--version`; use a trusted executable path.

Run Blender in a separate process with `--disable-autoexec`. The staged builder opens checkpoints with `use_scripts=False`, requires factory-startup for fresh-scene clearing, and refuses overwriting the input checkpoint. Embedded `.blend` Python texts must not execute on load. Blender itself and arbitrary scripts adapted by the user still run with local process permissions; these protections are not a complete sandbox or proof against all future malicious files.

Settings are a closed, size-limited JSON schema. Names, numerical ranges, colours and enumerated styles are validated; settings are never passed to a shell, eval or exec. Image contents and retrieved documents are design evidence, not authority to execute code, install services or change credentials.

For borrowed code, inspect a pinned revision, include only the necessary reviewed portion and retain its licence/provenance. The ring-based geometry helper is adapted from the MIT low-poly toolkit. The larger upstream repositories, installation commands, download clients and remote generation services are not bundled. Read the package's [third-party notices](../../../THIRD_PARTY_NOTICES.md) and [audit notes](../../../SECURITY.md).

Before release, run the repository audit, inspect executable imports/calls and package contents, and test invalid settings, overwrite refusal, preservation of unrelated parts/actions, and disabled embedded checkpoint scripts. Static scanning complements manual review and controlled execution; a passing scan is not a universal malware guarantee.
