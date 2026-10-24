"""
MomentumStudio AI — Declarative Spatial AST (Abstract Syntax Tree)
Defines the Pydantic v2 declarative schema (.world.json) for agent-generated 3D game worlds.
Includes procedural shader recipe definitions for infinite PBR material synthesis.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
try:
    from compiler.shader_recipes import ProceduralShaderRecipe, BUILTIN_SHADER_PRESETS
except ImportError:
    from shader_recipes import ProceduralShaderRecipe, BUILTIN_SHADER_PRESETS


class SplineTypeEnum(str, Enum):
    BEZIER = "BEZIER"
    NURBS = "NURBS"
    POLY = "POLY"


class GeneratorTypeEnum(str, Enum):
    PROCEDURAL_MEGATOWERS = "PROCEDURAL_MEGATOWERS"
    TRANSIT_TUBES = "TRANSIT_TUBES"
    NEON_BILLBOARDS = "NEON_BILLBOARDS"
    SKYBRIDGES = "SKYBRIDGES"
    SOLAR_SAILS = "SOLAR_SAILS"


class PhysicsEngineEnum(str, Enum):
    JOLT_3D = "JOLT_3D"
    BULLET = "BULLET"
    GODOT_PHYSICS = "GODOT_PHYSICS"


class Vector3D(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float
    z: float

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @classmethod
    def from_list(cls, coords: List[float]) -> Vector3D:
        if len(coords) != 3:
            raise ValueError("Coordinates list must contain exactly 3 numbers [x, y, z]")
        return cls(x=coords[0], y=coords[1], z=coords[2])


class SplinePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    co: List[float] = Field(..., min_length=3, max_length=3, description="[x, y, z] anchor coordinates")
    handle_left: Optional[List[float]] = Field(default=None, min_length=3, max_length=3)
    handle_right: Optional[List[float]] = Field(default=None, min_length=3, max_length=3)


class SplineTrack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=3, max_length=80)
    type: SplineTypeEnum = SplineTypeEnum.BEZIER
    closed: bool = False
    points: List[SplinePoint] = Field(..., min_length=2)
    corridor_clearance_radius_m: float = Field(default=32.0, ge=4.0, le=200.0)
    enforce_kdtree_audit: bool = True
    material_recipe_id: Optional[str] = Field(default="RainSoakedCyberHighway")


class ProceduralZone(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=3, max_length=80)
    anchor_spline: str = Field(..., min_length=3, max_length=80)
    generator: GeneratorTypeEnum = GeneratorTypeEnum.PROCEDURAL_MEGATOWERS
    parameters: Dict[str, Any] = Field(default_factory=dict)
    material_recipe_id: Optional[str] = Field(default="BrutalistConcrete")


class LightingBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_pooled_lights: int = Field(default=6, ge=1, le=32)
    volumetric_fog_density: float = Field(default=0.0145, ge=0.0, le=0.5)
    skybox_energy: float = Field(default=0.65, ge=0.0, le=5.0)
    rain_particle_budget: int = Field(default=14000, ge=0, le=100000)
    enable_interior_culling_volumes: bool = True


class PhysicsContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    engine: PhysicsEngineEnum = PhysicsEngineEnum.JOLT_3D
    collision_layers: List[str] = Field(
        default_factory=lambda: ["WORLD_STATIC", "PLAYER_TRACK", "HAZARDS"]
    )
    max_physics_tick_ms: float = Field(default=4.0, ge=0.1, le=16.67)


class WorldChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(default="1.0.0", alias="$schema_version")
    project_name: str = Field(..., min_length=3, max_length=120)
    sector_id: str = Field(default="S00", min_length=2, max_length=32)
    units: str = Field(default="meters")
    splines: List[SplineTrack] = Field(..., min_length=1)
    procedural_zones: List[ProceduralZone] = Field(default_factory=list)
    materials: List[ProceduralShaderRecipe] = Field(
        default_factory=lambda: list(BUILTIN_SHADER_PRESETS.values())
    )
    lighting_budget: LightingBudget = Field(default_factory=LightingBudget)
    physics_contracts: PhysicsContract = Field(default_factory=PhysicsContract)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(by_alias=True, indent=indent)

    def save(self, filepath: Union[str, Path]) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> WorldChunk:
        p = Path(filepath)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.model_validate(data)
