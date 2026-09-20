from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_default=True)


class Observation(StrictModel):
    event_id: str = Field(min_length=1, max_length=160)
    point_id: str = Field(min_length=1, max_length=160)
    device_timestamp: datetime
    value: float | None
    unit: str
    quality: Literal["GOOD", "BAD", "UNCERTAIN", "MISSING"] = "GOOD"

    source: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def quality_value(self):
        if (self.value is None) != (self.quality == "MISSING"):
            raise ValueError("MISSING quality requires null; numeric quality requires a value")
        return self

    @field_validator("device_timestamp")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("device_timestamp must include timezone")
        return value.astimezone(timezone.utc)

    @field_validator("value", mode="before")
    @classmethod
    def number(cls, value):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError("value must be a number")
        return value


class Target(StrictModel):
    property_type: str = "office"
    building_ids: list[str] = Field(default_factory=list)
    floor_ids: list[str] = Field(default_factory=list)
    zone_ids: list[str] = Field(default_factory=list)
    room_ids: list[str] = Field(default_factory=list)
    equipment_type: Literal["AHU"] = "AHU"
    space_use: str = "tenant_area"
    exclude_equipment_ids: list[str] = Field(default_factory=list)


class Logic(StrictModel):
    operating_point: str = "Run_Status"
    operating_equals: Literal[0, 1] = 1
    left: str = "Supply_Air_Temperature_Sensor"
    right: str = "Supply_Air_Temperature_Setpoint"
    operator: Literal["ABS_DIFF_GT", "DIFF_GT", "DIFF_LT"] = "ABS_DIFF_GT"
    threshold: float = Field(default=3, gt=0, le=100)
    unit: str = "C"
    duration_minutes: float = Field(default=15, gt=0, le=1440)
    freshness_seconds: int = Field(default=120, ge=15, le=3600)
    severity: Literal["CRITICAL", "WARNING"] = "CRITICAL"
    recovery: Literal["NORMAL_OR_OFF"] = "NORMAL_OR_OFF"


class Override(StrictModel):
    threshold: float | None = Field(default=None, gt=0, le=100)
    duration_minutes: float | None = Field(default=None, gt=0, le=1440)


class RuleConfig(StrictModel):
    name: str = Field(default="Supply air deviation", min_length=1, max_length=160)
    intent: str = "Monitor supply air temperature deviation while running."
    target: Target = Field(default_factory=Target)
    logic: Logic = Field(default_factory=Logic)
    overrides: dict[str, Override] = Field(default_factory=dict)


class Confirmation(StrictModel):
    confirmed: Literal[True]
    preview_digest: str
    reviewer: str = Field(min_length=1, max_length=100)


class AIRequest(StrictModel):
    prompt: str = Field(min_length=10, max_length=6000)
    mode: Literal["model", "demo"] = "model"
