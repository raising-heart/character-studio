"""Build a reproducible segmented robot in a dedicated Blender process."""
import argparse
import json
import math
from pathlib import Path
import re
import sys

import bpy
from mathutils import Matrix, Vector


def arguments(default_name='Scout', default_height=1.8, default_body='#247D88', default_accent='#F1B646',
              species_choices=None, description=None):
    parser = argparse.ArgumentParser(description=description or __doc__)
    if species_choices:
        parser.add_argument('--species', choices=species_choices, default=species_choices[0])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--name', default=default_name)
    parser.add_argument('--height', type=float, default=default_height)
    parser.add_argument('--body-color', default=default_body)
    parser.add_argument('--accent-color', default=default_accent)
    parser.add_argument('--no-rig', action='store_true')
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--render-size', type=int, default=512)
    parser.add_argument('--overwrite', action='store_true')
    supplied = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    result = parser.parse_args(supplied)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}', result.name):
        parser.error('name must start with a letter and contain only letters, digits, _ or -')
    if not math.isfinite(result.height) or not 0.4 <= result.height <= 4.0:
        parser.error('height must be between 0.4 and 4.0 metres')
    if not 128 <= result.render_size <= 2048:
        parser.error('render-size must be between 128 and 2048')
    for colour in (result.body_color, result.accent_color):
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', colour):
            parser.error('colours must be #RRGGBB')
    result.output = result.output.resolve()
    planned = [result.output / (result.name + suffix) for suffix in ('.blend', '.glb', '-report.json')]
    if not result.no_render:
        planned += [result.output / (result.name + '-' + view + '.png')
                    for view in ('front', 'side', 'back', 'three-quarter')]
    if not result.overwrite and any(path.exists() for path in planned):
        parser.error('output already exists; choose a new directory/name or explicitly use --overwrite')
    return result


def linear_channel(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def material(name, colour, metallic=0.0, emission=False):
    rgb = [linear_channel(int(colour[index:index + 2], 16) / 255) for index in (1, 3, 5)]
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*rgb, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = 0.65
    if emission:
        shader.inputs['Emission Color'].default_value = (*rgb, 1)
        shader.inputs['Emission Strength'].default_value = 1.8
    return result


def build_meshes(options, collection):
    scale = options.height / 1.8
    meshes = []
    mats = {
        'body': material('Body', options.body_color, 0.15),
        'accent': material('Accent', options.accent_color, 0.05),
        'joint': material('Joint', '#28333D', 0.3),
        'eye': material('Eye', '#C1F4E8', emission=True),
    }

    def part(name, location, size, mat, bone, sphere=False):
        if sphere:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        else:
            bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        obj.name = name
        obj.location = Vector(location) * scale
        obj.scale = Vector(size) * scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if not sphere:
            bevel = obj.modifiers.new('Small planar bevel', 'BEVEL')
            bevel.width = min(size) * scale * 0.10
            bevel.segments = 1
            bpy.ops.object.modifier_apply(modifier=bevel.name)
        obj.data.materials.append(mats[mat])
        for existing in list(obj.users_collection):
            existing.objects.unlink(obj)
        collection.objects.link(obj)
        obj['character_bone'] = bone
        meshes.append(obj)
        return obj

    part('Pelvis', (0, 0, .90), (.39, .27, .20), 'joint', 'Pelvis')
    part('Torso', (0, 0, 1.21), (.53, .31, .43), 'body', 'Spine')
    part('ChestPlate', (0, -.173, 1.22), (.29, .055, .24), 'accent', 'Spine')
    part('Neck', (0, 0, 1.485), (.09, .09, .085), 'joint', 'Head', True)
    part('Head', (0, 0, 1.65), (.45, .34, .30), 'body', 'Head')
    part('Visor', (0, -.185, 1.655), (.34, .06, .14), 'joint', 'Head')
    for x in (-.095, .095):
        side = 'L' if x > 0 else 'R'
        part('Eye.' + side, (x, -.221, 1.665), (.068, .021, .050), 'eye', 'Head')
    for direction, side in ((1, 'L'), (-1, 'R')):
        x = direction * .36
        part('Shoulder.' + side, (x, 0, 1.365), (.105, .105, .105), 'accent', 'UpperArm.' + side, True)
        part('UpperArm.' + side, (x, 0, 1.235), (.145, .17, .24), 'body', 'UpperArm.' + side)
        part('Elbow.' + side, (x, 0, 1.08), (.077, .077, .077), 'joint', 'LowerArm.' + side, True)
        part('LowerArm.' + side, (x, 0, .955), (.15, .18, .22), 'accent', 'LowerArm.' + side)
        part('Hand.' + side, (x, -.015, .78), (.15, .18, .14), 'joint', 'Hand.' + side)
        leg_x = direction * .135
        part('Hip.' + side, (leg_x, 0, .83), (.083, .083, .083), 'joint', 'UpperLeg.' + side, True)
        part('UpperLeg.' + side, (leg_x, 0, .65), (.18, .21, .28), 'body', 'UpperLeg.' + side)
        part('Knee.' + side, (leg_x, -.02, .46), (.083, .083, .083), 'joint', 'LowerLeg.' + side, True)
        part('LowerLeg.' + side, (leg_x, 0, .285), (.18, .20, .27), 'accent', 'LowerLeg.' + side)
        part('Foot.' + side, (leg_x, -.065, .085), (.22, .36, .17), 'joint', 'Foot.' + side)
    return meshes, mats


def build_rig(options, collection, meshes):
    scale = options.height / 1.8
    data = bpy.data.armatures.new(options.name + 'Skeleton')
    rig = bpy.data.objects.new(options.name + 'Rig', data)
    collection.objects.link(rig)
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    def bone(name, head, tail, parent=None):
        result = data.edit_bones.new(name)
        result.head = Vector(head) * scale
        result.tail = Vector(tail) * scale
        if parent:
            result.parent = data.edit_bones[parent]
        return result

    bone('Root', (0, 0, 0), (0, 0, .15))
    bone('Pelvis', (0, 0, .83), (0, 0, 1.0), 'Root')
    bone('Spine', (0, 0, 1), (0, 0, 1.45), 'Pelvis')
    bone('Head', (0, 0, 1.45), (0, 0, 1.80), 'Spine')
    for direction, side in ((1, 'L'), (-1, 'R')):
        x = direction * .36
        bone('UpperArm.' + side, (x, 0, 1.365), (x, 0, 1.08), 'Spine')
        bone('LowerArm.' + side, (x, 0, 1.08), (x, 0, .84), 'UpperArm.' + side)
        bone('Hand.' + side, (x, 0, .84), (x, 0, .70), 'LowerArm.' + side)
        leg_x = direction * .135
        bone('UpperLeg.' + side, (leg_x, 0, .83), (leg_x, 0, .46), 'Pelvis')
        bone('LowerLeg.' + side, (leg_x, 0, .46), (leg_x, 0, .14), 'UpperLeg.' + side)
        bone('Foot.' + side, (leg_x, 0, .14), (leg_x, -.25, .14), 'LowerLeg.' + side)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in meshes:
        group = obj.vertex_groups.new(name=obj['character_bone'])
        group.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
        modifier = obj.modifiers.new('Character skin', 'ARMATURE')
        modifier.object = rig
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = 'XYZ'
    return rig


def ground_clearance(rig, margin=0):
    """Lift a reference rig's Z-aligned Root enough to clear evaluated mesh bounds."""
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    skinned = [obj.evaluated_get(graph) for obj in bpy.context.scene.objects if obj.type == 'MESH'
               and any(mod.type == 'ARMATURE' and mod.object == rig for mod in obj.modifiers)]
    low = min((obj.matrix_world @ Vector(corner)).z for obj in skinned for corner in obj.bound_box)
    rig.pose.bones['Root'].location.y += max(0, margin - low)


def animate(rig, height):
    rig.animation_data_create()
    clips = {}
    for name, end_frame in (('Idle', 49), ('Walk', 25), ('Run', 17), ('Jump', 25), ('Roll', 25)):
        action = bpy.data.actions.new(name)
        rig.animation_data.action = action
        for frame in range(1, end_frame + 1):
            t = (frame - 1) / (end_frame - 1)
            phase = 2 * math.pi * (frame - 1) / (end_frame - 1)
            for bone in rig.pose.bones:
                bone.location = (0, 0, 0)
                bone.rotation_euler = (0, 0, 0)
            if name == 'Idle':
                rig.pose.bones['Pelvis'].location.y = .006 * height * (1 - math.cos(phase))
                rig.pose.bones['Spine'].rotation_euler.y = .025 * math.sin(phase)
                rig.pose.bones['Head'].rotation_euler.z = .035 * math.sin(phase)
            elif name in ('Walk', 'Run'):
                running = name == 'Run'
                rig.pose.bones['Pelvis'].location.y = (.025 if running else .008) * height * (1 - math.cos(phase * 2))
                rig.pose.bones['Spine'].rotation_euler.x = .12 if running else 0
                for direction, side in ((1, 'L'), (-1, 'R')):
                    swing = direction * math.sin(phase)
                    hip = (.70 if running else .40) * swing
                    # These down-facing leg bones flex the knee backward at positive local X.
                    # Recover the trailing heel; extend the leading leg without hyperextension.
                    knee = (.12 if running else .06) + (.95 if running else .42) * max(0, swing)
                    rig.pose.bones['UpperLeg.' + side].rotation_euler.x = hip
                    rig.pose.bones['LowerLeg.' + side].rotation_euler.x = knee
                    # The forward-facing foot bone has the opposite local X axis.
                    # Counter the shin pitch, retaining a small toe-down recovery pose.
                    rig.pose.bones['Foot.' + side].rotation_euler.x = hip + knee - (.25 if running else .10) * max(0, swing)
                    rig.pose.bones['UpperArm.' + side].rotation_euler.x = -(.65 if running else .28) * swing
                    rig.pose.bones['LowerArm.' + side].rotation_euler.x = -.70 if running else -.10
            elif name == 'Jump':
                lift = math.sin(math.pi * (t - .2) / .6) if .2 < t < .8 else 0
                crouch = math.sin(math.pi * t / .2) if t < .2 else (math.sin(math.pi * (t - .8) / .2) if t > .8 else 0)
                rig.pose.bones['Root'].location.y = .32 * height * lift
                rig.pose.bones['Pelvis'].location.y = -.07 * height * crouch
                for side in ('L', 'R'):
                    rig.pose.bones['UpperLeg.' + side].rotation_euler.x = .35 * crouch + .22 * lift
                    rig.pose.bones['LowerLeg.' + side].rotation_euler.x = -.7 * crouch - .45 * lift
                    rig.pose.bones['UpperArm.' + side].rotation_euler.x = -.8 * lift + .25 * crouch
                    rig.pose.bones['LowerArm.' + side].rotation_euler.x = -.4 * lift
            else:
                tuck = math.sin(math.pi * t) ** .5
                angle = 2 * math.pi * t
                root = rig.pose.bones['Root']
                root.rotation_euler.x = angle
                # Rotate about a body-height pivot, rather than the ground origin.
                pivot = Vector((0, 0, .55 * height))
                delta = pivot - Matrix.Rotation(angle, 3, 'X') @ pivot
                root.location = rig.data.bones['Root'].matrix_local.to_3x3().inverted() @ delta
                rig.pose.bones['Spine'].rotation_euler.x = .35 * tuck
                for side in ('L', 'R'):
                    rig.pose.bones['UpperLeg.' + side].rotation_euler.x = 1.05 * tuck
                    rig.pose.bones['LowerLeg.' + side].rotation_euler.x = -1.5 * tuck
                    rig.pose.bones['UpperArm.' + side].rotation_euler.x = -.9 * tuck
                    rig.pose.bones['LowerArm.' + side].rotation_euler.x = -1.1 * tuck
            if name != 'Idle':
                ground_clearance(rig, margin=.001 * height)
            for bone in rig.pose.bones:
                bone.keyframe_insert(data_path='rotation_euler', frame=frame, group=bone.name)
                bone.keyframe_insert(data_path='location', frame=frame, group=bone.name)
        slot = rig.animation_data.action_slot
        rig.animation_data.action = None
        track = rig.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, action)
        if hasattr(strip, 'action_slot'):
            strip.action_slot = slot
        track.mute = True
        clips[name] = (action, slot, end_frame)
    rig.animation_data.action = clips['Idle'][0]
    rig.animation_data.action_slot = clips['Idle'][1]
    return {name: {'first_frame': 1, 'last_frame': value[2], 'fps': 24, 'root_motion': False,
                   'loop': name in ('Idle', 'Walk', 'Run'),
                   'visual_root_offsets': name != 'Idle',
                   'preview_jump_height_metres': .32 * height if name == 'Jump' else 0}
            for name, value in clips.items()}


def staging(options):
    scene = bpy.context.scene
    stage = bpy.data.collections.new('PreviewStage')
    scene.collection.children.link(stage)
    floor_mat = material('PreviewFloor', '#DDE6E9')
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = bpy.context.object
    floor.name = 'PreviewFloor'
    floor.location.z = -.006
    floor.data.materials.append(floor_mat)
    for col in list(floor.users_collection):
        col.objects.unlink(floor)
    stage.objects.link(floor)
    for name, position, energy, size in (
            ('Key', (3, -4, 5), 650, 4), ('Fill', (-4, -2, 3), 400, 5), ('Rim', (1, 4, 4), 700, 3)):
        data = bpy.data.lights.new(name, 'AREA')
        lighting_scale = options.height / 1.8
        data.energy, data.size = energy * lighting_scale ** 2, size * lighting_scale
        light = bpy.data.objects.new(name, data)
        stage.objects.link(light)
        light.location = Vector(position) * (options.height / 1.8)
        light.rotation_euler = (Vector((0, 0, options.height * .5)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('CharacterPreview')
    camera = bpy.data.objects.new('CharacterPreview', data)
    stage.objects.link(camera)
    span = getattr(options, 'preview_span', options.height)
    data.type, data.ortho_scale = 'ORTHO', span * 1.25
    target = Vector((0, 0, options.height * .48))
    camera.location = target + Vector((4, -6, 2.2)) * options.height
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = options.render_size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    if not scene.world:
        scene.world = bpy.data.worlds.new('PreviewWorld')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.20, .24, .28, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
    return camera


def generate(options, mesh_builder, rig_builder, animator, limitations, rig_type='rigid segmented'):
    options.output.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 49
    character = bpy.data.collections.new(options.name)
    scene.collection.children.link(character)
    meshes, mats = mesh_builder(options, character)
    bpy.ops.object.select_all(action='DESELECT')
    rig = None if options.no_rig else rig_builder(options, character, meshes)
    clips = {} if rig is None else animator(rig, options.height)
    scene.frame_set(1)
    camera = staging(options)
    outputs = {'blend': str(options.output / (options.name + '.blend')),
               'glb': str(options.output / (options.name + '.glb'))}
    bpy.ops.wm.save_as_mainfile(filepath=outputs['blend'])
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes + ([rig] if rig else []):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig or meshes[0]
    export_args = {'filepath': outputs['glb'], 'export_format': 'GLB', 'use_selection': True,
                   'export_animations': rig is not None, 'export_skins': rig is not None,
                   'export_yup': True, 'export_cameras': False, 'export_lights': False}
    available = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_animation_mode' in available:
        export_args['export_animation_mode'] = 'ACTIONS'
    if 'export_force_sampling' in available:
        export_args['export_force_sampling'] = True
    bpy.ops.export_scene.gltf(**export_args)
    previews = {}
    if not options.no_render:
        target = Vector((0, 0, options.height * .48))
        for name, direction in (('front', (0, -6, 0)), ('side', (6, 0, 0)),
                                ('back', (0, 6, 0)), ('three-quarter', (4, -6, 2.2))):
            camera.location = target + Vector(direction) * options.height
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(options.output / (options.name + '-' + name + '.png'))
            bpy.ops.render.render(write_still=True)
            previews[name] = scene.render.filepath
        bpy.ops.wm.save_as_mainfile(filepath=outputs['blend'])
    depsgraph = bpy.context.evaluated_depsgraph_get()
    triangle_count = 0
    for obj in meshes:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        triangle_count += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    report = {'name': options.name, 'blender_version': bpy.app.version_string,
              'character_height_metres': options.height, 'mesh_objects': len(meshes),
              'evaluated_triangles': triangle_count, 'materials': list(mats),
              'bone_count': len(rig.data.bones) if rig else 0, 'clips': clips,
              'rig_type': rig_type if rig else 'static',
              'outputs': outputs, 'previews': previews,
              'glb_bytes': Path(outputs['glb']).stat().st_size,
              'limitations': limitations}
    report_path = options.output / (options.name + '-report.json')
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CHARACTER_STUDIO_RESULT ' + json.dumps(report))


def main():
    generate(arguments(), build_meshes, build_rig, animate,
             ['Rigid robot reference; not an organic auto-rigger.',
              'Walk/Run are in-place prototypes without foot locking.',
              'Jump/Roll are one-shot visual clips; Jump includes baked vertical lift.',
              'Game controls, collisions and horizontal movement are separate runtime work.'])


if __name__ == '__main__':
    main()
