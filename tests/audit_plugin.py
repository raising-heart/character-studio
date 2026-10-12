"""Release audit for the shipped package; manual review remains required."""
import ast
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent.parent
plugin = root / 'plugins/character-studio'
allowed_imports = {'argparse', 'json', 'math', 'pathlib', 're', 'sys', 'types', 'struct',
                   'bpy', 'bmesh', 'mathutils', 'build_robot', 'build_stylized_humanoid', 'lowpoly_geometry', 'PIL', 'random'}
forbidden_calls = {'eval', 'exec', 'compile', '__import__', 'system', 'popen'}
files = []
for path in sorted(plugin.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts:
        continue
    assert path.suffix in ('.py', '.ps1', '.mjs', '.json', '.md', '.yaml') or path.name == 'LICENSE', ('unexpected shipped file', path)
    source = path.read_text(encoding='utf-8')
    if path.suffix == '.py':
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module]
                assert all(m.split('.')[0] in allowed_imports for m in modules), (path, modules)
            if isinstance(node, ast.Call):
                call = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                assert call not in forbidden_calls, (path, call)
    if path.suffix == '.mjs':
        assert not re.search(r'\b(?:fetch|eval|WebSocket|XMLHttpRequest)\s*\(|new\s+Function\b|child_process|node:net', source), path
    if path.suffix == '.ps1':
        assert not re.search(r'Invoke-Expression|Invoke-WebRequest|Invoke-RestMethod|Start-Process|DownloadString|EncodedCommand', source, re.I), path
    if path.suffix == '.json':
        json.loads(source)
    files.append({'path': path.relative_to(plugin).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
manifest = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
assert 'mcpServers' not in manifest and 'hooks' not in manifest
package = json.loads((root / 'package.json').read_text())
assert not set(package.get('scripts', {})) & {'preinstall', 'install', 'postinstall', 'prepare'}
assert package.get('dependencies', {}) == {}, 'No plugin runtime npm dependencies expected'
print(json.dumps({'passed': True, 'version': manifest['version'], 'files': files,
                  'checks': ['Python imports and dynamic execution', 'JS network/dynamic execution', 'PowerShell download/eval/process hooks', 'manifest server/hooks', 'npm install hooks', 'unexpected binary files'],
                  'scope': 'Static checks of bundled resources; does not replace manual review or sandbox Blender.'}, indent=2))
