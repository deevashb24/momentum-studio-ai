"""
Integration Tests for MomentumStudio FastAPI Backend Server
"""

import pytest
from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert data["service"] == "MomentumStudio AI Engine"
    assert "blender_version" in data


def test_security_headers():
    res = client.get("/api/v1/health")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" in res.headers


def test_metrics_endpoint():
    res = client.get("/api/v1/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_compiles"] >= 1
    assert "avg_compile_latency_ms" in data


def test_list_scenes():
    res = client.get("/api/v1/scenes")
    assert res.status_code == 200
    scenes = res.json()
    assert isinstance(scenes, list)
    assert any(s["name"] == "sector_01_cerberus_corridor" for s in scenes)


def test_get_scene_details():
    res = client.get("/api/v1/scenes/sector_01_cerberus_corridor")
    assert res.status_code == 200
    data = res.json()
    assert data["project_name"] == "Sector_01_Cerberus_Corridor"
    assert len(data["splines"]) >= 1


def test_compile_endpoint():
    res = client.post(
        "/api/v1/compile",
        json={
            "scene_name": "sector_01_cerberus_corridor",
            "inject_obstruction": False,
            "min_clearance_m": 32.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASSED"
    assert data["objects_retained"] >= 40
    assert data["corridor_clearance_percent"] == 100.0
    assert data["compile_time_ms"] > 0
    assert data["glb_url"].startswith("/api/v1/build/")


def test_agent_prompt_endpoint():
    res = client.post(
        "/api/v1/agent/prompt",
        json={
            "prompt": "Widen corridor radius to 42m",
            "current_scene_name": "sector_01_cerberus_corridor",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "42" in data["action_taken"]
    assert "compilation" in data
    assert data["compilation"]["status"] == "PASSED"


def test_get_build_asset():
    res = client.get("/api/v1/build/sector_01_cerberus_corridor.glb")
    assert res.status_code == 200
    assert res.headers["content-type"] == "model/gltf-binary"
    assert len(res.content) > 1000
