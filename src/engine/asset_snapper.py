"""Catalog lookup, Y-up track sampling and cached Blender modular instancing.

AST/glTF use metres, Y up, +Z forward. Blender uses (x, -z, y).
The catalog counts file variants; a GLB/FBX/OBJ of one name is one asset.
"""
from __future__ import annotations

import bisect
import json
import math
from pathlib import Path


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, t):
    return tuple(x * t for x in a)


def length(a):
    return math.sqrt(sum(x * x for x in a))


def to_blender(p):
    return (p[0], -p[2], p[1])


def sample_spline(spline, step_m=4.0):
    """Tessellate POLY or cubic BEZIER; bound steps by control polygon length."""
    if step_m <= 0:
        raise ValueError("step_m must be positive")
    kind = spline.get("type", "BEZIER")
    if kind not in ("POLY", "BEZIER"):
        raise ValueError(f"Unsupported spline type: {kind}; use POLY or BEZIER")
    pts = spline["points"]
    pairs = list(zip(pts, pts[1:]))
    if spline.get("closed"):
        pairs.append((pts[-1], pts[0]))
    samples = []
    for a, b in pairs:
        p, q = tuple(a["co"]), tuple(b["co"])
        h1 = tuple(a.get("handle_right") or add(p, mul(sub(q, p), 1 / 3)))
        h2 = tuple(b.get("handle_left") or add(p, mul(sub(q, p), 2 / 3)))
        perimeter = sum(length(sub(v, u)) for u, v in zip((p, h1, h2), (h1, h2, q)))
        n = max(1, math.ceil(perimeter / step_m))
        for i in range(n):
            t = i / n
            if kind == "POLY":
                point = add(p, mul(sub(q, p), t))
            else:
                point = tuple((1-t)**3*p[j] + 3*(1-t)**2*t*h1[j] + 3*(1-t)*t*t*h2[j] + t**3*q[j] for j in range(3))
            if not samples or length(sub(point, samples[-1])) > 1e-7:
                samples.append(point)
    if pairs and (not samples or length(sub(pairs[-1][1]["co"], samples[-1])) > 1e-7):
        samples.append(tuple(pairs[-1][1]["co"]))
    if len(samples) < 2:
        raise ValueError("Track must contain at least two distinct points")
    return samples


class TrackPath:
    def __init__(self, spline):
        self.points = sample_spline(spline)
        self.distances = [0.0]
        for a, b in zip(self.points, self.points[1:]):
            self.distances.append(self.distances[-1] + length(sub(b, a)))
        self.length = self.distances[-1]

    def at(self, distance):
        d = max(0.0, min(distance, self.length))
        i = min(len(self.points)-2, max(0, bisect.bisect_right(self.distances, d)-1))
        direction = sub(self.points[i+1], self.points[i])
        tangent = mul(direction, 1 / length(direction))
        horizontal = math.hypot(tangent[0], tangent[2])
        if horizontal < 1e-7:
            raise ValueError("Vertical track segments cannot support a road vehicle")
        right = (tangent[2]/horizontal, 0.0, -tangent[0]/horizontal)
        return add(self.points[i], mul(tangent, d-self.distances[i])), tangent, right


def intersects_corridor(bounds, paths):
    """Conservative segment/expanded-AABB test, including full mesh bounds.

    The box expansion encloses the Euclidean clearance tube. This may prune
    extra objects near corners; it cannot certify objects inside that tube.
    Road surfaces are deliberately excluded from obstacle clearance checks.
    """
    lo, hi = bounds
    for path, radius in paths:
        for a, b in zip(path.points, path.points[1:]):
            enter, leave = 0.0, 1.0
            for axis in range(3):
                delta = b[axis]-a[axis]
                lower, upper = lo[axis]-radius, hi[axis]+radius
                if abs(delta) < 1e-10:
                    if not lower <= a[axis] <= upper:
                        enter = 2.0
                        break
                else:
                    t1, t2 = (lower-a[axis])/delta, (upper-a[axis])/delta
                    enter, leave = max(enter, min(t1, t2)), min(leave, max(t1, t2))
                if enter > leave:
                    break
            if enter <= leave:
                return True
    return False


class AssetCatalog:
    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        data = json.loads((self.root / "assets/asset_catalog.json").read_text())
        self.categories = data["categories"]

    def resolve(self, category, name):
        preference = {"GLB": 0, "GLTF": 1, "FBX": 2, "OBJ": 3}
        matches = sorted((a for a in self.categories.get(category, []) if a["name"] == name),
                         key=lambda a: (preference.get(a["format"].upper(), 99), a["relative_path"]))
        for item in matches:
            path = (self.root / item["relative_path"]).resolve()
            if not path.is_relative_to(self.root / "assets"):
                raise ValueError(f"Catalog path escapes asset directory: {name}")
            if path.is_file() and item["format"].upper() in preference:
                return path
        raise FileNotFoundError(f"No available asset {category}/{name}")


class AssetSnapper:
    """Import once; bake hierarchy transforms, then share meshes across instances."""
    def __init__(self, project_root, collection):
        self.catalog = AssetCatalog(project_root)
        self.collection = collection
        self.cache = {}
        self.instances = 0

    def _load(self, category, name):
        import bpy
        from mathutils import Matrix, Vector
        path = self.catalog.resolve(category, name)
        if path in self.cache:
            return self.cache[path]
        before = set(bpy.data.objects)
        try:
            if path.suffix.lower() in (".glb", ".gltf"):
                bpy.ops.import_scene.gltf(filepath=str(path))
            elif path.suffix.lower() == ".fbx":
                bpy.ops.import_scene.fbx(filepath=str(path))
            else:
                bpy.ops.wm.obj_import(filepath=str(path))
            bpy.context.view_layer.update()
            imported = set(bpy.data.objects)-before
            meshes = []
            points = []
            for obj in imported:
                if obj.type == "MESH":
                    mesh = obj.data.copy()
                    mesh.transform(obj.matrix_world)
                    meshes.append(mesh)
                    points.extend(v.co.copy() for v in mesh.vertices)
            if not points:
                raise ValueError(f"Asset has no mesh vertices: {path}")
            low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
            high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
            origin = Vector(((low.x+high.x)/2, (low.y+high.y)/2, low.z))
            for mesh in meshes:
                mesh.transform(Matrix.Translation(-origin))
            self.cache[path] = (meshes, high-low)
            return self.cache[path]
        finally:
            for obj in set(bpy.data.objects)-before:
                bpy.data.objects.remove(obj, do_unlink=True)

    def snap(self, category, name, position, tangent=(0, 0, 1), size_m=4.0):
        import bpy
        from mathutils import Matrix, Vector
        meshes, dimensions = self._load(category, name)
        # Uniform scale preserves the authored shape. size_m is largest dimension.
        scale = size_m / max(dimensions)
        yaw = math.atan2(tangent[0], tangent[2])
        matrix = Matrix.Translation(Vector(to_blender(position))) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(scale, 4)
        objects = []
        for index, mesh in enumerate(meshes):
            obj = bpy.data.objects.new(f"Module_{name}_{self.instances:04d}_{index}", mesh)
            obj.matrix_world = matrix
            self.collection.objects.link(obj)
            objects.append(obj)
        self.instances += 1
        return objects
