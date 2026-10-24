"""
Unit & Integration Tests for Procedural Shader Recipes and Material Engine
"""

import pytest
from fastapi.testclient import TestClient

from compiler.shader_recipes import (
    BUILTIN_SHADER_PRESETS,
    ColorRGBA,
    ProceduralNoiseParams,
    ProceduralShaderRecipe,
    ProceduralVoronoiParams,
    ShaderRecipeTypeEnum,
    WeatheringControls,
)
from server.app import app

client = TestClient(app)


def test_shader_recipe_creation():
    recipe = ProceduralShaderRecipe(
        id="Custom_Cyber_Asphalt",
        recipe_type=ShaderRecipeTypeEnum.RAIN_SOAKED_ASPHALT,
        base_color=ColorRGBA(r=0.03, g=0.04, b=0.05, a=1.0),
        metallic=0.1,
        roughness=0.7,
        weathering=WeatheringControls(wetness=0.9, crack_density=0.5),
    )
    data = recipe.model_dump()
    assert data["id"] == "Custom_Cyber_Asphalt"
    assert data["weathering"]["wetness"] == 0.9
    assert data["weathering"]["crack_density"] == 0.5


def test_builtin_presets_catalog():
    assert "RainSoakedCyberHighway" in BUILTIN_SHADER_PRESETS
    assert "ErodedRustedMetal" in BUILTIN_SHADER_PRESETS
    assert "NeonCyberCyan" in BUILTIN_SHADER_PRESETS
    assert "BrutalistConcrete" in BUILTIN_SHADER_PRESETS

    rain = BUILTIN_SHADER_PRESETS["RainSoakedCyberHighway"]
    assert rain.weathering.wetness >= 0.8
    assert rain.recipe_type == ShaderRecipeTypeEnum.RAIN_SOAKED_ASPHALT


def test_api_get_recipes():
    res = client.get("/api/v1/recipes")
    assert res.status_code == 200
    data = res.json()
    assert "RainSoakedCyberHighway" in data
    assert "ErodedRustedMetal" in data
    assert data["NeonCyberCyan"]["emission_strength"] > 0


def test_api_apply_recipe():
    res = client.post(
        "/api/v1/recipes/apply",
        json={
            "scene_name": "sector_01_cerberus_corridor",
            "recipe_id": "RainSoakedCyberHighway",
            "target_slot": "track",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPLIED"
    assert data["compilation"]["status"] == "PASSED"
    assert data["compilation"]["materials_compiled"] >= 4


def test_agent_material_prompt():
    res = client.post(
        "/api/v1/agent/prompt",
        json={
            "prompt": "Add heavy rain puddles and surface cracks to the highway",
            "current_scene_name": "sector_01_cerberus_corridor",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "Rain" in data["action_taken"]
    assert data["compilation"]["status"] == "PASSED"
