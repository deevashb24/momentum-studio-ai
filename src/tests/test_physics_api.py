"""
Integration Tests for FastAPI Godot Jolt 3D Physics Audit Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_physics_audit_api_success():
    res = client.post(
        "/api/v1/physics/audit",
        json={"scene_name": "sector_01_cerberus_corridor", "distance_m": 900.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASSED"
    assert data["distance_driven_m"] >= 900.0
    assert data["collision_meshes"] >= 96
    assert data["max_physics_tick_ms"] < data["physics_budget_ms"]
    assert data["physics_engine"] == "Jolt Physics"
    assert "4.7" in data["godot_version"]


def test_physics_audit_validation_scene_1000m():
    res = client.post(
        "/api/v1/physics/audit",
        json={"scene_name": "physics_1000m_validation", "distance_m": 1000.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASSED"
    assert data["distance_driven_m"] >= 1000.0


def test_physics_audit_short_route_fails():
    # Production scene is ~918m, so asking to drive 1200m fails explicitly as too short
    res = client.post(
        "/api/v1/physics/audit",
        json={"scene_name": "sector_01_cerberus_corridor", "distance_m": 1200.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert "too short" in data["reason"].lower()


def test_agent_physics_prompt_dispatch():
    res = client.post(
        "/api/v1/agent/prompt",
        json={
            "prompt": "Simulate vehicle traversal with Jolt physics",
            "current_scene_name": "sector_01_cerberus_corridor",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "physics_audit" in data
    assert data["physics_audit"]["status"] == "PASSED"
