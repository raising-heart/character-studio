"""Build a stylized segmented fox/dog/cat reference in a dedicated Blender process."""
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_robot as shared
import bpy
from mathutils import Vector


def build_meshes(options, collection):
    scale = options.height
    mats = {'body': shared.material('Coat', options.body_color),
            'accent': shared.material('MuzzleAndSocks', options.accent_color),
            'dark': shared.material('EyesAndNose', '#242932')}
    meshes = []

    def part(name, location, size, colour, bone, sphere=False):
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
            bevel = obj.modifiers.new('Planar bevel', 'BEVEL')
            bevel.width, bevel.segments = min(size) * scale * .12, 1
            bpy.ops.object.modifier_apply(modifier=bevel.name)
        obj.data.materials.append(mats[colour])
        for existing in list(obj.users_collection):
            existing.objects.unlink(obj)
        collection.objects.link(obj)
        obj['character_bone'] = bone
        meshes.append(obj)
        return obj

    part('Body', (0, .02, .59), (.37, .72, .34), 'body', 'Spine')
    part('Haunch', (0, .28, .56), (.38, .27, .32), 'body', 'Pelvis')
    part('Chest', (0, -.28, .6), (.34, .18, .3), 'accent', 'Spine')
    part('Neck', (0, -.36, .69), (.25, .22, .25), 'body', 'Neck')
    part('Head', (0, -.51, .80), (.34, .32, .29), 'body', 'Head')
    muzzle_length = .11 if options.species == 'cat' else (.25 if options.species == 'dog' else .20)
    part('Muzzle', (0, -.68 - muzzle_length / 3, .75), (.23, muzzle_length, .13), 'accent', 'Head')
    part('Nose', (0, -.68 - muzzle_length * .84, .775), (.09, .05, .065), 'dark', 'Head')
    for sign, side in ((1, 'L'), (-1, 'R')):
        part('Eye.' + side, (sign * .145, -.65, .845), (.05, .035, .055), 'dark', 'Head')
        if options.species == 'dog':
            part('Ear.' + side, (sign * .19, -.46, .82), (.08, .17, .25), 'body', 'Head')
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=.11 * scale, radius2=0,
                                           depth=.19 * scale, location=(sign * .105 * scale, -.46 * scale, .98 * scale))
            obj = bpy.context.object
            obj.name = 'Ear.' + side
            obj.data.materials.append(mats['body'])
            for existing in list(obj.users_collection): existing.objects.unlink(obj)
            collection.objects.link(obj); obj['character_bone'] = 'Head'; meshes.append(obj)
        for region, y in (('Front', -.25), ('Hind', .28)):
            suffix = region + '.' + side
            part('Hip.' + suffix, (sign * .17, y, .49), (.065, .065, .065), 'body', 'Upper' + suffix, True)
            part('Upper.' + suffix, (sign * .17, y, .4), (.12, .13, .22), 'body', 'Upper' + suffix)
            part('Knee.' + suffix, (sign * .17, y, .29), (.045, .045, .045), 'dark', 'Lower' + suffix, True)
            part('Lower.' + suffix, (sign * .17, y, .18), (.095, .10, .20), 'accent', 'Lower' + suffix)
            part('Paw.' + suffix, (sign * .17, y - .045, .055), (.14, .20, .11), 'dark', 'Paw' + suffix)
    part('TailBase', (0, .59, .64), (.11, .30, .14), 'body', 'Tail')
    part('TailTip', (0, .85, .70), (.14 if options.species == 'fox' else .075, .30, .16), 'accent', 'TailTip')
    return meshes, mats


def build_rig(options, collection, meshes):
    data = bpy.data.armatures.new(options.name + 'Skeleton')
    rig = bpy.data.objects.new(options.name + 'Rig', data)
    collection.objects.link(rig); rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name, head, tail, parent=None):
        result = data.edit_bones.new(name)
        result.head, result.tail = Vector(head) * options.height, Vector(tail) * options.height
        if parent: result.parent = data.edit_bones[parent]
    bone('Root', (0, 0, 0), (0, 0, .15))
    bone('Pelvis', (0, .28, .5), (0, .28, .65), 'Root')
    bone('Spine', (0, .28, .58), (0, -.28, .58), 'Pelvis')
    bone('Neck', (0, -.28, .58), (0, -.43, .75), 'Spine')
    bone('Head', (0, -.43, .75), (0, -.60, .84), 'Neck')
    bone('Tail', (0, .42, .58), (0, .72, .67), 'Pelvis')
    bone('TailTip', (0, .72, .67), (0, 1.0, .73), 'Tail')
    for sign, side in ((1, 'L'), (-1, 'R')):
        for region, y, parent in (('Front', -.25, 'Spine'), ('Hind', .28, 'Pelvis')):
            suffix = region + '.' + side; x = sign * .17
            bone('Upper' + suffix, (x, y, .49), (x, y, .29), parent)
            bone('Lower' + suffix, (x, y, .29), (x, y, .08), 'Upper' + suffix)
            bone('Paw' + suffix, (x, y, .08), (x, y - .16, .08), 'Lower' + suffix)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in meshes:
        group = obj.vertex_groups.new(name=obj['character_bone'])
        group.add(list(range(len(obj.data.vertices))), 1, 'REPLACE')
        obj.modifiers.new('Character skin', 'ARMATURE').object = rig
    for bone in rig.pose.bones: bone.rotation_mode = 'XYZ'
    return rig


def animate(rig, height):
    rig.animation_data_create(); clips = {}
    for name, end in (('Idle', 49), ('Walk', 33), ('Run', 17), ('Jump', 25)):
        action = bpy.data.actions.new(name); rig.animation_data.action = action
        for frame in range(1, end + 1):
            t = (frame - 1) / (end - 1); phase = t * 2 * math.pi
            for bone in rig.pose.bones:
                bone.location = (0, 0, 0); bone.rotation_euler = (0, 0, 0)
            rig.pose.bones['Tail'].rotation_euler.z = .20 * math.sin(phase)
            rig.pose.bones['TailTip'].rotation_euler.z = .12 * math.sin(phase - .3)
            if name == 'Idle':
                rig.pose.bones['Head'].rotation_euler.x = .035 * math.sin(phase)
            elif name in ('Walk', 'Run'):
                running = name == 'Run'
                rig.pose.bones['Root'].location.y = height * (.025 if running else .008) * (1 - math.cos(phase * 2))
                for region in ('Front', 'Hind'):
                    for side in ('L', 'R'):
                        # Diagonal walk pairs; a compact bounding run with hind/front offset.
                        offset = (0 if side == 'L' else math.pi) + (math.pi if region == 'Hind' else 0)
                        if running: offset = (.12 if side == 'R' else 0) + (.8 * math.pi if region == 'Hind' else 0)
                        swing = math.sin(phase + offset)
                        suffix = region + '.' + side
                        rig.pose.bones['Upper' + suffix].rotation_euler.x = (.60 if running else .32) * swing
                        rig.pose.bones['Lower' + suffix].rotation_euler.x = -(.85 if running else .4) * max(0, -swing)
            else:
                lift = math.sin(math.pi * t)
                rig.pose.bones['Root'].location.y = height * .40 * lift
                for region in ('Front', 'Hind'):
                    for side in ('L', 'R'):
                        rig.pose.bones['Upper' + region + '.' + side].rotation_euler.x = .25 * lift
                        rig.pose.bones['Lower' + region + '.' + side].rotation_euler.x = -.5 * lift
            if name != 'Idle':
                shared.ground_clearance(rig, margin=.001 * height)
            for bone in rig.pose.bones:
                bone.keyframe_insert(data_path='location', frame=frame, group=bone.name)
                bone.keyframe_insert(data_path='rotation_euler', frame=frame, group=bone.name)
        slot = rig.animation_data.action_slot; rig.animation_data.action = None
        track = rig.animation_data.nla_tracks.new(); track.name = name; track.mute = True
        strip = track.strips.new(name, 1, action)
        if hasattr(strip, 'action_slot'): strip.action_slot = slot
        clips[name] = (action, slot)
    rig.animation_data.action, rig.animation_data.action_slot = clips['Idle']
    return {name: {'fps': 24, 'root_motion': False, 'loop': name != 'Jump',
                   'visual_root_offsets': name != 'Idle', 'preview_jump_height_metres': .4 * height if name == 'Jump' else 0}
            for name in clips}


def main():
    options = shared.arguments('Companion', .9, '#D87C32', '#F4DEC1',
                               species_choices=('fox', 'dog', 'cat'), description=__doc__)
    options.preview_span = options.height * 1.9
    shared.generate(options, build_meshes, build_rig, animate,
                    ['Segmented fox/dog/cat reference, not an animal auto-rigger.',
                     'Walk/Run are stylized prototypes without paw locking.',
                     'Jump includes visual vertical lift; game physics must avoid applying it twice.',
                     'Other body plans need custom geometry, rigs and species-specific motion.'],
                    rig_type='rigid segmented quadruped')


if __name__ == '__main__': main()
