from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UnitType(StrEnum):
    cav = "cav"
    inf = "inf"
    art = "art"
    other = "other"


class Unit(BaseModel):
    model_config = ConfigDict(frozen=True)

    alliance: int
    army: int
    index: int
    x: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)
    men: int
    initial_men: int | None = None
    bearing: float | None = Field(default=None, allow_inf_nan=False)
    type: UnitType | None = None
    routing: bool | None = None
    shattered: bool | None = None
    ammo: int | None = None


class BattleState(BaseModel):
    model_config = ConfigDict(frozen=True)

    tick: int
    last_seq: str | None = None
    units: list[Unit]
    skipped_lines: int = Field(default=0, ge=0)

    @field_validator("last_seq", mode="before")
    @classmethod
    def _last_seq_is_text(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        raise ValueError("last_seq must be text")
