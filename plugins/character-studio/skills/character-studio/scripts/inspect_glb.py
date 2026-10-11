"""Inspect uncompressed GLB metadata and storage using Python's standard library."""
import argparse
import json
from pathlib import Path
import struct
import sys


class InvalidAsset(ValueError):
    pass


def inspect(path, max_triangles=None, require_skin=False, required_animations=()):
    raw = Path(path).read_bytes()
    if len(raw) < 20:
        raise InvalidAsset('GLB is too short')
    magic, version, declared_length = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or declared_length != len(raw):
        raise InvalidAsset('GLB header magic, version, or declared length is invalid')
    offset, chunks = 12, []
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise InvalidAsset('Truncated GLB chunk header')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if length % 4 or offset + length > len(raw):
            raise InvalidAsset('Chunk is unaligned or extends beyond the file')
        chunks.append((kind, raw[offset:offset + length]))
        offset += length
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise InvalidAsset('First chunk must be JSON')
    doc = json.loads(chunks[0][1].decode('utf-8'))
    if doc.get('asset', {}).get('version') != '2.0':
        raise InvalidAsset('glTF asset version must be 2.0')
    if sum(kind == 0x4E4F534A for kind, _ in chunks) != 1:
        raise InvalidAsset('Duplicate JSON chunks')
    bins = [data for kind, data in chunks if kind == 0x004E4942]
    if len(bins) > 1:
        raise InvalidAsset('Multiple BIN chunks')
    binary = bins[0] if bins else b''
    errors, warnings = [], []

    def fail(message):
        errors.append(message)

    def reference(key, index, context):
        array = doc.get(key, [])
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(array):
            fail(f'{context}: invalid {key} index {index!r}')
            return None
        return array[index]

    buffers = doc.get('buffers', [])
    for index, buffer in enumerate(buffers):
        if buffer.get('uri'):
            fail(f'buffer {index}: external/data URI resource; expected a self-contained GLB')
        elif index != 0 or not isinstance(buffer.get('byteLength'), int) or not 0 <= len(binary) - buffer['byteLength'] <= 3:
            fail(f'buffer {index}: byteLength does not match padded BIN chunk')
    if binary and not buffers:
        fail('BIN chunk is present without a buffer declaration')
    for index, view in enumerate(doc.get('bufferViews', [])):
        buffer = reference('buffers', view.get('buffer'), f'bufferView {index}')
        start, length = view.get('byteOffset', 0), view.get('byteLength')
        if (not isinstance(start, int) or not isinstance(length, int) or start < 0 or length < 1
                or (buffer and start + length > buffer.get('byteLength', 0))):
            fail(f'bufferView {index}: byte range is invalid')
        stride = view.get('byteStride')
        if stride is not None and (not isinstance(stride, int) or not 4 <= stride <= 252 or stride % 4):
            fail(f'bufferView {index}: byteStride is invalid')
        if view.get('extensions'):
            warnings.append(f'bufferView {index}: extensions are not decoded')
    sizes = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    dimensions = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
    for index, accessor in enumerate(doc.get('accessors', [])):
        count, kind, component = accessor.get('count'), accessor.get('type'), accessor.get('componentType')
        if not isinstance(count, int) or count < 1 or kind not in dimensions or component not in sizes:
            fail(f'accessor {index}: invalid count, type, or componentType')
            continue
        element_size = dimensions[kind] * sizes[component]
        if kind.startswith('MAT'):
            columns = int(kind[-1])
            element_size = columns * ((columns * sizes[component] + 3) // 4 * 4)
        if 'bufferView' in accessor:
            view = reference('bufferViews', accessor['bufferView'], f'accessor {index}')
            if view:
                start = accessor.get('byteOffset', 0)
                stride = view.get('byteStride', element_size)
                if (not isinstance(start, int) or start < 0 or start % sizes[component]
                        or stride < element_size or start + stride * (count - 1) + element_size > view.get('byteLength', 0)):
                    fail(f'accessor {index}: storage extends beyond its view or is misaligned')
        if 'sparse' in accessor:
            sparse = accessor['sparse']
            if not isinstance(sparse.get('count'), int) or not 1 <= sparse['count'] <= count:
                fail(f'accessor {index}: invalid sparse count')
            for field in ('indices', 'values'):
                reference('bufferViews', sparse.get(field, {}).get('bufferView'), f'accessor {index} sparse {field}')
            warnings.append(f'accessor {index}: sparse payload contents are not inspected')

    triangles, vertices, primitives, count_complete = 0, 0, 0, True
    mesh_triangles = []
    for index, mesh in enumerate(doc.get('meshes', [])):
        this_mesh = 0
        for primitive in mesh.get('primitives', []):
            primitives += 1
            attributes = primitive.get('attributes', {})
            position = reference('accessors', attributes.get('POSITION'), f'mesh {index} POSITION')
            for semantic, accessor_index in attributes.items():
                reference('accessors', accessor_index, f'mesh {index} {semantic}')
            if 'material' in primitive:
                reference('materials', primitive['material'], f'mesh {index}')
            indices = reference('accessors', primitive['indices'], f'mesh {index} indices') if 'indices' in primitive else None
            if indices and (indices.get('type') != 'SCALAR' or indices.get('componentType') not in (5121, 5123, 5125)):
                fail(f'mesh {index}: indices must be unsigned integer SCALAR')
            count = (indices or position or {}).get('count', 0)
            vertices += (position or {}).get('count', 0)
            mode = primitive.get('mode', 4)
            if mode == 4:
                if count % 3:
                    fail(f'mesh {index}: TRIANGLES index/vertex count is not divisible by 3')
                this_mesh += count // 3
            elif mode in (5, 6):
                this_mesh += max(0, count - 2)
            elif mode not in (0, 1, 2, 3):
                fail(f'mesh {index}: unknown primitive mode {mode}')
                count_complete = False
            else:
                warnings.append(f'mesh {index}: contains non-triangle primitives')
            if primitive.get('extensions'):
                warnings.append(f'mesh {index}: extension payloads are not decoded; counts use metadata')
        mesh_triangles.append(this_mesh)
        triangles += this_mesh

    instanced_triangles = 0
    for index, node in enumerate(doc.get('nodes', [])):
        for child in node.get('children', []):
            reference('nodes', child, f'node {index} child')
        if 'mesh' in node and reference('meshes', node['mesh'], f'node {index}') is not None:
            instanced_triangles += mesh_triangles[node['mesh']]
        if 'skin' in node:
            skin = reference('skins', node['skin'], f'node {index}')
            if skin and 'mesh' not in node:
                fail(f'node {index}: skin is attached without a mesh')
            if skin and 'mesh' in node:
                mesh = reference('meshes', node['mesh'], f'node {index} skin mesh')
                for primitive in (mesh or {}).get('primitives', []):
                    if not {'JOINTS_0', 'WEIGHTS_0'} <= primitive.get('attributes', {}).keys():
                        fail(f'node {index}: skinned mesh is missing JOINTS_0 or WEIGHTS_0')
    for index, skin in enumerate(doc.get('skins', [])):
        joints = skin.get('joints', [])
        if not joints or len(joints) != len(set(joints)):
            fail(f'skin {index}: joints are empty or duplicated')
        for joint in joints:
            reference('nodes', joint, f'skin {index} joint')
        if 'skeleton' in skin:
            reference('nodes', skin['skeleton'], f'skin {index} skeleton')
        if 'inverseBindMatrices' in skin:
            accessor = reference('accessors', skin['inverseBindMatrices'], f'skin {index} inverse bind')
            if accessor and (accessor.get('type') != 'MAT4' or accessor.get('componentType') != 5126 or accessor.get('count', 0) < len(joints)):
                fail(f'skin {index}: invalid inverse bind matrix accessor')
    for index, image in enumerate(doc.get('images', [])):
        if image.get('uri'):
            fail(f'image {index}: external/data URI; expected an embedded image')
        elif 'bufferView' in image:
            reference('bufferViews', image['bufferView'], f'image {index}')
    for index, scene in enumerate(doc.get('scenes', [])):
        for node in scene.get('nodes', []):
            reference('nodes', node, f'scene {index}')
    if 'scene' in doc:
        reference('scenes', doc['scene'], 'default scene')

    animations = []
    for animation_index, animation in enumerate(doc.get('animations', [])):
        times, sampler_count = [], len(animation.get('samplers', []))
        for sampler in animation.get('samplers', []):
            accessor = reference('accessors', sampler.get('input'), f'animation {animation_index} input')
            reference('accessors', sampler.get('output'), f'animation {animation_index} output')
            if accessor and (accessor.get('type') != 'SCALAR' or accessor.get('componentType') != 5126):
                fail(f'animation {animation_index}: times must be float SCALAR')
            elif accessor and 'bufferView' in accessor and 'sparse' not in accessor:
                view = reference('bufferViews', accessor['bufferView'], 'animation time view')
                if view and view.get('buffer') == 0 and not view.get('extensions'):
                    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
                    stride = view.get('byteStride', 4)
                    try:
                        values = [struct.unpack_from('<f', binary, start + item * stride)[0]
                                  for item in range(accessor['count'])]
                        if any(not value >= 0 or value == float('inf') for value in values) or any(b <= a for a, b in zip(values, values[1:])):
                            fail(f'animation {animation_index}: times must be finite, nonnegative, and strictly increasing')
                        times.extend(values)
                    except struct.error:
                        fail(f'animation {animation_index}: time data is truncated')
        for channel in animation.get('channels', []):
            sampler = channel.get('sampler')
            if not isinstance(sampler, int) or not 0 <= sampler < sampler_count:
                fail(f'animation {animation_index}: invalid channel sampler')
            target = channel.get('target', {})
            if 'node' in target:
                reference('nodes', target['node'], f'animation {animation_index} target')
            if target.get('path') not in ('translation', 'rotation', 'scale', 'weights'):
                fail(f'animation {animation_index}: unsupported target path')
        animations.append({'name': animation.get('name', f'unnamed-{animation_index}'),
                           'channels': len(animation.get('channels', [])),
                           'duration_seconds': max(times) - min(times) if times else None})
    names = {animation['name'] for animation in animations}
    for name in required_animations:
        if name not in names:
            fail(f'Required animation is missing: {name}')
    if require_skin and not any('skin' in node for node in doc.get('nodes', [])):
        fail('Required skin is missing')
    if max_triangles is not None and (not count_complete or triangles > max_triangles or instanced_triangles > max_triangles):
        fail(f'Triangle budget {max_triangles} exceeded or uncountable: meshes={triangles}, instances={instanced_triangles}')
    return {'file': str(Path(path).resolve()), 'bytes': len(raw), 'mesh_triangles': triangles,
            'instanced_triangles': instanced_triangles, 'vertices': vertices, 'primitives': primitives,
            'meshes': len(doc.get('meshes', [])), 'materials': len(doc.get('materials', [])),
            'skins': len(doc.get('skins', [])), 'joint_counts': [len(skin.get('joints', [])) for skin in doc.get('skins', [])],
            'animations': animations, 'count_complete': count_complete,
            'errors': errors, 'warnings': sorted(set(warnings)), 'passed': not errors,
            'scope': 'Core structural/storage checks; not a full glTF validator or visual/deformation test.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset', type=Path)
    parser.add_argument('--max-triangles', type=int)
    parser.add_argument('--require-skin', action='store_true')
    parser.add_argument('--require-animation', action='append', default=[])
    parser.add_argument('--report', type=Path)
    options = parser.parse_args()
    if options.max_triangles is not None and options.max_triangles < 0:
        parser.error('max-triangles must be nonnegative')
    try:
        result = inspect(options.asset, options.max_triangles, options.require_skin, options.require_animation)
    except (OSError, ValueError, TypeError, KeyError, struct.error) as exc:
        result = {'file': str(options.asset), 'passed': False, 'errors': [str(exc)]}
    rendered = json.dumps(result, indent=2)
    if options.report:
        options.report.parent.mkdir(parents=True, exist_ok=True)
        options.report.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
