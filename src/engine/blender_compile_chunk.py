"""
MomentumStudio AI — Blender 5.2.1 LTS In-Engine World Compiler Script
Executed headlessly via `/Applications/Blender.app/Contents/MacOS/Blender -b --python blender_compile_chunk.py -- <args>`
Reads .world.json, procedurally generates 3D geometry with bmesh, audits corridor clearance
via mathutils.kdtree, applies PBR materials, and exports Draco-compressed glTF 2.0 chunk (.glb).
"""

import sys
import os
import json
import math

try:
    import bpy
    import bmesh
    import mathutils
    from mathutils import Vector, kdtree
except ImportError:
    bpy = None
    bmesh = None
    mathutils = None


def parse_args():
    argv = sys.argv
    if "--" not in argv:
        return None, None
    args = argv[argv.index("--") + 1 :]
    world_json_path = args[0] if len(args) > 0 else None
    output_glb_path = args[1] if len(args) > 1 else None
    return world_json_path, output_glb_path


def reset_blender_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)


def create_cyber_material(name: str, base_color: tuple, emission_color: tuple = (0, 0, 0, 1), emission_strength: float = 0.0, metallic: float = 0.8, roughness: float = 0.2):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def compile_world_chunk(world_data: dict, output_glb: str) -> dict:
    reset_blender_scene()
    scene = bpy.context.scene
    scene.name = world_data.get("project_name", "MomentumStudio_Chunk")

    root_col = bpy.data.collections.new("World_Root")
    scene.collection.children.link(root_col)

    # 0. Create Materials
    mat_track = create_cyber_material("Mat_TrackAsphalt", (0.05, 0.06, 0.08, 1.0), metallic=0.9, roughness=0.15)
    mat_neon_cyan = create_cyber_material("Mat_NeonCyan", (0.02, 0.7, 0.85, 1.0), emission_color=(0.02, 0.85, 1.0, 1.0), emission_strength=4.5)
    mat_neon_orange = create_cyber_material("Mat_NeonOrange", (0.95, 0.45, 0.05, 1.0), emission_color=(1.0, 0.5, 0.1, 1.0), emission_strength=4.0)
    mat_tower = create_cyber_material("Mat_MegatowerConcrete", (0.12, 0.14, 0.18, 1.0), metallic=0.4, roughness=0.6)

    # 1. Build Spline Track Geometry
    splines_data = world_data.get("splines", [])
    spline_samples = []
    min_clearance = 32.0

    track_mesh = bpy.data.meshes.new("Track_Surface_Mesh")
    bm_track = bmesh.new()

    for s_info in splines_data:
        min_clearance = s_info.get("corridor_clearance_radius_m", 32.0)
        pts = s_info.get("points", [])
        
        # Build ribbon geometry along spline points
        road_half_width = 7.0
        prev_left = None
        prev_right = None

        for i, pt in enumerate(pts):
            co = pt["co"]
            pos = Vector(co)
            spline_samples.append(pos)

            # Lateral tangent normal for road width
            v_left = bm_track.verts.new(pos + Vector((-road_half_width, 0.0, 0.0)))
            v_right = bm_track.verts.new(pos + Vector((road_half_width, 0.0, 0.0)))

            if prev_left and prev_right:
                bm_track.faces.new([prev_left, prev_right, v_right, v_left])

            prev_left = v_left
            prev_right = v_right

    bm_track.to_mesh(track_mesh)
    bm_track.free()

    track_obj = bpy.data.objects.new("Track_Surface", track_mesh)
    track_obj.data.materials.append(mat_track)
    root_col.objects.link(track_obj)

    # 2. Build Procedural Megatowers
    towers_col = bpy.data.collections.new("Procedural_Megatowers")
    root_col.children.link(towers_col)
    spawned_objects = 0

    zones = world_data.get("procedural_zones", [])
    for zone in zones:
        params = zone.get("parameters", {})
        lateral_offset = params.get("lateral_clearance_m", 38.5)
        tower_count = params.get("tower_count_per_side", 8)
        inject_obstruction = params.get("inject_obstruction_test", False)

        for side in (-1, 1):
            for t_idx in range(tower_count):
                z_pos = t_idx * 80.0
                x_pos = side * (lateral_offset + (t_idx % 3) * 12.0)

                # If test obstruction requested, intentionally violate clearance
                if inject_obstruction and t_idx == 2 and side == 1:
                    x_pos = 12.0  # Violates 32.0m corridor clearance!

                # Create concrete 3D tower geometry with bmesh
                bmesh_tower = bmesh.new()
                bmesh.ops.create_cube(bmesh_tower, size=1.0)
                
                # Scale cube into skyscraper proportions
                scale_vec = Vector((24.0, 110.0, 32.0))
                bmesh.ops.scale(bmesh_tower, vec=scale_vec, verts=bmesh_tower.verts)

                mesh_data = bpy.data.meshes.new(f"TowerMesh_{'L' if side < 0 else 'R'}_{t_idx}")
                bmesh_tower.to_mesh(mesh_data)
                bmesh_tower.free()

                tower_obj = bpy.data.objects.new(f"Tower_{'L' if side < 0 else 'R'}_{t_idx}", mesh_data)
                tower_obj.location = (x_pos, 45.0, z_pos)
                
                # Assign materials
                tower_obj.data.materials.append(mat_tower)
                if t_idx % 2 == 0:
                    tower_obj.data.materials.append(mat_neon_cyan if side < 0 else mat_neon_orange)

                towers_col.objects.link(tower_obj)
                spawned_objects += 1

    # 3. 3D KDTree Spatial Corridor Clearance Audit
    tree = kdtree.KDTree(len(spline_samples))
    for idx, pt in enumerate(spline_samples):
        tree.insert(pt, idx)
    tree.balance()

    violations = []
    pruned_count = 0
    for obj in list(towers_col.objects):
        co, idx, dist = tree.find(obj.location)
        if dist < min_clearance:
            violations.append({"name": obj.name, "distance_m": round(dist, 2), "min_clearance_m": min_clearance})
            bpy.data.objects.remove(obj, do_unlink=True)
            pruned_count += 1

    # 4. Export to Draco-compressed glTF 2.0
    os.makedirs(os.path.dirname(os.path.abspath(output_glb)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb,
        export_format="GLB",
        export_draco_mesh_compression_enable=True,
    )

    file_size = os.path.getsize(output_glb) if os.path.exists(output_glb) else 0

    return {
        "status": "PASSED" if len(violations) == 0 or pruned_count == len(violations) else "FAILED",
        "objects_spawned": spawned_objects + 1,  # +1 for track
        "objects_retained": (spawned_objects - pruned_count) + 1,
        "violations_detected": len(violations),
        "auto_pruned_count": pruned_count,
        "corridor_clearance_percent": 100.0 if pruned_count == len(violations) else round(((spawned_objects - len(violations)) / spawned_objects) * 100.0, 2),
        "glb_output_bytes": file_size,
        "output_path": output_glb,
        "violations": violations,
    }


def main():
    world_json_path, output_glb_path = parse_args()
    if not world_json_path or not output_glb_path:
        print(json.dumps({"error": "Missing world_json_path or output_glb_path"}))
        sys.exit(1)

    with open(world_json_path, "r", encoding="utf-8") as f:
        world_data = json.load(f)

    result = compile_world_chunk(world_data, output_glb_path)
    print("\n__MOMENTUM_STUDIO_RESULT_START__")
    print(json.dumps(result))
    print("__MOMENTUM_STUDIO_RESULT_END__\n")


if __name__ == "__main__":
    main()
