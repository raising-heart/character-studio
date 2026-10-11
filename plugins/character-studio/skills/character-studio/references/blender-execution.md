# Blender execution

Use Blender 4.5 LTS or a tested compatible version. Record `blender --version`. Read the installed API or official versioned documentation before using version-sensitive operators.

On Windows, run the bundled discovery helper:

```powershell
$blenderExe = & '<skill-root>\scripts\find_blender.ps1'
& $blenderExe --version
& $blenderExe --background --factory-startup --python-exit-code 1 --python '<skill-root>\scripts\build_robot.py' -- --output '<absolute-output-directory>' --name 'Scout' --height 1.8
```

Substitute resolved absolute paths. Flags before `--` belong to Blender; flags after it belong to the Python script. `--python-exit-code 1` makes Python failures observable to the caller. Wait for completion and inspect exit status and output files. A save log alone does not prove every later step succeeded.

The discovery helper checks `BLENDER_EXECUTABLE`, PATH, `<Codex-home>/plugins/runtimes/character-studio`, and standard Windows Blender install folders. `<Codex-home>` is `CODEX_HOME` when set, otherwise the user's `.codex` directory. On macOS/Linux use `command -v blender` and normal app install paths. If no executable or live MCP connection exists, preserve the design and scripts and report that Blender execution is pending; do not claim a model was generated. Downloading/installing new software is a separate setup action unless the current task authorizes it.

For existing `.blend` files, open a copy in background Blender without `--factory-startup`, use the existing scene structure, save to a new output path, and avoid global deletion. The reference builder deliberately resets only its dedicated test process. Export the character collection or explicit selection, excluding render rigs, floors, debug helpers, and unrelated objects.

Maintain a small editable script/config with named dimensions and colour values. Avoid thousands of unlabelled operators. Apply object rotation/scale before binding; prefer predictable mesh origins and named collections. Keep Blender-space Z-up conventions internally and let Blender's glTF exporter perform its normal Y-up conversion once.

References:
- https://docs.blender.org/api/4.5/
- https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html
- https://download.blender.org/release/
