"""
MomentumStudio AI — Blender 5.2.1 LTS In-Engine World Compiler Script
Executed headlessly via `/Applications/Blender.app/Contents/MacOS/Blender -b --python blender_compile_chunk.py -- <args>`
Reads .world.json, compiles procedural shader node graphs (Noise, Voronoi, ColorRamp, Bump),
builds bmesh geometry, audits corridor clearance via mathutils.kdtree, and exports Draco glTF 2.0 chunk.
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


def build_procedural_shader_recipe(recipe: dict) -> bpy.types.Material:
    """
    Builds a real procedural node graph inside Blender for a given shader recipe.
    Supports procedural water puddles (Noise + ColorRamp), asphalt cracks (Voronoi + Bump),
    metal rust oxidization, and pulsating neon emission.
    """
    mat_id = recipe.get("id", "ProceduralMat")
    mat = bpy.data.materials.new(name=mat_id)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return mat

    # Extract base properties
    bc = recipe.get("base_color", {})
    base_color = (bc.get("r", 0.1), bc.get("g", 0.1), bc.get("b", 0.12), bc.get("a", 1.0))
    metallic = recipe.get("metallic", 0.1)
    roughness = recipe.get("roughness", 0.6)
    
    ec = recipe.get("emission_color", {})
    emission_color = (ec.get("r", 0.0), ec.get("g", 0.0), ec.get("b", 0.0), ec.get("a", 1.0))
    emission_strength = recipe.get("emission_strength", 0.0)

    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    recipe_type = recipe.get("recipe_type", "GENERIC")
    weathering = recipe.get("weathering", {})
    wetness = weathering.get("wetness", 0.0)

    # Recipe 1: Rain-Soaked Asphalt with Procedural Noise Puddles & Voronoi Cracks
    if "RAIN" in recipe_type or wetness > 0.3:
        # Texture Coordinate & Mapping
        tex_coord = nodes.new(type="ShaderNodeTexCoord")
        tex_coord.location = (-800, 200)

        # Procedural Noise for Water Puddles
        noise_node = nodes.new(type="ShaderNodeTexNoise")
        noise_node.location = (-550, 300)
        noise_params = recipe.get("noise", {})
        noise_node.inputs["Scale"].default_value = noise_params.get("scale", 5.0)
        noise_node.inputs["Detail"].default_value = noise_params.get("detail", 6.0)
        noise_node.inputs["Roughness"].default_value = noise_params.get("roughness", 0.6)
        links.new(tex_coord.outputs["Object"], noise_node.inputs["Vector"])

        # ColorRamp to map noise into sharp puddle reflection (0.02 mirror) vs damp road (0.75)
        puddle_ramp = nodes.new(type="ShaderNodeValToRGB")
        puddle_ramp.location = (-280, 300)
        puddle_ramp.color_ramp.elements[0].position = max(0.05, 0.5 - (wetness * 0.35))
        puddle_ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1.0)  # Wet reflection
        puddle_ramp.color_ramp.elements[1].position = min(0.95, 0.5 + (wetness * 0.25))
        puddle_ramp.color_ramp.elements[1].color = (0.72, 0.72, 0.72, 1.0)  # Dry asphalt
        links.new(noise_node.outputs["Fac"], puddle_ramp.inputs["Fac"])
        links.new(puddle_ramp.outputs["Color"], bsdf.inputs["Roughness"])

        # Procedural Voronoi for Surface Cracks
        if weathering.get("crack_density", 0.0) > 0.1:
            voronoi = nodes.new(type="ShaderNodeTexVoronoi")
            voronoi.location = (-550, -100)
            voronoi.inputs["Scale"].default_value = 24.0
            links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

            bump = nodes.new(type="ShaderNodeBump")
            bump.location = (-280, -100)
            bump.inputs["Strength"].default_value = 0.35
            bump.inputs["Distance"].default_value = 0.05
            links.new(voronoi.outputs["Distance"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Recipe 2: Eroded Rusted Metal with Musgrave Noise Rust Streaks
    elif "RUST" in recipe_type or weathering.get("rust_intensity", 0.0) > 0.2:
        tex_coord = nodes.new(type="ShaderNodeTexCoord")
        tex_coord.location = (-700, 200)

        noise_rust = nodes.new(type="ShaderNodeTexNoise")
        noise_rust.location = (-450, 200)
        noise_rust.inputs["Scale"].default_value = 8.5
        noise_rust.inputs["Detail"].default_value = 8.0
        links.new(tex_coord.outputs["Object"], noise_rust.inputs["Vector"])

        rust_ramp = nodes.new(type="ShaderNodeValToRGB")
        rust_ramp.location = (-200, 200)
        rust_ramp.color_ramp.elements[0].color = base_color  # Steel
        rust_ramp.color_ramp.elements[1].color = (0.42, 0.14, 0.04, 1.0)  # Oxidized Rust
        links.new(noise_rust.outputs["Fac"], rust_ramp.inputs["Fac"])
        links.new(rust_ramp.outputs["Color"], bsdf.inputs["Base Color"])

    return mat


def compile_world_chunk(world_data: dict, output_glb: str) -> dict:
    reset_blender_scene()
    scene = bpy.context.scene
    scene.name = world_data.get("project_name", "MomentumStudio_Chunk")

    root_col = bpy.data.collections.new("World_Root")
    scene.collection.children.link(root_col)

    # 0. Compile Procedural Shader Recipes
    compiled_materials = {}
    recipes_list = world_data.get("materials", [])
    
    # If no explicit recipes provided, load standard defaults
    if not recipes_list:
        recipes_list = [
            {"id": "RainSoakedCyberHighway", "recipe_type": "RAIN_SOAKED_ASPHALT", "weathering": {"wetness": 0.85, "crack_density": 0.3}, "metallic": 0.15, "roughness": 0.65},
            {"id": "BrutalistConcrete", "recipe_type": "WEATHERED_CONCRETE", "base_color": {"r": 0.18, "g": 0.20, "b": 0.24, "a": 1.0}, "roughness": 0.85},
            {"id": "NeonCyberCyan", "recipe_type": "NEON_CYBER_EMISSIVE", "base_color": {"r": 0.02, "g": 0.85, "b": 1.0, "a": 1.0}, "emission_color": {"r": 0.02, "g": 0.95, "b": 1.0, "a": 1.0}, "emission_strength": 5.5},
            {"id": "NeonCyberOrange", "recipe_type": "NEON_CYBER_EMISSIVE", "base_color": {"r": 1.0, "g": 0.45, "b": 0.05, "a": 1.0}, "emission_color": {"r": 1.0, "g": 0.5, "b": 0.08, "a": 1.0}, "emission_strength": 4.8},
        ]

    for r in recipes_list:
        mat_obj = build_procedural_shader_recipe(r)
        compiled_materials[r.get("id")] = mat_obj

    mat_track = compiled_materials.get("RainSoakedCyberHighway", list(compiled_materials.values())[0])
    mat_concrete = compiled_materials.get("BrutalistConcrete", list(compiled_materials.values())[0])
    mat_neon_cyan = compiled_materials.get("NeonCyberCyan", list(compiled_materials.values())[0])
    mat_neon_orange = compiled_materials.get("NeonCyberOrange", list(compiled_materials.values())[0])

    # 1. Build Spline Track Geometry with Procedural Road Surface
    splines_data = world_data.get("splines", [])
    spline_samples = []
    min_clearance = 32.0

    track_mesh = bpy.data.meshes.new("Track_Surface_Mesh")
    bm_track = bmesh.new()

    for s_info in splines_data:
        min_clearance = s_info.get("corridor_clearance_radius_m", 32.0)
        pts = s_info.get("points", [])
        road_half_width = 7.0
        prev_left = None
        prev_right = None

        for i, pt in enumerate(pts):
            co = pt["co"]
            pos = Vector(co)
            spline_samples.append(pos)

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

    # 2. Build Procedural Megatowers with Weathered Concrete & Neon Markers
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

                # Intentional obstruction test case
                if inject_obstruction and t_idx == 2 and side == 1:
                    x_pos = 12.0  # Violates 32.0m clearance!

                bmesh_tower = bmesh.new()
                bmesh.ops.create_cube(bmesh_tower, size=1.0)
                scale_vec = Vector((24.0, 110.0, 32.0))
                bmesh.ops.scale(bmesh_tower, vec=scale_vec, verts=bmesh_tower.verts)

                mesh_data = bpy.data.meshes.new(f"TowerMesh_{'L' if side < 0 else 'R'}_{t_idx}")
                bmesh_tower.to_mesh(mesh_data)
                bmesh_tower.free()

                tower_obj = bpy.data.objects.new(f"Tower_{'L' if side < 0 else 'R'}_{t_idx}", mesh_data)
                tower_obj.location = (x_pos, 45.0, z_pos)
                
                # Assign procedural materials
                tower_obj.data.materials.append(mat_concrete)
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
        "objects_spawned": spawned_objects + 1,
        "objects_retained": (spawned_objects - pruned_count) + 1,
        "violations_detected": len(violations),
        "auto_pruned_count": pruned_count,
        "corridor_clearance_percent": 100.0 if pruned_count == len(violations) else round(((spawned_objects - len(violations)) / spawned_objects) * 100.0, 2),
        "glb_output_bytes": file_size,
        "output_path": output_glb,
        "materials_compiled": len(compiled_materials),
        "recipe_types": [r.get("recipe_type") for r in recipes_list],
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
