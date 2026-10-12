"""Local connected T-pose mannequin; geometry and joint-study poses only.

Run in a dedicated Blender process with --factory-startup --disable-autoexec.
No downloaded assets, network, external services or dynamic code execution.
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys

import bmesh
import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'character-studio/scripts'))
from build_stylized_humanoid import Builder, DEFAULT
from build_robot import material, staging
from lowpoly_geometry import mesh_object
from types import SimpleNamespace

BUILDS = {'balanced': (1, 1, 1, 1), 'compact': (1.06, 1.10, 1.10, .87),
          'sturdy': (1.22, 1.02, 1.20, 1)}  # torso/head/limb width, leg length
POSES = ('Shoulders', 'Elbows', 'Knees', 'HipSpread', 'Twist')
LIMITS = ['Style study base, not finished character art or automatic anatomy reconstruction.',
          'Simple palms and feet; no individual fingers, facial features or facial rig.',
          'Joint-study actions are validation poses, not gameplay or locomotion clips.',
          'The older dressed humanoid helper is not compatible with this new geometry.',
          'Clothing, face, hair and motion must be fitted and reviewed after body edits.']


def options():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--name', default='StudioBase')
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--build', choices=tuple(BUILDS))
    parser.add_argument('--render-size', type=int, default=512)
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--no-rig', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}', args.name):
        parser.error('name must start with a letter, with at most 48 letters/digits/_/-')
    if not 128 <= args.render_size <= 1024:
        parser.error('render-size must be 128..1024')
    raw = {}
    if args.spec:
        if args.spec.stat().st_size > 32768:
            parser.error('spec exceeds 32 KiB')
        raw = json.loads(args.spec.read_text(encoding='utf-8-sig'))
    if not isinstance(raw, dict) or set(raw) - {'height', 'build', 'colour'}:
        parser.error('supported JSON keys: height, build, colour')
    spec = {'height': 1.6, 'build': 'balanced', 'colour': '#8DAEBB', **raw}
    if args.build:
        spec['build'] = args.build
    if isinstance(spec['height'], bool) or not isinstance(spec['height'], (int, float)) or not math.isfinite(spec['height']) or not .6 <= spec['height'] <= 2.5:
        parser.error('height must be finite and .6..2.5')
    if not isinstance(spec['build'], str) or spec['build'] not in BUILDS:
        parser.error('unsupported build')
    if not isinstance(spec['colour'], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', spec['colour']):
        parser.error('colour must be #RRGGBB')
    args.output = args.output.resolve()
    planned = [args.output / (args.name + suffix) for suffix in ('.blend', '.glb', '-report.json')]
    if not args.no_render:
        planned += [args.output / (args.name + '-' + view + '.png') for view in ('front', 'side', 'back', 'three-quarter')]
        if not args.no_rig:
            planned += [args.output / (args.name + '-' + pose + '-' + view + '.png') for pose in POSES for view in ('front', 'side', 'three-quarter')]
    if not args.overwrite and any(path.exists() for path in planned):
        parser.error('output exists; choose a new directory or explicitly use --overwrite')
    if bpy.data.filepath or '--factory-startup' not in sys.argv:
        parser.error('requires a fresh dedicated --factory-startup process')
    return args, spec


class Mannequin(Builder):
    def __init__(self, args, spec):
        self.form = spec
        self.torso, self.head_width, self.limb, self.leg = BUILDS[spec['build']]
        # Normalise height after proportion edits, rather than stretching only the mesh.
        self.shift = .48 * (self.leg - 1)
        self.norm = spec['height'] / (1.60 + self.shift)
        compatible = {**DEFAULT, 'palette': {**DEFAULT['palette'], 'skin': spec['colour']}, 'height': spec['height']}
        super().__init__(args, compatible)
        self.scale = self.norm
        self.vertices, self.faces, self.regions = [], [], []

    def level(self, z):
        return .20 + (z - .20) * self.leg if z <= .68 else z + self.shift

    def joints(self):
        h = self.level
        # Builder.create_rig applies self.scale after __init__.
        points = {'Root': ((0, 0, 0), (0, 0, .12), None),
                  'Pelvis': ((0, 0, h(.68)), (0, 0, h(.84)), 'Root'),
                  'Spine': ((0, 0, h(.84)), (0, 0, h(1.115)), 'Pelvis'),
                  'Head': ((0, 0, h(1.115)), (0, 0, h(1.53)), 'Spine')}
        for sign, side in ((1, 'L'), (-1, 'R')):
            start = .205 * self.torso
            elbow, wrist = start + .245, start + .445
            x = .112 * self.torso
            points.update({
                'UpperArm.' + side: ((sign * start, 0, h(1.055)), (sign * elbow, 0, h(1.055)), 'Spine'),
                'LowerArm.' + side: ((sign * elbow, 0, h(1.055)), (sign * wrist, 0, h(1.055)), 'UpperArm.' + side),
                'Hand.' + side: ((sign * wrist, 0, h(1.055)), (sign * (wrist + .14), 0, h(1.055)), 'LowerArm.' + side),
                'UpperLeg.' + side: ((sign * x, 0, h(.68)), (sign * x, 0, h(.36)), 'Pelvis'),
                'LowerLeg.' + side: ((sign * x, 0, h(.36)), (sign * x, 0, .105), 'UpperLeg.' + side),
                'Foot.' + side: ((sign * x, 0, .105), (sign * x, -.16, .055), 'LowerLeg.' + side),
            })
        return points

    def vertex(self, point, region):
        self.vertices.append(point)
        self.regions.append(region)
        return len(self.vertices) - 1

    def ring(self, coords, region):
        return [self.vertex(point, region) for point in coords]

    def connect(self, a, b):
        assert len(a) == len(b)
        for i in range(len(a)):
            j = (i + 1) % len(a)
            self.faces.append((a[i], a[j], b[j], b[i]))

    def build_mesh(self):
        # Ten-sided bevelled rectangle: centre points make an explicit crotch fork.
        outline = [(0, -1), (.65, -1), (1, -.65), (1, .65), (.65, 1),
                   (0, 1), (-.65, 1), (-1, .65), (-1, -.65), (-.65, -1)]
        profiles = [(.68, .195 * self.torso, .118), (.75, .200 * self.torso, .132),
                    (.84, .160 * self.torso, .110), (.94, .185 * self.torso, .130),
                    (.985, .207 * self.torso, .125), (1.125, .207 * self.torso, .115),
                    (1.155, .070, .065), (1.185, .073, .072),
                    (1.205, .132 * self.head_width, .127 * self.head_width),
                    (1.26, .207 * self.head_width, .157 * self.head_width),
                    (1.48, .224 * self.head_width, .169 * self.head_width),
                    (1.565, .205 * self.head_width, .154 * self.head_width),
                    (1.60, .158 * self.head_width, .121 * self.head_width)]
        rings = [self.ring([(x * width, y * depth, self.level(z)) for x, y in outline], 'torso') for z, width, depth in profiles]
        for row in range(len(rings) - 1):
            for i in range(10):
                if row == 4 and i in (2, 7):  # shoulder ports, no capped overlap
                    continue
                j = (i + 1) % 10
                self.faces.append((rings[row][i], rings[row][j], rings[row + 1][j], rings[row + 1][i]))
        self.faces.append(tuple(rings[-1]))
        arm_outline = [(-.65, -1), (.65, -1), (1, -.65), (1, .65),
                       (.65, 1), (-.65, 1), (-1, .65), (-1, -.65)]
        for sign, side in ((1, 'L'), (-1, 'R')):
            start = .205 * self.torso
            i = 2 if sign == 1 else 7
            port = [rings[4][i], rings[4][i + 1], rings[5][i + 1], rings[5][i]]
            if sign == -1:
                port = [rings[4][i + 1], rings[4][i], rings[5][i], rings[5][i + 1]]
            arm = []
            # Extra rings around elbow and wrist give both flexion and volume control.
            for offset, depth, radius in [(.035, .073, .082), (.12, .064, .080),
                                           (.205, .055, .065), (.245, .053, .061),
                                           (.285, .056, .066), (.355, .058, .069),
                                           (.445, .037, .043), (.485, .045, .063),
                                           (.555, .043, .061), (.585, .025, .036)]:
                arm.append(self.ring([(sign * (start + offset), y * depth * self.limb,
                                       self.level(1.055) + z * radius * self.limb) for y, z in arm_outline], 'arm:' + side))
            # Connect rectangular shoulder opening to an octagonal limb with real edges.
            for k in range(4):
                self.faces.append((port[k], arm[0][(2 * k - 1) % 8], arm[0][2 * k]))
                self.faces.append((port[k], port[(k + 1) % 4], arm[0][2 * k + 1], arm[0][2 * k]))
            for a, b in zip(arm, arm[1:]):
                self.connect(a, b)
            self.faces.append(tuple(arm[-1]))
            # Each leg shares one crotch edge and its entire top boundary with the pelvis.
            loop = [rings[0][k] for k in ([0, 1, 2, 3, 4, 5] if sign == 1 else [5, 6, 7, 8, 9, 0])]
            leg_outline = [(-.72, -1), (.45, -1), (1, -.4), (1, .55), (.15, 1), (-.86, .70)]
            if sign == -1:
                leg_outline = [(-x, y) for x, y in reversed(leg_outline)]
            last = loop
            # Legs and feet are one surface, with foot influence blended at the ankle.
            for z, radius, depth, forward in [(.60, .098, .109, 0), (.50, .086, .098, 0),
                                             (.395, .074, .084, 0), (.36, .070, .080, 0),
                                             (.325, .074, .084, 0), (.25, .079, .089, 0),
                                             (.16, .052, .061, 0), (.115, .048, .057, 0),
                                             (.085, .070, .122, -.038), (.040, .077, .153, -.065),
                                             (.016, .075, .150, -.065), (.006, .064, .134, -.065)]:
                actual_z = self.level(z) if z > .20 else z
                radius *= self.limb
                depth *= min(1.10, self.limb)
                current = self.ring([(sign * .112 * self.torso + x * radius, forward + y * depth, actual_z) for x, y in leg_outline], 'leg:' + side)
                self.connect(last, current)
                last = current
            self.faces.append(tuple(reversed(last)))
        obj = mesh_object(self.owner + '_Body', [tuple(Vector(v) * self.norm) for v in self.vertices], self.faces, self.collection('body'), self.materials['skin'])
        obj['cs_owner'], obj['cs_stage'], obj['cs_generated'] = self.owner, 'base-body', True
        obj['cs_base_build'] = self.form['build']
        self.assign_weights(obj)
        return obj

    def assign_weights(self, obj):
        clamp = lambda value: max(0, min(1, value))
        for index, ((x, y, z), region) in enumerate(zip(self.vertices, self.regions)):
            if region == 'torso':
                spine = clamp((z - self.level(.80)) / .19)
                head = clamp((z - self.level(1.125)) / .07)
                weights = {'Pelvis': (1 - spine) * (1 - head), 'Spine': spine * (1 - head), 'Head': head}
                if self.level(.985) - .001 <= z <= self.level(1.125) + .001 and abs(x) > .19 * self.torso:
                    side = 'L' if x > 0 else 'R'
                    weights = {'Spine': .72, 'UpperArm.' + side: .28}
            elif region.startswith('arm:'):
                side = region.split(':')[1]
                offset = abs(x) - .205 * self.torso
                shoulder = clamp((offset - .015) / .07)
                elbow = clamp((offset - .205) / .08)
                hand = clamp((offset - .415) / .065)
                weights = {'Spine': 1 - shoulder,
                           'UpperArm.' + side: shoulder * (1 - elbow),
                           'LowerArm.' + side: shoulder * elbow * (1 - hand),
                           'Hand.' + side: shoulder * elbow * hand}
            else:
                side = region.split(':')[1]
                pelvis = clamp((z - self.level(.54)) / (self.level(.68) - self.level(.54)))
                knee = clamp((self.level(.44) - z) / (self.level(.44) - self.level(.28)))
                foot = clamp((.15 - z) / .07)
                weights = {'Pelvis': pelvis, 'UpperLeg.' + side: (1 - pelvis) * (1 - knee),
                           'LowerLeg.' + side: (1 - pelvis) * knee * (1 - foot),
                           'Foot.' + side: (1 - pelvis) * knee * foot}
            for name, weight in weights.items():
                if weight > 0:
                    group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
                    group.add([index], weight, 'REPLACE')

    def desired_pose(self, name):
        identity = Quaternion()
        q = lambda axis, angle: Quaternion(axis, math.radians(angle))
        desired = {bone.name: identity.copy() for bone in self.rig.pose.bones}
        if name == 'Twist':
            for bone in ('Spine', 'Head', 'UpperArm.L', 'LowerArm.L', 'Hand.L', 'UpperArm.R', 'LowerArm.R', 'Hand.R'):
                desired[bone] = q((0, 0, 1), 40)
        for sign, side in ((1, 'L'), (-1, 'R')):
            if name == 'Shoulders':
                for part in ('UpperArm.', 'LowerArm.', 'Hand.'):
                    desired[part + side] = q((0, 1, 0), -sign * 45)
            elif name == 'Elbows':
                for part in ('LowerArm.', 'Hand.'):
                    desired[part + side] = q((0, 0, 1), -sign * 90)
            elif name == 'Knees':
                desired['UpperLeg.' + side] = q((1, 0, 0), -30)
                desired['LowerLeg.' + side] = q((1, 0, 0), 55)
                desired['Foot.' + side] = q((1, 0, 0), 15)
            elif name == 'HipSpread':
                for part in ('UpperLeg.', 'LowerLeg.', 'Foot.'):
                    desired[part + side] = q((0, 1, 0), -sign * 25)
        return desired

    def apply_pose(self, name):
        desired = self.desired_pose(name)
        identity = Quaternion()
        for bone in self.rig.pose.bones:
            rest = bone.bone.matrix_local.to_quaternion()
            parent = desired[bone.parent.name] if bone.parent else identity
            bone.rotation_quaternion = rest.inverted() @ parent.inverted() @ desired[bone.name] @ rest
            bone.location = (0, 0, 0)
        bpy.context.view_layer.update()

    def joint_actions(self):
        self.rig.animation_data_create()
        for name in POSES:
            self.apply_pose(name)
            action = bpy.data.actions.new('Check' + name)
            self.rig.animation_data.action = action
            for frame in (1, 2):
                for bone in self.rig.pose.bones:
                    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=bone.name)
            slot = self.rig.animation_data.action_slot
            self.rig.animation_data.action = None
            track = self.rig.animation_data.nla_tracks.new()
            track.name = action.name
            strip = track.strips.new(action.name, 1, action)
            strip.action_slot = slot
            track.mute = True
        self.rest_pose()


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    components = 0
    for vertex in bm.verts:
        if vertex.index in seen:
            continue
        components += 1
        todo = [vertex]
        while todo:
            current = todo.pop()
            if current.index in seen:
                continue
            seen.add(current.index)
            todo += [edge.other_vert(current) for edge in current.link_edges]
    result = {'vertices': len(bm.verts), 'edges': len(bm.edges), 'faces': len(bm.faces),
              'connected_components': components, 'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
              'zero_area_faces': sum(face.calc_area() < 1e-10 for face in bm.faces),
              'euler_characteristic': len(bm.verts) - len(bm.edges) + len(bm.faces)}
    bm.free()
    return result


def main():
    args, spec = options()
    # Dedicated fresh process only. Existing models are never opened or replaced.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.preferences.filepaths.save_version = 0
    args.output.mkdir(parents=True, exist_ok=True)
    builder = Mannequin(args, spec)
    obj = builder.build_mesh()
    if not args.no_rig:
        builder.create_rig()
        builder.bind()
        builder.joint_actions()
    structural = topology(obj)
    assert structural['connected_components'] == 1 and structural['nonmanifold_edges'] == 0 and structural['zero_area_faces'] == 0, structural
    if builder.rig:
        assert all(abs(sum(g.weight for g in v.groups) - 1) < 1e-5 and len(v.groups) <= 4 for v in obj.data.vertices)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 2
    scene['cs_base_spec_json'] = json.dumps(spec)
    scene['cs_owner'] = args.name
    staging(SimpleNamespace(height=spec['height'], render_size=args.render_size, preview_span=spec['height'] * 1.14))
    scene.view_settings.view_transform = 'Standard'
    scene.cycles.samples = 12
    for light in scene.objects:
        if light.type == 'LIGHT':
            light.data.energy *= .48
    stem = args.output / args.name
    # T-pose is saved and exported as the default; joint actions are muted in source.
    bpy.ops.wm.save_as_mainfile(filepath=str(stem) + '.blend')
    builder.export(Path(str(stem) + '.glb'))
    previews = {}
    target = Vector((0, 0, spec['height'] * .49))
    views = {'front': (0, -6, 0), 'side': (6, 0, 0), 'back': (0, 6, 0), 'three-quarter': (4, -6, 1.2)}
    if not args.no_render:
        for pose in ('Tpose', *POSES) if builder.rig else ('Tpose',):
            if pose == 'Tpose':
                builder.rest_pose()
            else:
                builder.apply_pose(pose)
            for view, direction in views.items():
                if pose != 'Tpose' and view == 'back':
                    continue
                scene.camera.location = target + Vector(direction) * spec['height']
                scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
                suffix = '-' + view if pose == 'Tpose' else '-' + pose + '-' + view
                scene.render.filepath = str(stem) + suffix + '.png'
                bpy.ops.render.render(write_still=True)
                previews[pose + '/' + view] = scene.render.filepath
    builder.rest_pose()
    scene.camera.location = target + Vector(views['three-quarter']) * spec['height']
    scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stem) + '-three-quarter.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(stem) + '.blend')
    obj.data.calc_loop_triangles()
    report = {'name': args.name, 'spec': spec, 'blender_version': bpy.app.version_string,
              'topology': structural, 'triangles': len(obj.data.loop_triangles), 'bones': len(builder.rig.data.bones) if builder.rig else 0,
              'joint_check_actions': ['Check' + p for p in POSES] if builder.rig else [],
              'actual_height': max(v.co.z for v in obj.data.vertices) - min(v.co.z for v in obj.data.vertices),
              'weights_normalised': True, 'body_meshes': 1,
              'outputs': {'blend': str(stem) + '.blend', 'glb': str(stem) + '.glb'},
              'previews': previews, 'limitations': LIMITS}
    Path(str(stem) + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CHARACTER_BASE_RESULT ' + json.dumps(report))


if __name__ == '__main__':
    main()
