from typing import Dict
from pydantic import BaseModel, Field


class CoreSizePercent(BaseModel):
    office: float
    residential: float
    mixed_use: float


class EngineeringDefaults(BaseModel):
    structural_grid: str = Field(..., description="Typical structural grid size")
    core_size_percent: CoreSizePercent
    mep_allowance_mm: int = Field(..., description="Ceiling plenum allowance for MEP")
    wall_thickness_mm: int = Field(..., description="Typical wall thickness")
    circulation_percent: float = Field(
        ..., description="Percentage of GFA for circulation"
    )
    fire_stair_width_mm: int = Field(..., description="Minimum fire stair width")


class EngineeringDefaultsResponse(BaseModel):
    defaults: Dict[str, EngineeringDefaults]
