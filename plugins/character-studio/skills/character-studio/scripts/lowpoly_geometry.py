"""Local profile geometry. Ring stitching adapted from MIT blender-LPM-skill.

Upstream: ozanzeng/blender-LPM-skill, revision
687d0a46f1280bc7d11dbf83539840100ec909dc, scripts/lpm.py (lathe).
Copyright (c) 2026 Ozan Zengin. See ../../../THIRD_PARTY_NOTICES.md.
No scene reset, file access, download, subprocess, or dynamic execution here.
"""
import math

import bmesh
import bpy
from mathutils import Vector


def mesh_object(name, vertices, faces, collection, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def loft(name, rings, collection, material, segments=10, axis=(0, 0, 1), flat_front=False):
    """Rings: (centre XYZ, radius on first basis, radius on second basis)."""
    direction = Vector(axis).normalized()
    first = Vector((1, 0, 0)) if abs(direction.z) > .9 else Vector((0, 1, 0))
    first = (first - direction * first.dot(direction)).normalized()
    second = direction.cross(first).normalized()
    vertices = []
    for centre, a, b in rings:
        for index in range(segments):
            angle = math.tau * index / segments
            u, v = math.cos(angle), math.sin(angle)
            if flat_front and v < -.20:
                v = -1
            vertices.append(tuple(Vector(centre) + first * (a * u) + second * (b * v)))
    faces = []
    for row in range(len(rings) - 1):
        for index in range(segments):
            a, b = row * segments + index, row * segments + (index + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.extend([tuple(reversed(range(segments))), tuple((len(rings) - 1) * segments + i for i in range(segments))])
    return mesh_object(name, vertices, faces, collection, material)


def garment_shell(name, profiles, collection, material, opening=.0, thickness=.004, segments=12):
    """Elliptical Z profiles (z, half width, half depth); fitted open garment."""
    angles = [-math.pi / 2 + opening + (math.tau - opening * 2) * i / segments for i in range(segments + 1)]
    vertices = []
    for inset in (0, thickness):
        for z, x, y in profiles:
            for angle in angles:
                vertices.append(((x - inset) * math.cos(angle), (y - inset) * math.sin(angle), z))
    width, rows = len(angles), len(profiles)
    layer = width * rows
    faces = []
    for row in range(rows - 1):
        for index in range(width - 1):
            a = row * width + index
            faces.append((a, a + 1, a + width + 1, a + width))
            faces.append((layer + a + width, layer + a + width + 1, layer + a + 1, layer + a))
    for row in (0, rows - 1):
        for index in range(width - 1):
            a = row * width + index
            faces.append((a, layer + a, layer + a + 1, a + 1))
    for index in (0, width - 1):
        for row in range(rows - 1):
            a = row * width + index
            faces.append((a, a + width, layer + a + width, layer + a))
    return mesh_object(name, vertices, faces, collection, material)


def ellipsoid(name, centre, radii, collection, material, segments=10, rows=5):
    rings = []
    for row in range(rows + 1):
        angle = math.pi * row / rows
        radius = max(.015, math.sin(angle))
        rings.append(((centre[0], centre[1], centre[2] - radii[2] * math.cos(angle)), radii[0] * radius, radii[1] * radius))
    return loft(name, rings, collection, material, segments)


def rod(name, start, end, radius, collection, material, segments=6):
    delta = Vector(end) - Vector(start)
    return loft(name, [(start, radius, radius), (end, radius, radius)], collection, material, segments, delta)


def face_patch(name, centre, outline, collection, material):
    vertices = [(centre[0] + x, centre[1], centre[2] + z) for x, z in outline]
    return mesh_object(name, vertices, [tuple(range(len(vertices)))], collection, material)
