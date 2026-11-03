from pydantic import BaseModel, ConfigDict, Field, model_validator


class General(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    experience: int = Field(ge=0)
    portrait: str = Field(min_length=1)
    category: str | None = Field(default=None, min_length=1)


class BattleUnit(BaseModel):
    """One unit on the field. `x` and `z` are game metres; XML writes them as x/y."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str = Field(min_length=1)
    x: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)
    experience: int = Field(ge=0)
    width: float | None = Field(
        default=None,
        gt=0,
        allow_inf_nan=False,
        description="Formation width in metres. Omit to use the catalogue width.",
    )
    general: General | None = None


class DeploymentZone(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)
    width: float = Field(gt=0, allow_inf_nan=False)
    height: float = Field(gt=0, allow_inf_nan=False)


class BattleSide(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    faction: str = Field(min_length=1)
    zone: DeploymentZone
    facing: float = Field(allow_inf_nan=False)
    units: list[BattleUnit]

    @model_validator(mode="after")
    def _at_least_one_unit(self) -> "BattleSide":
        if len(self.units) < 1:
            raise ValueError("each side needs at least one unit")
        return self


class Battle(BaseModel):
    """Side 1 is the player (alliance 0). Side 2 is the army we command (alliance 1)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    map: str = Field(min_length=1)
    climate: str = Field(min_length=1)
    sides: list[BattleSide]

    @model_validator(mode="after")
    def _exactly_two_sides(self) -> "Battle":
        if len(self.sides) != 2:
            raise ValueError("a battle needs exactly two sides")
        return self
