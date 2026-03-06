from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SpawnPoint(BaseModel):
    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class WeatherConfig(BaseModel):
    preset: str = "ClearNoon"


class SyncConfig(BaseModel):
    enabled: bool = True
    fixed_delta_seconds: float = 0.05

    @field_validator("fixed_delta_seconds")
    @classmethod
    def validate_fixed_delta_seconds(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("fixed_delta_seconds must be > 0")
        if value > 0.2:
            raise ValueError("fixed_delta_seconds should be <= 0.2 for stable control")
        return value


class EgoVehicleConfig(BaseModel):
    blueprint: str = "vehicle.tesla.model3"
    spawn_point: SpawnPoint


class TrafficConfig(BaseModel):
    enabled: bool = False
    num_vehicles: int = 0
    num_walkers: int = 0

    @field_validator("num_vehicles", "num_walkers")
    @classmethod
    def validate_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("traffic counts must be non-negative")
        return value


class SensorsConfig(BaseModel):
    enabled: bool = False


class TerminationConfig(BaseModel):
    timeout_seconds: int = 30
    success_condition: str = "timeout"

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be > 0")
        return value


class RecorderConfig(BaseModel):
    enabled: bool = False


class DebugConfig(BaseModel):
    viewer_friendly: bool = False


class MetadataConfig(BaseModel):
    author: str = "unknown"
    tags: list[str] = Field(default_factory=list)
    description: str = ""


class ScenarioDescriptor(BaseModel):
    version: int = 1
    scenario_name: str
    map_name: str
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)
    ego_vehicle: EgoVehicleConfig
    traffic: TrafficConfig = Field(default_factory=TrafficConfig)
    sensors: SensorsConfig = Field(default_factory=SensorsConfig)
    termination: TerminationConfig = Field(default_factory=TerminationConfig)
    recorder: RecorderConfig = Field(default_factory=RecorderConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)

    @field_validator("scenario_name", "map_name")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be empty")
        return value

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
