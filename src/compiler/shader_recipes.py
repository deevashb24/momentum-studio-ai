"""
MomentumStudio AI — Declarative Procedural Shader Recipes
Defines Pydantic v2 schemas and standard algorithmic presets for infinite PBR surface synthesis.
These recipes compile headlessly into Blender shader node graphs (Noise, Voronoi, Musgrave, ColorRamp).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class ShaderRecipeTypeEnum(str, Enum):
    RAIN_SOAKED_ASPHALT = "RAIN_SOAKED_ASPHALT"
    ERODED_RUSTED_METAL = "ERODED_RUSTED_METAL"
    NEON_CYBER_EMISSIVE = "NEON_CYBER_EMISSIVE"
    WEATHERED_CONCRETE = "WEATHERED_CONCRETE"
    HOLOGRAPHIC_GRID = "HOLOGRAPHIC_GRID"
    CARBON_FIBER_WEAVE = "CARBON_FIBER_WEAVE"


class ColorRGBA(BaseModel):
    model_config = ConfigDict(extra="forbid")
    r: float = Field(default=0.8, ge=0.0, le=1.0)
    g: float = Field(default=0.8, ge=0.0, le=1.0)
    b: float = Field(default=0.8, ge=0.0, le=1.0)
    a: float = Field(default=1.0, ge=0.0, le=1.0)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)


class ProceduralNoiseParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scale: float = Field(default=5.0, ge=0.1, le=200.0)
    detail: float = Field(default=4.0, ge=0.0, le=15.0)
    roughness: float = Field(default=0.5, ge=0.0, le=1.0)
    distortion: float = Field(default=0.0, ge=0.0, le=10.0)


class ProceduralVoronoiParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scale: float = Field(default=16.0, ge=0.5, le=300.0)
    randomness: float = Field(default=1.0, ge=0.0, le=1.0)


class WeatheringControls(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wetness: float = Field(default=0.0, ge=0.0, le=1.0, description="0.0 = bone dry, 1.0 = submerged puddles")
    puddle_coverage: float = Field(default=0.35, ge=0.0, le=1.0)
    rust_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Surface oxidization ratio")
    grime_factor: float = Field(default=0.15, ge=0.0, le=1.0, description="Edge and crevice ambient grime")
    crack_density: float = Field(default=0.0, ge=0.0, le=1.0, description="Voronoi fracture intensity")


class ProceduralShaderRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=3, max_length=64)
    recipe_type: ShaderRecipeTypeEnum = ShaderRecipeTypeEnum.RAIN_SOAKED_ASPHALT
    description: str = Field(default="", max_length=240)
    
    # Base PBR Channels
    base_color: ColorRGBA = Field(default_factory=lambda: ColorRGBA(r=0.08, g=0.09, b=0.12, a=1.0))
    metallic: float = Field(default=0.1, ge=0.0, le=1.0)
    roughness: float = Field(default=0.6, ge=0.0, le=1.0)
    emission_color: ColorRGBA = Field(default_factory=lambda: ColorRGBA(r=0.0, g=0.0, b=0.0, a=1.0))
    emission_strength: float = Field(default=0.0, ge=0.0, le=50.0)
    
    # Procedural Generators
    noise: ProceduralNoiseParams = Field(default_factory=ProceduralNoiseParams)
    voronoi: ProceduralVoronoiParams = Field(default_factory=ProceduralVoronoiParams)
    weathering: WeatheringControls = Field(default_factory=WeatheringControls)
    use_triplanar_mapping: bool = True


# Standard Master Preset Catalog
BUILTIN_SHADER_PRESETS: Dict[str, ProceduralShaderRecipe] = {
    "RainSoakedCyberHighway": ProceduralShaderRecipe(
        id="RainSoakedCyberHighway",
        recipe_type=ShaderRecipeTypeEnum.RAIN_SOAKED_ASPHALT,
        description="Dark asphalt road surface with dynamic Voronoi cracks and high-contrast reflective water puddles.",
        base_color=ColorRGBA(r=0.05, g=0.06, b=0.08, a=1.0),
        metallic=0.15,
        roughness=0.65,
        noise=ProceduralNoiseParams(scale=4.5, detail=6.0, roughness=0.6),
        voronoi=ProceduralVoronoiParams(scale=22.0, randomness=0.9),
        weathering=WeatheringControls(wetness=0.85, puddle_coverage=0.45, crack_density=0.3),
        use_triplanar_mapping=True,
    ),
    "ErodedRustedMetal": ProceduralShaderRecipe(
        id="ErodedRustedMetal",
        recipe_type=ShaderRecipeTypeEnum.ERODED_RUSTED_METAL,
        description="Industrial structural alloy with oxidized reddish-brown rust peeling at edges and seams.",
        base_color=ColorRGBA(r=0.45, g=0.48, b=0.52, a=1.0),
        metallic=0.92,
        roughness=0.35,
        noise=ProceduralNoiseParams(scale=8.0, detail=8.0, roughness=0.75),
        weathering=WeatheringControls(rust_intensity=0.65, grime_factor=0.4),
        use_triplanar_mapping=True,
    ),
    "NeonCyberCyan": ProceduralShaderRecipe(
        id="NeonCyberCyan",
        recipe_type=ShaderRecipeTypeEnum.NEON_CYBER_EMISSIVE,
        description="High-intensity kinetic electric cyan neon strip for speed rails and architectural beacons.",
        base_color=ColorRGBA(r=0.02, g=0.85, b=1.0, a=1.0),
        metallic=0.0,
        roughness=0.05,
        emission_color=ColorRGBA(r=0.02, g=0.95, b=1.0, a=1.0),
        emission_strength=5.5,
    ),
    "NeonCyberOrange": ProceduralShaderRecipe(
        id="NeonCyberOrange",
        recipe_type=ShaderRecipeTypeEnum.NEON_CYBER_EMISSIVE,
        description="Hazard amber-orange emission for corridor boundary markers and caution zones.",
        base_color=ColorRGBA(r=1.0, g=0.45, b=0.05, a=1.0),
        metallic=0.0,
        roughness=0.08,
        emission_color=ColorRGBA(r=1.0, g=0.5, b=0.08, a=1.0),
        emission_strength=4.8,
    ),
    "BrutalistConcrete": ProceduralShaderRecipe(
        id="BrutalistConcrete",
        recipe_type=ShaderRecipeTypeEnum.WEATHERED_CONCRETE,
        description="Matte high-density skyscraper concrete with multi-octave noise grime and vertical rain streaks.",
        base_color=ColorRGBA(r=0.22, g=0.24, b=0.28, a=1.0),
        metallic=0.05,
        roughness=0.88,
        noise=ProceduralNoiseParams(scale=12.0, detail=5.0, roughness=0.8),
        weathering=WeatheringControls(grime_factor=0.35),
        use_triplanar_mapping=True,
    ),
}
