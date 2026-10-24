"""
Unit & Integration Tests for Procedural Zone Generators (TRANSIT_TUBES, NEON_BILLBOARDS)
"""

import json
import os
import subprocess
from pathlib import Path

import pytest
from compiler.spatial_ast import (
    GeneratorTypeEnum,
    LightingBudget,
    PhysicsContract,
    ProceduralZone,
    SplinePoint,
    SplineTrack,
    WorldChunk,
)

BLENDER_BIN = Path(os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender"))
COMPILER_SCRIPT = Path(__file__).resolve().parents[1] / "engine" / "blender_compile_chunk.py"


def test_zone_generator_ast_validation():
    chunk = WorldChunk(
        project_name="Generators_Test_World",
        sector_id="S02",
        splines=[
            SplineTrack(
                id="main_spline",
                points=[
                    SplinePoint(co=[0.0, 0.0, 0.0]),
                    SplinePoint(co=[0.0, 10.0, 200.0]),
                ],
                corridor_clearance_radius_m=32.0,
            )
        ],
        procedural_zones=[
            ProceduralZone(
                id="zone_tubes",
                anchor_spline="main_spline",
                generator=GeneratorTypeEnum.TRANSIT_TUBES,
                parameters={"tube_radius_m": 4.5},
            ),
            ProceduralZone(
                id="zone_billboards",
                anchor_spline="main_spline",
                generator=GeneratorTypeEnum.NEON_BILLBOARDS,
                parameters={"billboard_scale": 12.0},
            ),
        ],
        lighting_budget=LightingBudget(),
        physics_contracts=PhysicsContract(),
    )
    assert len(chunk.procedural_zones) == 2
    assert chunk.procedural_zones[0].generator == GeneratorTypeEnum.TRANSIT_TUBES
    assert chunk.procedural_zones[1].generator == GeneratorTypeEnum.NEON_BILLBOARDS


def test_zone_generators_blender_compilation(tmp_path):
    if not BLENDER_BIN.exists():
        pytest.skip("Blender binary not available")

    scene_data = {
        "$schema_version": "1.0.0",
        "project_name": "Generator_Compilation_Test",
        "sector_id": "S03",
        "units": "meters",
        "splines": [
            {
                "id": "spline_test",
                "type": "BEZIER",
                "closed": False,
                "corridor_clearance_radius_m": 32.0,
                "enforce_kdtree_audit": True,
                "points": [
                    {"co": [0.0, 0.0, 0.0]},
                    {"co": [0.0, 10.0, 300.0]},
                ],
            }
        ],
        "procedural_zones": [
            {
                "id": "tubes_01",
                "anchor_spline": "spline_test",
                "generator": "TRANSIT_TUBES",
                "material_recipe_id": "NeonCyberCyan",
                "parameters": {"tube_radius_m": 4.0},
            },
            {
                "id": "billboards_01",
                "anchor_spline": "spline_test",
                "generator": "NEON_BILLBOARDS",
                "material_recipe_id": "NeonCyberOrange",
            },
        ],
    }

    scene_json = tmp_path / "gen_test.world.json"
    out_glb = tmp_path / "gen_test.glb"
    scene_json.write_text(json.dumps(scene_data, indent=2))

    cmd = [
        str(BLENDER_BIN),
        "-b",
        "--python-exit-code", "1",
        "--python", str(COMPILER_SCRIPT),
        "--", str(scene_json), str(out_glb),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0
    assert out_glb.exists()
    assert out_glb.stat().st_size > 1000
    assert "__MOMENTUM_STUDIO_RESULT_START__" in proc.stdout
    token = proc.stdout.split("__MOMENTUM_STUDIO_RESULT_START__")[1].split("__MOMENTUM_STUDIO_RESULT_END__")[0]
    result = json.loads(token)
    assert result["status"] == "PASSED"
    assert result["objects_retained"] > 5
