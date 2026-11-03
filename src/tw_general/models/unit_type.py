from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CapabilityTag = Literal["special_ability", "shot_type", "bayonet_type"]


class UnitCapability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tag: CapabilityTag
    text: str = Field(min_length=1)


class UnitType(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    unit_category: str = Field(min_length=1)
    num_soldiers: int = Field(gt=0)
    width: float = Field(gt=0, allow_inf_nan=False)
    capabilities: list[UnitCapability]
