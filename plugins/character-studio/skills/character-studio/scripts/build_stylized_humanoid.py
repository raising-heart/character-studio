"""Staged, local-only low-poly humanoid builder with checkpoint part edits.

Run in background Blender with --factory-startup --disable-autoexec.
Settings are bounded JSON data, never Python code. No external services.
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_robot import material, staging
from lowpoly_geometry import ellipsoid, face_patch, garment_shell, loft, rod

STAGES = ('body', 'outfit', 'footwear', 'face', 'hair', 'animation')
DEFAULT = {
    'height': 1.6, 'head_scale': 1.0, 'body_width': 1.0, 'leg_length': 1.0,
    'boot_width': 1.0, 'hair_style': 'braids', 'outfit_style': 'jacket',
    'palette': {'skin': '#FFD3AF', 'hair': '#F5743C', 'outfit': '#3B5541',
                'trim': '#718267', 'shirt': '#E78554', 'lower': '#A19170',
                'boots': '#B9453E', 'white': '#FFF8E7', 'iris': '#689337',
                'dark': '#44352E', 'gold': '#E9B956'},
}
LIMITATIONS = ['Parameterized stylized starter, not arbitrary image reconstruction.',
               'Simple mitten hands and static mesh face; no individual fingers or facial rig.',
               'Prototype locomotion without foot locking or cloth/hair physics.',
               'Rigid head details; skin has simple analytic weights requiring character-specific review.',
               'Body-proportion changes require a new full build; checkpoint edits preserve unrelated parts.',
               'Jump has baked vertical lift; Roll offsets are visual, not gameplay travel.']


def validated_spec(raw, base=None):
    if not isinstance(raw, dict) or set(raw) - set(DEFAULT):
        raise ValueError('spec must be an object with supported keys only')
    result = dict(DEFAULT if base is None else base)
    result['palette'] = dict(result['palette'])
    for key, bounds in {'height': (.6, 2.5), 'head_scale': (.75, 1.25), 'body_width': (.8, 1.3),
                        'leg_length': (.8, 1.2), 'boot_width': (.8, 1.35)}.items():
        value = raw.get(key, result[key])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not bounds[0] <= value <= bounds[1]:
            raise ValueError(f'{key} must be finite and within {bounds}')
        result[key] = value
    for key, choices in {'hair_style': ('braids', 'short', 'bald'), 'outfit_style': ('jacket', 'tunic')}.items():
        value = raw.get(key, result[key])
        if value not in choices:
            raise ValueError(f'{key} must be one of {choices}')
        result[key] = value
    palette = raw.get('palette', {})
    if not isinstance(palette, dict) or set(palette) - set(DEFAULT['palette']):
        raise ValueError('unsupported palette entries')
    for key, value in palette.items():
        if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise ValueError('palette colours must be #RRGGBB')
        result['palette'][key] = value
    return result


def read_spec(path, base=None):
    if path is None:
        return validated_spec({}, base)
    if path.stat().st_size > 32768:
        raise ValueError('spec exceeds 32 KiB')
    return validated_spec(json.loads(path.read_text(encoding='utf-8-sig')), base)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--name', default='Adventurer')
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--input', type=Path, help='previous checkpoint; opened with embedded scripts disabled')
    parser.add_argument('--stage', choices=(*STAGES, 'all'), default='all')
    parser.add_argument('--no-rig', action='store_true')
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--render-size', type=int, default=384)
    parser.add_argument('--overwrite', action='store_true')
    supplied = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    args = parser.parse_args(supplied)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}', args.name):
        parser.error('name must start with a letter and use letters, digits, _ or -')
    if not 128 <= args.render_size <= 1024:
        parser.error('render-size must be 128–1024')
    args.output = args.output.resolve()
    if args.input:
        args.input = args.input.resolve()
        if args.input.suffix.lower() != '.blend' or not args.input.is_file():
            parser.error('input must be an existing .blend checkpoint')
    if args.no_rig and args.stage == 'animation':
        parser.error('animation needs a rig')
    return args


class Builder:
    def __init__(self, args, spec):
        self.args, self.spec = args, spec
        self.scale = spec['height'] / 1.6
        self.width = spec['body_width']
        self.leg_delta = .35 * (spec['leg_length'] - 1)
        self.owner = args.name
        self.rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE' and o.get('cs_owner') == self.owner), None)
        self.materials = {}
        for key, colour in spec['palette'].items():
            name = self.owner + '_' + key
            existing = bpy.data.materials.get(name)
            self.materials[key] = existing or material(name, colour)
            if existing:
                from build_robot import linear_channel
                rgb = tuple(linear_channel(int(colour[i:i + 2], 16) / 255) for i in (1, 3, 5))
                existing.diffuse_color = (*rgb, 1)
                existing.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1)
        self.points = self.joints()

    def z(self, value):
        return value + self.leg_delta if value > .43 else value

    def joints(self):
        z, w = self.z, self.width
        points = {'Root': ((0, 0, 0), (0, 0, .12), None),
                  'Pelvis': ((0, 0, z(.77)), (0, 0, z(.95)), 'Root'),
                  'Spine': ((0, 0, z(.95)), (0, 0, z(1.16)), 'Pelvis'),
                  'Head': ((0, 0, z(1.16)), (0, 0, z(1.52)), 'Spine')}
        for sign, side in ((1, 'L'), (-1, 'R')):
            shoulder = .17 * w
            points.update({
                'UpperArm.' + side: ((sign * shoulder, 0, z(1.10)), (sign * (shoulder + .23), 0, z(1.10)), 'Spine'),
                'LowerArm.' + side: ((sign * (shoulder + .23), 0, z(1.10)), (sign * (shoulder + .43), 0, z(1.10)), 'UpperArm.' + side),
                'Hand.' + side: ((sign * (shoulder + .43), 0, z(1.10)), (sign * (shoulder + .52), 0, z(1.10)), 'LowerArm.' + side),
                'UpperLeg.' + side: ((sign * .10 * w, 0, z(.77)), (sign * .10 * w, 0, .43), 'Pelvis'),
                'LowerLeg.' + side: ((sign * .10 * w, 0, .43), (sign * .10 * w, 0, .085), 'UpperLeg.' + side),
                'Foot.' + side: ((sign * .10 * w, 0, .085), (sign * .10 * w, -.16, .085), 'LowerLeg.' + side),
            })
        return points

    def collection(self, stage):
        name = self.owner + '_' + stage.title()
        collection = bpy.data.collections.get(name)
        if collection is None:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
        return collection

    def remove_stage(self, stage):
        for obj in list(bpy.data.objects):
            if obj.get('cs_owner') == self.owner and obj.get('cs_stage') == stage:
                bpy.data.objects.remove(obj, do_unlink=True)

    def weights(self, obj, rule):
        for vertex in obj.data.vertices:
            x, y, z = vertex.co
            weights = {}
            if rule.startswith('arm:'):
                side = rule.split(':')[1]
                along = abs(x) - .17 * self.width
                blend = max(0, min(1, (along - .19) / .08))
                hand = max(0, min(1, (along - .405) / .05))
                weights = {'UpperArm.' + side: (1 - blend) * (1 - hand), 'LowerArm.' + side: blend * (1 - hand), 'Hand.' + side: hand}
            elif rule.startswith('leg:'):
                side = rule.split(':')[1]
                blend = max(0, min(1, (.47 - z) / .08))
                weights = {'UpperLeg.' + side: 1 - blend, 'LowerLeg.' + side: blend}
            elif rule == 'torso':
                blend = max(0, min(1, (z - self.z(.86)) / .16))
                weights = {'Pelvis': 1 - blend, 'Spine': blend}
            elif rule == 'skirt':
                side = 'L' if x >= 0 else 'R'
                blend = max(0, min(.65, (self.z(.79) - z) / .22))
                weights = {'Pelvis': 1 - blend, 'UpperLeg.' + side: blend}
            else:
                weights = {rule: 1}
            for bone, value in weights.items():
                if value > 0:
                    group = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
                    group.add([vertex.index], value, 'REPLACE')

    def tag(self, obj, stage, rule):
        self.weights(obj, rule)
        for vertex in obj.data.vertices:
            vertex.co *= self.scale
        obj['cs_owner'], obj['cs_stage'] = self.owner, stage
        obj['cs_generated'] = True
        return obj

    def profile(self, name, stage, values, colour, rule, axis=(0, 0, 1), segments=10, flat=False):
        return self.tag(loft(name, values, self.collection(stage), self.materials[colour], segments, axis, flat), stage, rule)

    def bead(self, name, stage, centre, radii, colour, rule, segments=10, rows=5):
        return self.tag(ellipsoid(name, centre, radii, self.collection(stage), self.materials[colour], segments, rows), stage, rule)

    def line(self, name, stage, start, end, radius, colour, rule):
        return self.tag(rod(name, start, end, radius, self.collection(stage), self.materials[colour]), stage, rule)

    def patch(self, name, centre, outline, colour):
        return self.tag(face_patch(name, centre, outline, self.collection('face'), self.materials[colour]), 'face', 'Head')

    def body(self):
        z, w = self.z, self.width
        self.profile('Body', 'body', [((0, 0, z(h)), a * w, b) for h, a, b in
                     ((.72, .105, .07), (.79, .145, .085), (.88, .12, .075), (.95, .125, .075), (1.06, .16, .09), (1.12, .17, .08), (1.16, .085, .045))], 'skin', 'torso')
        self.profile('Neck', 'body', [((0, 0, z(h)), r, r) for h, r in ((1.13, .045), (1.23, .055))], 'skin', 'Head', segments=8)
        hs = self.spec['head_scale']
        self.profile('Head', 'body', [((0, 0, z(1.20) + (h - 1.20) * hs), a * hs, b * hs) for h, a, b in
                     ((1.20, .055, .075), (1.235, .12, .12), (1.30, .175, .14), (1.40, .19, .14), (1.49, .17, .13), (1.54, .11, .085))], 'skin', 'Head', segments=12, flat=True)
        for sign, side in ((1, 'L'), (-1, 'R')):
            shoulder = .17 * w
            self.profile('Arm.' + side, 'body', [((sign * (shoulder + a), 0, z(1.10)), b, c) for a, b, c in
                         ((-.02, .055, .065), (.08, .05, .055), (.19, .041, .043), (.23, .042, .043), (.27, .039, .043), (.38, .032, .035), (.43, .027, .03))], 'skin', 'arm:' + side, axis=(1, 0, 0), segments=8)
            self.bead('Hand.' + side, 'body', (sign * (shoulder + .475), -.005, z(1.10)), (.06, .029, .038), 'skin', 'Hand.' + side, segments=8, rows=4)
            self.profile('Leg.' + side, 'body', [((sign * .10 * w, 0, h), a, b) for h, a, b in
                         ((z(.77), .075, .077), (z(.67), .07, .075), (.49, .05, .055), (.43, .047, .05), (.39, .049, .052), (.26, .045, .05), (.085, .032, .034))], 'skin', 'leg:' + side, segments=8)
            self.profile('Foot.' + side, 'body', [((sign * .10 * w, -.06, h), a, b) for h, a, b in
                         ((.012, .05, .115), (.06, .053, .115), (.09, .035, .07))], 'skin', 'Foot.' + side, segments=8)

    def outfit(self):
        z, w = self.z, self.width
        self.profile('Shirt', 'outfit', [((0, 0, z(h)), a * w, b) for h, a, b in
                     ((.77, .14, .092), (.91, .137, .093), (1.08, .174, .105), (1.135, .115, .066))], 'shirt', 'torso', segments=12, flat=True)
        profiles = [(z(h), a * w, b) for h, a, b in ((.77, .19, .115), (.88, .158, .11), (1.01, .174, .113), (1.11, .187, .108), (1.14, .13, .076))]
        obj = garment_shell('Jacket', profiles, self.collection('outfit'), self.materials['outfit'], opening=.38 if self.spec['outfit_style'] == 'jacket' else .08)
        self.tag(obj, 'outfit', 'torso')
        for sign, side in ((1, 'L'), (-1, 'R')):
            shoulder = .17 * w
            self.profile('Sleeve.' + side, 'outfit', [((sign * (shoulder + a), 0, z(1.10)), b, c) for a, b, c in
                         ((-.02, .069, .076), (.10, .062, .067), (.19, .053, .054), (.23, .052, .055), (.27, .051, .054), (.36, .045, .047), (.415, .047, .049))], 'outfit', 'arm:' + side, axis=(1, 0, 0), segments=8)
            self.line('JacketEdge.' + side, 'outfit', (sign * .07 * w, -.111, z(.79)), (sign * .07 * w, -.106, z(1.10)), .009, 'trim', 'torso')
        lower = garment_shell('LowerGarment', [(z(.65), .183 * w, .118), (z(.72), .178 * w, .108), (z(.81), .154 * w, .097)], self.collection('outfit'), self.materials['lower'], thickness=.005)
        self.tag(lower, 'outfit', 'skirt')
        self.profile('Belt', 'outfit', [((0, 0, z(h)), .155 * w, .103) for h in (.805, .825)], 'dark', 'Pelvis', segments=12)
        self.bead('Buckle', 'outfit', (0, -.109, z(.82)), (.028, .009, .024), 'gold', 'Pelvis', segments=8, rows=3)

    def footwear(self):
        width = self.spec['boot_width']
        for sign, side in ((1, 'L'), (-1, 'R')):
            x = sign * .10 * self.width
            self.profile('BootShaft.' + side, 'footwear', [((x, 0, z), a * width, b) for z, a, b in
                         ((.075, .045, .055), (.15, .048, .062), (.28, .061, .073), (.405, .063, .077))], 'boots', 'LowerLeg.' + side, segments=8, flat=True)
            self.profile('BootFoot.' + side, 'footwear', [((x, y, z), a * width, b) for z, y, a, b in
                         ((.008, -.075, .06, .15), (.035, -.078, .066, .15), (.075, -.07, .059, .138), (.11, -.025, .045, .08))], 'boots', 'Foot.' + side, segments=10)
            self.profile('Sole.' + side, 'footwear', [((x, -.078, z), .066 * width, .152) for z in (.004, .024)], 'dark', 'Foot.' + side, segments=10)
            for index in range(5):
                bottom = .13 + index * .046
                for direction in (-1, 1):
                    self.line('Lace.' + side, 'footwear', (x - direction * .036 * width, -.080, bottom), (x + direction * .036 * width, -.080, bottom + .038), .003, 'white', 'LowerLeg.' + side)

    def head_z(self, value):
        return self.z(1.20) + (value - 1.20) * self.spec['head_scale']

    def face(self):
        hs = self.spec['head_scale']
        almond = [(-.047, 0), (-.031, -.029), (.023, -.031), (.044, 0), (.024, .034), (-.025, .034)]
        for sign, side in ((1, 'L'), (-1, 'R')):
            x, z = sign * .076 * hs, self.head_z(1.365)
            def scaled(points, factor=1):
                return [(a * hs * factor, b * hs * factor) for a, b in points]
            self.patch('EyeOutline.' + side, (x, -.143 * hs, z), scaled(almond, 1.08), 'dark')
            self.patch('EyeWhite.' + side, (x, -.145 * hs, z), scaled(almond), 'white')
            for name, radius, colour, y in (('Iris', .025, 'iris', -.147), ('Pupil', .013, 'dark', -.149)):
                circle = [(radius * math.cos(math.tau * i / 12), radius * 1.12 * math.sin(math.tau * i / 12)) for i in range(12)]
                self.patch(name + '.' + side, (x, y * hs, z), scaled(circle), colour)
            self.patch('EyeHighlight.' + side, (x - .008 * hs, -.151 * hs, z + .012 * hs), scaled([(-.008, -.008), (.008, -.008), (.008, .008), (-.008, .008)]), 'white')
            self.patch('Brow.' + side, (x, -.146 * hs, z + .055 * hs), scaled([(-.036, -.002), (.033, -.003), (.028, .009), (-.029, .011)]), 'dark')
        self.patch('Mouth', (0, -.142 * hs, self.head_z(1.275)), [(-.024 * hs, .005 * hs), (0, -.004 * hs), (.023 * hs, .004 * hs), (0, .001 * hs)], 'dark')

    def hair(self):
        if self.spec['hair_style'] == 'bald':
            return
        hs = self.spec['head_scale']
        hz = self.head_z
        self.bead('HairCap', 'hair', (0, .008 * hs, hz(1.50)), (.205 * hs, .164 * hs, .10 * hs), 'hair', 'Head', segments=12, rows=5)
        back = garment_shell('BackHair', [(hz(1.24), .18 * hs, .145 * hs), (hz(1.44), .204 * hs, .162 * hs), (hz(1.51), .184 * hs, .14 * hs)], self.collection('hair'), self.materials['hair'], opening=1.03, thickness=.006, segments=10)
        self.tag(back, 'hair', 'Head')
        for index in range(9):
            x = (index - 4) * .037 * hs
            bottom = hz(1.435 + (.016 if index % 3 == 0 else 0))
            self.profile('Bang', 'hair', [((x, -.150 * hs, bottom), .013 * hs, .009 * hs), ((x, -.150 * hs, hz(1.505)), .023 * hs, .015 * hs)], 'hair', 'Head', segments=6)
        if self.spec['hair_style'] == 'braids':
            for sign, side in ((1, 'L'), (-1, 'R')):
                self.bead('HairTuft.' + side, 'hair', (sign * .171 * hs, 0, hz(1.54)), (.05 * hs, .046 * hs, .052 * hs), 'hair', 'Head', segments=8, rows=4)
                for index in range(7):
                    x = sign * (.193 * hs + (.014 if index % 2 else -.005))
                    centre = (x, -.047, hz(1.33) - index * .057)
                    self.bead('Braid.' + side, 'hair', centre, (.032, .035, .044), 'hair', 'Head', segments=6, rows=3)
                self.bead('HairTie.' + side, 'hair', (sign * .201 * hs, -.047, hz(1.33) - .34), (.034, .037, .012), 'gold', 'Head', segments=6, rows=3)

    def create_rig(self):
        if self.args.no_rig:
            return
        data = bpy.data.armatures.new(self.owner + 'Skeleton')
        self.rig = bpy.data.objects.new(self.owner + 'Rig', data)
        self.collection('rig').objects.link(self.rig)
        self.rig['cs_owner'] = self.owner
        self.rig.show_in_front = True
        bpy.ops.object.select_all(action='DESELECT')
        self.rig.select_set(True)
        bpy.context.view_layer.objects.active = self.rig
        bpy.ops.object.mode_set(mode='EDIT')
        for name, (head, tail, parent) in self.points.items():
            bone = data.edit_bones.new(name)
            bone.head, bone.tail = Vector(head) * self.scale, Vector(tail) * self.scale
            bone.align_roll(Vector((0, 1, 0)))
            if parent:
                bone.parent = data.edit_bones[parent]
        bpy.ops.object.mode_set(mode='OBJECT')
        for bone in self.rig.pose.bones:
            bone.rotation_mode = 'QUATERNION'

    def bind(self):
        if self.rig:
            for obj in self.meshes():
                modifier = next((m for m in obj.modifiers if m.type == 'ARMATURE'), None) or obj.modifiers.new('Character skin', 'ARMATURE')
                modifier.object = self.rig
                obj.parent = self.rig

    def meshes(self):
        return [o for o in bpy.data.objects if o.type == 'MESH' and o.get('cs_owner') == self.owner]

    def consolidate(self, stage):
        objs = [o for o in self.meshes() if o.get('cs_stage') == stage]
        if not objs:
            return
        # Preserve weighted head/body as named subparts; collapse repetitive detail draw calls.
        groups = {}
        for obj in objs:
            key = ('Head' if obj.name.startswith(('Head', 'Neck')) else 'Body') if stage == 'body' else stage.title()
            groups.setdefault(key, []).append(obj)
        for key, group in groups.items():
            bpy.ops.object.select_all(action='DESELECT')
            for obj in group:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            if len(group) > 1:
                bpy.ops.object.join()
            obj = bpy.context.object
            obj.name = self.owner + '_' + key
            obj['cs_owner'], obj['cs_stage'], obj['cs_generated'] = self.owner, stage, True

    def animate(self):
        if not self.rig:
            raise ValueError('animation requires an existing rigged checkpoint')
        rig = self.rig
        rig.animation_data_create()
        for track in list(rig.animation_data.nla_tracks):
            if track.name in ('Idle', 'Walk', 'Run', 'Jump', 'Roll'):
                rig.animation_data.nla_tracks.remove(track)
        rig.animation_data.action = None
        identity = Quaternion()
        rx = lambda angle: Quaternion((1, 0, 0), angle)
        ry = lambda angle: Quaternion((0, 1, 0), angle)
        clips = {}
        for name, last in (('Idle', 49), ('Walk', 25), ('Run', 17), ('Jump', 25), ('Roll', 25)):
            action = bpy.data.actions.new(self.owner + '_' + name)
            action['cs_owner'], action['cs_clip'] = self.owner, name
            rig.animation_data.action = action
            for frame in range(1, last + 1):
                t = (frame - 1) / (last - 1)
                phase = math.tau * t
                desired = {'Root': identity.copy(), 'Pelvis': identity.copy(), 'Spine': identity.copy(), 'Head': identity.copy()}
                root_delta = Vector((0, 0, 0))
                lift = crouch = tuck = 0
                if name in ('Walk', 'Run'):
                    root_delta.z = (.014 if name == 'Walk' else .028) * (1 - math.cos(phase * 2)) * self.scale
                    desired['Spine'] = rx(.08 if name == 'Run' else 0)
                    desired['Head'] = desired['Spine']
                elif name == 'Jump':
                    lift = math.sin(math.pi * (t - .2) / .6) if .2 < t < .8 else 0
                    crouch = math.sin(math.pi * t / .2) if t < .2 else math.sin(math.pi * (t - .8) / .2) if t > .8 else 0
                    root_delta.z = (.42 * lift - .045 * crouch) * self.scale
                elif name == 'Roll':
                    tuck = math.sin(math.pi * t) ** .5
                    desired['Root'] = rx(math.tau * t)
                    pivot = Vector((0, 0, .62 * self.scale))
                    root_delta = pivot - desired['Root'] @ pivot
                    desired['Spine'] = rx(.25 * tuck)
                    desired['Head'] = desired['Spine']
                root = desired['Root']
                desired['Pelvis'] = root.copy()
                desired['Spine'] = root @ desired['Spine']
                desired['Head'] = root @ desired['Head']
                for sign, side in ((1, 'L'), (-1, 'R')):
                    swing = sign * math.sin(phase)
                    hip, knee, arm, elbow = 0, .05, 0, -.10
                    if name in ('Walk', 'Run'):
                        running = name == 'Run'
                        hip = (.56 if running else .32) * swing
                        knee = .05 + (.92 if running else .42) * max(0, swing)
                        arm, elbow = -hip * .8, -.55 if running else -.16
                    elif name == 'Jump':
                        hip, knee, arm, elbow = -.35 * crouch + .12 * lift, .05 + .7 * crouch + .28 * lift, -.5 * lift, -.10 - .2 * lift
                    elif name == 'Roll':
                        hip, knee, arm, elbow = -.75 * tuck, .05 + 1.25 * tuck, -.6 * tuck, -.10 - .7 * tuck
                    down = ry(sign * math.pi / 2)
                    desired['UpperArm.' + side] = desired['Spine'] @ rx(arm) @ down
                    desired['LowerArm.' + side] = desired['Spine'] @ rx(arm + elbow) @ down
                    desired['Hand.' + side] = desired['LowerArm.' + side]
                    desired['UpperLeg.' + side] = root @ rx(hip)
                    desired['LowerLeg.' + side] = root @ rx(hip + knee)
                    desired['Foot.' + side] = root.copy()
                for bone in rig.pose.bones:
                    parent_rotation = desired[bone.parent.name] if bone.parent else identity
                    rest = bone.bone.matrix_local.to_quaternion()
                    bone.rotation_quaternion = rest.inverted() @ parent_rotation.inverted() @ desired[bone.name] @ rest
                    bone.location = (0, 0, 0)
                root_bone = rig.pose.bones['Root']
                root_bone.location = root_bone.bone.matrix_local.to_3x3().inverted() @ root_delta
                bpy.context.view_layer.update()
                graph = bpy.context.evaluated_depsgraph_get()
                low = min((obj.matrix_world @ vertex.co).z for source in self.meshes() for obj in [source.evaluated_get(graph)] for vertex in obj.data.vertices)
                root_bone.location += root_bone.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, max(0, .001 * self.scale - low)))
                for bone in rig.pose.bones:
                    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=bone.name)
                    bone.keyframe_insert(data_path='location', frame=frame, group=bone.name)
            slot = rig.animation_data.action_slot
            rig.animation_data.action = None
            track = rig.animation_data.nla_tracks.new()
            track.name = name
            strip = track.strips.new(name, 1, action)
            if hasattr(strip, 'action_slot'):
                strip.action_slot = slot
            track.mute = True
            clips[name] = {'first_frame': 1, 'last_frame': last, 'fps': 24, 'loop': name in ('Idle', 'Walk', 'Run'), 'root_motion': False, 'visual_root_offsets': name != 'Idle'}
        return clips

    def rest_pose(self):
        if self.rig:
            if self.rig.animation_data:
                self.rig.animation_data.action = None
            for bone in self.rig.pose.bones:
                bone.rotation_quaternion = Quaternion()
                bone.location = (0, 0, 0)
        bpy.context.view_layer.update()

    def export(self, path):
        bpy.ops.object.select_all(action='DESELECT')
        meshes = self.meshes()
        for obj in meshes + ([self.rig] if self.rig else []):
            obj.select_set(True)
        bpy.context.view_layer.objects.active = self.rig or meshes[0]
        parents = [(obj, obj.parent, obj.matrix_world.copy()) for obj in meshes]
        try:
            # glTF skinned meshes should be roots; skin modifiers still identify the rig.
            for obj, parent, world in parents:
                obj.parent = None
                obj.matrix_world = world
            bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                                      export_animations=bool(self.rig), export_skins=bool(self.rig),
                                      export_yup=True, export_cameras=False, export_lights=False,
                                      export_animation_mode='NLA_TRACKS', export_force_sampling=True)
        finally:
            for obj, parent, world in parents:
                obj.parent = parent
                obj.matrix_world = world

    def checkpoint(self, stage, clips):
        scene = bpy.context.scene
        scene['cs_spec_json'] = json.dumps(self.spec)
        scene['cs_owner'] = self.owner
        scene['cs_clips_json'] = json.dumps(clips)
        stem = self.args.output / (self.owner + '-' + stage)
        self.rest_pose()
        bpy.ops.wm.save_as_mainfile(filepath=str(stem) + '.blend')
        self.export(Path(str(stem) + '.glb'))
        previews = {}
        if not self.args.no_render:
            camera = scene.camera
            target = Vector((0, 0, self.spec['height'] * .49))
            for view, direction in [('front', (0, -6, 0)), ('side', (6, 0, 0)), ('back', (0, 6, 0)), ('three-quarter', (4, -6, 1.4))]:
                if stage not in ('body', 'hair', 'animation') and view in ('side', 'back'):
                    continue
                camera.location = target + Vector(direction) * self.spec['height']
                camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
                scene.render.filepath = str(stem) + '-' + view + '.png'
                bpy.ops.render.render(write_still=True)
                previews[view] = scene.render.filepath
        triangles = 0
        for obj in self.meshes():
            obj.data.calc_loop_triangles()
            triangles += len(obj.data.loop_triangles)
        report = {'name': self.owner, 'stage': stage, 'spec': self.spec, 'blender_version': bpy.app.version_string,
                  'mesh_objects': len(self.meshes()), 'evaluated_triangles': triangles,
                  'bone_count': len(self.rig.data.bones) if self.rig else 0, 'clips': clips,
                  'outputs': {'blend': str(stem) + '.blend', 'glb': str(stem) + '.glb'},
                  'previews': previews, 'limitations': LIMITATIONS,
                  'glb_bytes': Path(str(stem) + '.glb').stat().st_size}
        Path(str(stem) + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('CHARACTER_STUDIO_RESULT ' + json.dumps(report))
        return report


def main():
    args = arguments()
    if args.input:
        if 'use_scripts' not in bpy.ops.wm.open_mainfile.get_rna_type().properties:
            raise RuntimeError('Blender does not expose safe checkpoint loading')
        bpy.ops.wm.open_mainfile(filepath=str(args.input), use_scripts=False, load_ui=False)
        if bpy.context.scene.get('cs_owner') != args.name:
            raise ValueError('checkpoint character name does not match --name')
        base = validated_spec(json.loads(bpy.context.scene['cs_spec_json']))
        spec = read_spec(args.spec, base)
        if args.stage == 'body' or any(spec[key] != base[key] for key in ('height', 'head_scale', 'body_width', 'leg_length')):
            raise ValueError('body/proportion edits require a new full build; choose a fresh output')
        allowed_changes = {'footwear': {'boot_width', 'boots'}, 'hair': {'hair_style', 'hair'},
                           'outfit': {'outfit_style', 'outfit', 'trim', 'shirt', 'lower'},
                           'face': {'iris'}, 'animation': set(), 'all': set(spec) | set(spec['palette'])}
        changed = {key for key in spec if key != 'palette' and spec[key] != base[key]}
        changed |= {key for key in spec['palette'] if spec['palette'][key] != base['palette'][key]}
        if changed - allowed_changes[args.stage]:
            raise ValueError('spec changes affect other stages; request all or separate relevant updates')
    else:
        if bpy.data.filepath or '--factory-startup' not in sys.argv:
            raise ValueError('fresh build requires a factory-startup process, or --input for an existing checkpoint')
        spec = read_spec(args.spec)
        # Only a fresh dedicated process may clear its initial default scene.
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    stages = list(STAGES if args.stage == 'all' else STAGES[:STAGES.index(args.stage) + 1]) if not args.input else list(STAGES[1:] if args.stage == 'all' else [args.stage])
    if args.no_rig:
        stages = [stage for stage in stages if stage != 'animation']
    planned = []
    for stage in stages:
        stem = args.output / (args.name + '-' + stage)
        planned += [Path(str(stem) + suffix) for suffix in ('.blend', '.glb', '-report.json')]
        if not args.no_render:
            planned += [Path(str(stem) + '-' + view + '.png') for view in ('front', 'side', 'back', 'three-quarter')]
    if args.input and args.input in [p.resolve() for p in planned]:
        raise ValueError('input checkpoint must not be overwritten; choose a different output directory')
    if not args.overwrite and any(path.exists() for path in planned):
        raise ValueError('outputs exist; choose a fresh directory or explicitly use --overwrite')
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 49
    builder = Builder(args, spec)
    if args.input and args.no_rig and builder.rig:
        raise ValueError('a rigged checkpoint cannot be changed to static by a part edit; make a fresh --no-rig build')
    if not args.input:
        options = SimpleNamespace(height=spec['height'], render_size=args.render_size, preview_span=spec['height'] * 1.10)
        staging(options)
    scene.render.resolution_x = scene.render.resolution_y = args.render_size
    scene.cycles.samples = 8
    scene.view_settings.view_transform = 'Standard'
    # Neutral lighting should preserve the palette instead of bleaching saturated hair.
    if not scene.get('cs_neutral_lighting'):
        for obj in scene.objects:
            if obj.type == 'LIGHT' and obj.name in ('Key', 'Fill', 'Rim'):
                obj.data.energy *= .55
        scene['cs_neutral_lighting'] = True
    clips = json.loads(scene.get('cs_clips_json', '{}'))
    for stage in stages:
        if stage == 'animation':
            clips = builder.animate()
        else:
            builder.remove_stage(stage)
            getattr(builder, stage)()
            builder.consolidate(stage)
            if stage == 'body' and not builder.rig:
                builder.create_rig()
            builder.bind()
        builder.checkpoint(stage, clips)


if __name__ == '__main__':
    main()
