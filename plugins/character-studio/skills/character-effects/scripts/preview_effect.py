"""Add editable stylized mesh VFX to a copy of a Blender character scene."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--kind', choices=('aura', 'sparks', 'fire', 'smoke'), default='aura')
    parser.add_argument('--bone', default='Head')
    parser.add_argument('--rig')
    parser.add_argument('--offset', type=float, nargs=3, default=(0, 0, 0), metavar=('X', 'Y', 'Z'),
                        help='Attachment offset in bone-local coordinates')
    parser.add_argument('--frames', default='1,13,25')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--render-size', type=int, default=384)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    args.input = args.input.resolve()
    args.output = args.output.resolve()
    if not args.input.is_file() or args.input.suffix.lower() != '.blend':
        parser.error('input must be an existing .blend file')
    try:
        frames = sorted(set(int(value.strip()) for value in args.frames.split(',')))
    except ValueError:
        parser.error('frames must be comma-separated integers')
    if not frames or len(frames) > 12 or min(frames) < 0 or max(frames) > 10000:
        parser.error('provide 1..12 frames in range 0..10000')
    if not 128 <= args.render_size <= 2048:
        parser.error('render-size must be 128..2048')
    if not all(math.isfinite(value) for value in args.offset):
        parser.error('offset must contain finite numbers')
    stem = 'effects-' + args.kind
    blend_path = args.output / (stem + '.blend')
    report_path = args.output / (stem + '-report.json')
    images = [args.output / f'{stem}-{frame:04d}.png' for frame in frames]
    if blend_path == args.input:
        parser.error('input and output .blend must be different files')
    if not args.overwrite and any(path.exists() for path in [blend_path, report_path, *images]):
        parser.error('output exists; choose a new folder or explicitly use --overwrite')
    bpy.ops.wm.open_mainfile(filepath=str(args.input))
    scene = bpy.context.scene
    candidates = [obj for obj in scene.objects if obj.type == 'ARMATURE' and (not args.rig or obj.name == args.rig)]
    if len(candidates) != 1:
        parser.error('scene needs one armature; use --rig to disambiguate')
    rig = candidates[0]
    if args.bone not in rig.pose.bones:
        parser.error(f'bone {args.bone!r} was not found')
    if not scene.camera:
        parser.error('input scene needs a preview camera')
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    effects = bpy.data.collections.new('CharacterStudioEffects-' + args.kind)
    scene.collection.children.link(effects)
    rng = random.Random(args.seed)
    character_meshes = [obj for obj in scene.objects if obj.type == 'MESH' and
                        any(mod.type == 'ARMATURE' and mod.object == rig for mod in obj.modifiers)]
    corners = [obj.matrix_world @ Vector(corner) for obj in character_meshes for corner in obj.bound_box]
    character_height = max(.1, max(point.z for point in corners) - min(point.z for point in corners)) if corners else 1.8
    radius = .20 * character_height

    def anchor():
        bpy.context.view_layer.update()
        return rig.matrix_world @ rig.pose.bones[args.bone].matrix @ Vector(args.offset)

    def mat(name, colour, strength=0, opacity=1):
        material = bpy.data.materials.new(name)
        material.diffuse_color = (*colour, opacity)
        material.use_nodes = True
        shader = material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*colour, 1)
        shader.inputs['Roughness'].default_value = .7
        shader.inputs['Alpha'].default_value = opacity
        shader.inputs['Emission Color'].default_value = (*colour, 1)
        shader.inputs['Emission Strength'].default_value = strength
        return material

    def move_to_effects(obj):
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        effects.objects.link(obj)
        return obj

    start, end = min(frames), max(max(frames), min(frames) + 24)
    fps = scene.render.fps / scene.render.fps_base
    scene.frame_set(start)
    origin = anchor().copy()
    if args.kind == 'aura':
        bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=6,
            major_radius=radius, minor_radius=radius * .065)
        ring = move_to_effects(bpy.context.object)
        ring.name = 'AuraRing'
        ring.data.materials.append(mat('AuraEmission', (.05, .65, 1), 3))
        for frame in range(start, end + 1):
            scene.frame_set(frame)
            ring.location = anchor()
            pulse = 1 + .06 * math.sin((frame - start) / fps * math.pi)
            ring.scale = (pulse, pulse, pulse)
            ring.keyframe_insert(data_path='location', frame=frame)
            ring.keyframe_insert(data_path='scale', frame=frame)
    else:
        smoke = args.kind == 'smoke'
        particles = 24 if args.kind == 'sparks' else 18
        for number in range(particles):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
            puff = move_to_effects(bpy.context.object)
            puff.name = args.kind.title() + f'Puff-{number:02d}'
            colour = (.35, .40, .44) if smoke else ((1, .32 + rng.random() * .40, .025))
            puff.data.materials.append(mat(puff.name + 'Material', colour, 0 if smoke else 3, .45 if smoke else 1))
            direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(.35, 1)))
            speed = radius * (2.5 if args.kind == 'sparks' else .6)
            lifetime = rng.uniform(.55, .95) if args.kind == 'sparks' else rng.uniform(.8, 1.5)
            phase = rng.uniform(0, lifetime) if args.kind != 'sparks' else 0
            size = radius * (.035 if args.kind == 'sparks' else .22)
            for frame in range(start, end + 1):
                scene.frame_set(frame)
                elapsed = (frame - start) / fps
                age = elapsed + phase
                if args.kind != 'sparks':
                    age %= lifetime
                fraction = min(1, age / lifetime)
                # Sparks use their birth position; persistent puffs are an illustrative attached preview.
                base = origin if args.kind == 'sparks' else anchor()
                gravity = -radius * 2 if args.kind == 'sparks' else radius * .5
                puff.location = base + direction * speed * age + Vector((0, 0, .5 * gravity * age * age))
                envelope = max(.001, 1 - fraction)
                scale = size * ((1 + fraction * 2) * envelope if smoke else envelope)
                puff.scale = (scale, scale, scale * (1.5 if args.kind == 'fire' else 1))
                puff.keyframe_insert(data_path='location', frame=frame)
                puff.keyframe_insert(data_path='scale', frame=frame)
    scene.frame_start = min(scene.frame_start, start)
    scene.frame_end = max(scene.frame_end, end)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = args.render_size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    for frame, path in zip(frames, images):
        scene.frame_set(frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    scene.frame_set(start)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report = {'kind': args.kind, 'input': str(args.input), 'output_blend': str(blend_path),
              'attachment': {'rig': rig.name, 'bone': args.bone, 'offset': args.offset}, 'seed': args.seed,
              'frames': frames, 'renders': [str(path) for path in images],
              'effect_objects': len(effects.objects), 'blender_version': bpy.app.version_string,
              'delivery': 'Editable Blender mesh preview; no GLB export or fluid simulation.',
              'limitations': ['Emission is not compositor bloom.',
                              'Persistent Blender puffs follow the attachment as a visual sketch; browser particles use scene-space births.']}
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CHARACTER_EFFECTS_RESULT ' + json.dumps(report))


if __name__ == '__main__':
    main()
