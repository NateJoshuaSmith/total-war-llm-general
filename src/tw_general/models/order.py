from pydantic import BaseModel, ConfigDict, Field


class MoveOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    seq: int = Field(gt=0)
    unit: int = Field(ge=1)
    x: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)
    run: bool
