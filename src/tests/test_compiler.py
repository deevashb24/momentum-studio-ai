"""
Unit & Integration Tests for Spatial AST and KDTree Clearance Auditor
"""

import pytest
from pathlib import Path
import json

from compiler.spatial_ast import (
    WorldChunk,
    SplineTrack,
    SplinePoint,
    ProceduralZone,
    GeneratorTypeEnum,
    LightingBudget,
    PhysicsContract,
)
from validator.kdtree_auditor import audit_corridor_clearance, PurePythonKDTree


def test_spatial_ast_serialization():
    chunk = WorldChunk(
        project_name="Unit_Test_City",
        sector_id="S01",
        splines=[
            SplineTrack(
                id="Track_01",
                points=[
                    SplinePoint(co=[0.0, 0.0, 0.0]),
                    SplinePoint(co=[0.0, 10.0, 150.0]),
                ],
                corridor_clearance_radius_m=32.0,
            )
        ],
        procedural_zones=[
            ProceduralZone(
                id="Zone_01",
                anchor_spline="Track_01",
                generator=GeneratorTypeEnum.PROCEDURAL_MEGATOWERS,
                parameters={"tower_count": 8},
            )
        ],
        lighting_budget=LightingBudget(max_pooled_lights=6),
        physics_contracts=PhysicsContract(),
    )

    data_json = chunk.to_json()
    assert "Unit_Test_City" in data_json
    assert "S01" in data_json

    # Parse back
    loaded = WorldChunk.model_validate_json(data_json)
    assert loaded.project_name == "Unit_Test_City"
    assert loaded.splines[0].corridor_clearance_radius_m == 32.0


def test_spatial_ast_invalid_coordinates():
    with pytest.raises(Exception):
        # 2D coordinates instead of 3D
        SplinePoint(co=[0.0, 0.0])


def test_kdtree_pure_python_search():
    tree = PurePythonKDTree()
    tree.insert((0.0, 0.0, 0.0), 0)
    tree.insert((0.0, 0.0, 100.0), 1)
    tree.balance()

    nearest_co, idx, dist = tree.find_nearest((0.0, 0.0, 10.0))
    assert idx == 0
    assert dist == 10.0

    nearest_co2, idx2, dist2 = tree.find_nearest((0.0, 0.0, 95.0))
    assert idx2 == 1
    assert dist2 == 5.0


def test_corridor_clearance_auditor_clean():
    spline_points = [(0.0, 0.0, 0.0), (0.0, 0.0, 100.0), (0.0, 0.0, 200.0)]
    # All objects placed safely at x=45.0m (outside 32.0m radius)
    objects = [
        {"name": "Tower_L_0", "position": (-45.0, 0.0, 50.0)},
        {"name": "Tower_R_0", "position": (45.0, 0.0, 50.0)},
    ]

    res = audit_corridor_clearance(spline_points, objects, min_clearance_m=32.0)
    assert res["status"] == "PASSED"
    assert res["violations_detected"] == 0
    assert res["corridor_clearance_percent"] == 100.0
    assert res["retained_count"] == 2


def test_corridor_clearance_auditor_auto_prune():
    spline_points = [(0.0, 0.0, 0.0), (0.0, 0.0, 100.0)]
    # Tower placed at x=15.0m (violates 32.0m clearance)
    objects = [
        {"name": "Safe_Tower", "position": (40.0, 0.0, 50.0)},
        {"name": "Obstruction_Tower", "position": (15.0, 0.0, 50.0)},
    ]

    res = audit_corridor_clearance(spline_points, objects, min_clearance_m=32.0, auto_prune=True)
    assert res["status"] == "PASSED"
    assert res["violations_detected"] == 1
    assert res["auto_pruned_count"] == 1
    assert res["retained_count"] == 1
    assert res["violations"][0]["name"] == "Obstruction_Tower"
